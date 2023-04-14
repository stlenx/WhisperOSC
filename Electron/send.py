import sys

from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

text = sys.argv[1]

client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
client.send_message("/chatbox/input", [text, True])