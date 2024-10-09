from oscpy.server import OSCThreadServer
import time
from time import sleep
from threading import Timer
import socket
import sys
import select

address = ('localhost', 6006)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

""" Touchpad controls 
def clbk_pad(*vals):
    key, val = vals
    if key == b"/multisense/pad/x":
        if val > 0:
            sock.sendto(b"P_ACCELERATE", address)
            sock.sendto(b"R_BRAKE", address)
        else:
            sock.sendto(b"R_ACCELERATE", address)
            sock.sendto(b"P_BRAKE", address)
    elif key == b"/multisense/pad/y":
        if val > 0:
            sock.sendto(b"P_RIGHT", address)
            sock.sendto(b"R_LEFT", address)
        else:
            sock.sendto(b"R_RIGHT", address)
            sock.sendto(b"P_LEFT", address)
"""


last_tap = time.time()

def clbk(*vals):
    key, val = vals
    if key == b"/multisense/orientation/yaw":
        if val < -15:
            sock.sendto(b"P_RIGHT", address)
            sock.sendto(b"R_LEFT", address)
        elif val > 15:
            sock.sendto(b"R_RIGHT", address)
            sock.sendto(b"P_LEFT", address)
        else:
            sock.sendto(b"R_RIGHT", address)
            sock.sendto(b"R_LEFT", address)
    
    elif key == b"/multisense/orientation/pitch":
        if val > -25:
            sock.sendto(b"P_ACCELERATE", address)
        else:
            sock.sendto(b"R_ACCELERATE", address)

    elif key == b"/multisense/pad/touchUP" and val == True:
        global last_tap
        now = time.time()
        if now - last_tap < 0.2:
            sock.sendto(b"P_FIRE", address)
            def rel():
                sock.sendto(b"R_FIRE", address)
            Timer(0.1, rel).start()
            print("double")
        else:
            print("single")
        last_tap = now
    

osc = OSCThreadServer(default_handler=clbk)  # See sources for all the arguments

# You can also use an \*nix socket path here
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

# osc.bind(b'/multisense/pad/x', callback)

sleep(1000)
osc.stop()  # Stop the default socket