import vgamepad as vg
from oscpy.server import OSCThreadServer
from time import sleep
from enum import Enum
import socket


gamepad = vg.VX360Gamepad()





def dump(address, *values):
    print(u'{}: {}'.format(
        address.decode('utf8'),
        ', '.join(
            '{}'.format(
                v.decode(options.encoding or 'utf8')
                if isinstance(v, bytes)
                else v
            )
            for v in values if values
        )
    ))



def callback_x(*values):
    global current_accel

    data = b''

    if values[0]:
        gamepad.left_joystick_float(x_value_float=0.0, y_value_float=values[0]) 
        gamepad.update()




def callback_y(*values):
    global current_steering

    data = b''

    if values[0]:
        gamepad.left_joystick_float(x_value_float=values[0], y_value_float=0.0) 
        gamepad.update()





address = ('localhost', 6006)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

osc = OSCThreadServer(default_handler=dump)  # See sources for all the arguments

# You can also use an \*nix socket path here
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

osc.bind(b'/multisense/pad/x', callback_x)
osc.bind(b'/multisense/pad/y', callback_y)


sleep(1000)
osc.stop()  # Stop the default socket




gamepad.left_joystick_float(x_value_float=steer, y_value_float=0.0) 
gamepad.update()