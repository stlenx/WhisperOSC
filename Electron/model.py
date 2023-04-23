import argparse
import io
import os
import speech_recognition as sr
from faster_whisper import WhisperModel
import torch
import gc
import numpy as np
import msvcrt

import threading
from threading import Event
from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform
import sys

from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer


def stdListener(stop, mute):
    isMuted = False
    while not stop.is_set():
        for line in sys.stdin:
            if line.strip() == 'stop':
                stop.set()
                break
            elif line.strip() == 'mute':
                sys.stdout.flush()
                if isMuted:
                    #unmute
                    mute.clear()
                else:
                    #mute
                    mute.set()
                isMuted = not isMuted


def main(model, noEnglish, deviceToUse, stop, mute):
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
    # Initialize the device

    if torch.cuda.is_available() and deviceToUse == "GPU":
        #Theoretically int8_float16 is faster, but perhaps the loss on precision is too much. Need further testing
        device = "cuda"
        compute_type = "float16"

        print("Using GPU, Loading model...")
    else:
        device = "cpu"
        compute_type = "int8"

        if deviceTouse == "GPU":
            print("GPU not available, using CPU, Loading model...")
        else:
            print("Using CPU, Loading model...")

    
    if model != "large" and not noEnglish:
        model = model + ".en"

    # Normal whisper
    # audio_model = whisper.load_model(model, device=device)
    try:
        audio_model = WhisperModel(model, device=device, compute_type=compute_type) #cpu_threads=16  <-- useful
    except Exception as e:
        pass

    record_timeout = 5
    phrase_timeout = 3

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

    current_text = ""
    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)

    # Cue the user that we're ready to go.
    print("Model loaded")
    sys.stdout.flush()

    while not stop.is_set():
        try:
            now = datetime.utcnow()

            if mute.is_set():
                data_queue = Queue()

            
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

                #print("I'm gonna try!")
                # convert the audio data to a NumPy ndarray
                #audio_array = np.frombuffer(audio_data.frame_data, dtype=np.int16)
                

                # Write wav data to the temporary file as bytes.
                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                # Read the transcription.
                result, info = audio_model.transcribe(temp_file, no_speech_threshold=0.3, log_prob_threshold=0.2)

                transcription = "".join(segment.text for segment in result).strip()
                print(transcription)
                sys.stdout.flush()
                client.send_message("/chatbox/input", [transcription, True])

                # Infinite loops are bad for processors, must sleep.
                sleep(0.1)
        except KeyboardInterrupt:
            break

    #Empty the vram use and clean everything up
    #del audio_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    gc.collect()
    print("Model closed")


inputModel = sys.argv[1]
inputNonEnglish = sys.argv[2]
inputDevice = sys.argv[3]

if inputNonEnglish == "false":
    inputNonEnglish = False
else:
    inputNonEnglish = True

stop = Event()
mute = Event()

listener = threading.Thread(target=stdListener, args=(stop, mute))
listener.start()


main(inputModel, inputNonEnglish, inputDevice, stop, mute)


listener.join()