import speech_recognition as sr
import numpy as np
from faster_whisper import WhisperModel
import whisper

# set up the speech recognition object
r = sr.Recognizer()

# record audio from the microphone
with sr.Microphone() as source:
    print("Say something!")
    audio_data = r.record(source, duration=5)

# convert the audio data to a NumPy ndarray
sample_rate = audio_data.sample_rate
audio = np.frombuffer(audio_data.frame_data, dtype=np.int16).astype(np.float32) / 32768.0 

print(audio)

audio_model = WhisperModel("tiny", device="cpu")

segments, info = audio_model.transcribe(audio)

transcription = "".join(segment.text for segment in segments).strip()