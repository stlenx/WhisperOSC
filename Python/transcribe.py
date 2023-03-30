#! python3.7

import argparse
import io
import os
import speech_recognition as sr
import whisper
import torch
import gc

import threading
from threading import Event
from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform

import PySimpleGUI as sg
import socket
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

def main(model, noEnglish, communicator, stop_event):
    # The last time a recording was retreived from the queue.
    phrase_time = None
    # Current raw audio bytes.
    last_sample = bytes()
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feauture where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = 1000
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramtically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

    if torch.cuda.is_available():
        print("Using GPU, Loading model...")
        communicator.put("Using GPU, Loading model...")
    else:
        print("GPU not available, using CPU, Loading model...")
        communicator.put("GPU not available, using CPU, Loading model...")
    
    # Important for linux users. 
    # Prevents permanent application hang and crash by using the wrong Microphone
    if 'linux' in platform:
        mic_name = 'pulse'
        if not mic_name or mic_name == 'list':
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")   
            return
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        source = sr.Microphone(sample_rate=16000)
        
    # Load / Download model
    if model != "large" and not noEnglish:
        model = model + ".en"
    audio_model = whisper.load_model(model)

    record_timeout = 2 #Default
    phrase_timeout = 3 #Default

    temp_file = NamedTemporaryFile().name

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio:sr.AudioData) -> None:
        """
        Threaded callback function to recieve audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)
    
    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
    current_text = ""

    # Cue the user that we're ready to go.
    print("Model loaded.\n")
    communicator.put("Model loaded")

    #If the stop event gets called, we stoppin
    while not stop_event.is_set():
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now

                # Concatenate our current audio data with the latest audio data.
                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                # Use AudioData to convert the raw data to wav data.
                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # Write wav data to the temporary file as bytes.
                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                # Read the transcription.
                result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                #print(result['segments'][0]['no_speech_prob'])

                #Only prints out if the ai is certain that it's speech. Prevents hallucinations.

                if len(result['segments']) > 0:
                    if result['segments'][0]['no_speech_prob'] < 0.2:
                        text = result['text'].strip()

                        #Logging stuff is fun
                        print(text)
                    
                        #Send the text to vrchat and the GUI, while limiting it to 144 characters
                        client.send_message("/chatbox/input", [text[len(text)-144:len(text)], True])
                        communicator.put(text[len(text)-144:len(text)])
                
                
                

                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    #Empty the vram use and clean everything up
    del audio_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    gc.collect()
    print("\nClosing script")



def GUI(communicator):
    model = 'tiny'
    noEnglish = False
    
    stop_event = Event()
    OSCListener = threading.Thread(target=main, args=(model, noEnglish, communicator, stop_event))
    OSCListener.start()

    sg.theme('DarkGrey6')
    selected_color = '#949494'
    unselected_color = '#4f4f4f'

    def set_buttons():
        window['tiny'].Update(button_color = unselected_color)
        window['base'].Update(button_color = unselected_color)
        window['small'].Update(button_color = unselected_color)
        window['medium'].Update(button_color = unselected_color)
        window['large'].Update(button_color = unselected_color)

        window[model].Update(button_color = selected_color)

    def run_model(OSCListener):
        #Set the button colours
        set_buttons()
        
        #Cue to the user he's done something
        communicator.put('Restarting model...')
        
        #Stop the listner
        stop_event.set()
        OSCListener.join()

        #Reset the stop event so the next listener doesn't immediatedly stop
        stop_event.clear()
        OSCListener = threading.Thread(target=main, args=(model, noEnglish, communicator, stop_event))
        OSCListener.start()

        return OSCListener
    
    
    #This function runs in a separate thread and updates the GUI text
    def update_text(text_element, communicator, stop_event):
        while not stop_event.is_set():
            try:
                text_element.update(communicator.get(timeout=0.1))
            except Exception as e:
                if not communicator.empty():
                    print(f"Caught exception in update_text: {e}")
                
            sleep(0.1)
        print("Stopping the text update.")


    button_style = {'font': ('Sans-Serif', 18),
                'border_width': 0,
                'pad': (8, 8),
                'button_color': unselected_color}
    
    layout = [[sg.Push(), sg.Button('tiny', key='tiny', **button_style), sg.Button('base', key='base', **button_style), sg.Button('small', key='small', **button_style), sg.Button('medium', key='medium', **button_style), sg.Button('large', key='large', **button_style), sg.Push()],
              [sg.VPush()],
              [sg.Text("", key="-TEXT-", size=(33, 4), font=('Sans-Serif', 26), justification='c')],
              [sg.VPush()],
              [sg.Push(), sg.Button('Non english', key='noEnglish', **button_style), sg.Push()]]

    window = sg.Window("WhisperOSC", layout, finalize=True, resizable=True, size=(669, 320), icon='Images/OpenAI.ico')

    window['-TEXT-'].expand(True, True)
    text_element = window['-TEXT-']  # get the Text element by its key

    set_buttons()

    # start a separate thread to update the GUI
    updateText_close = Event()
    textUpdater = threading.Thread(target=update_text, args=(text_element, communicator, updateText_close))
    textUpdater.start()


    # read events from the GUI in the main thread
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        if event == 'noEnglish':
            if noEnglish:
                window['noEnglish'].Update(button_color = unselected_color)
                noEnglish = False
            else:
                window['noEnglish'].Update(button_color = selected_color)
                noEnglish = True

            OSCListener = run_model(OSCListener)
        
        if event == 'tiny':
            model = 'tiny'
            OSCListener = run_model(OSCListener)
            
        if event == 'base':
            model = 'base'
            OSCListener = run_model(OSCListener)
            
        if event == 'small':
            model = 'small'
            OSCListener = run_model(OSCListener)

        if event == 'medium':
            model = 'medium'
            OSCListener = run_model(OSCListener)

        if event == 'large':
            model = 'large'
            OSCListener = run_model(OSCListener)
            
    print("Closing app")
    stop_event.set()
    OSCListener.join()
    
    updateText_close.set()
    textUpdater.join()
    print("Updater closed")

    window.close()


if __name__ == "__main__":
    communicator = Queue()
    communicator.put("")

    GUI(communicator)


