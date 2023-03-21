import PySimpleGUI as sg
import subprocess
from time import sleep
import socket

subprocess.Popen(["python", "transcribe.py", "--non_english"], shell=False)

layout = [[sg.Text("Hello from PysimpleGUI")], [sg.Button("OK")]]
window = sg.Window("Demo", layout)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 6969))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message: %s" % data)
