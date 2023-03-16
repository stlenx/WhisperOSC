import numpy as np
import pyaudio
import matplotlib.pyplot as plt
from scipy import signal

# Define constants
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
CHUNK = 1024
N_MELS = 128
WINDOW = signal.windows.hann(CHUNK)

# Initialize PyAudio
pa = pyaudio.PyAudio()

# Open microphone stream
stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                 frames_per_buffer=CHUNK)

# Initialize Mel filterbank
mel_filterbank = signal.filters.mel(RATE, CHUNK, n_mels=N_MELS)

# Create figure and axes for the plot
fig, ax = plt.subplots()

# Loop for streaming and plotting
while True:
    # Read audio data from microphone stream
    data = stream.read(CHUNK)
    # Convert data to numpy array
    data_np = np.frombuffer(data, dtype=np.float32)
    # Apply Hann window
    data_win = data_np * WINDOW
    # Compute power spectrum
    spectrum = np.abs(np.fft.fft(data_win))**2
    # Apply Mel filterbank
    spectrum_mel = mel_filterbank.dot(spectrum)
    # Convert to decibels
    spectrum_db = 10 * np.log10(spectrum_mel)
    # Plot Mel spectrogram
    ax.clear()
    ax.imshow(spectrum_db.T, origin='lower', aspect='auto')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Mel frequency')
    plt.pause(0.01)
