import vgamepad as vg
from oscpy.server import OSCThreadServer
from time import sleep
import socket

'''
This script allows users to control the kart by dragging on the screen, simulating joystick-like movements. The kart responds to swipes both horizontally (left to right) and vertically (up to down), with the initial touch point dynamically setting the joystick's center.
'''

# Create the virtual Xbox 360 gamepad
gamepad = vg.VX360Gamepad()

# Function to print incoming OSC messages for debugging
def dump(address, *values):
    print(u'{}: {}'.format(
        address.decode('utf8'),
        ', '.join(
            '{}'.format(
                v.decode('utf8') if isinstance(v, bytes) else v
            )
            for v in values if values
        )
    ))

# Callback function for vertical movement (Y-axis)
def callback_x(*values):
    if values and values[0] != 0:
        if values[0] > 0.2:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        
        if values[0] < -0.2:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X) 

    gamepad.update()

# Callback function for horizontal movement (X-axis)
def callback_y(*values):
    if values and values[0] != 0:
        
        # Move joystick horizontally based on received value (left/right)
        gamepad.left_joystick_float(x_value_float=values[0], y_value_float=0.0)
    else:
        # Reset joystick to center when no value or release occurs
        gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
    
    # Update gamepad state
    gamepad.update()

# Handle 'touchUP' event to reset joystick to center
def callback_touch_up(*values):
    # Reset joystick to the center position on touch release

    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X) 
    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y) 

    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
    gamepad.update()

# OSC server setup
address = ('localhost', 6006)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

osc = OSCThreadServer(default_handler=dump)

# Listening on all interfaces, port 8000
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

# Bind OSC addresses for handling X and Y joystick control
osc.bind(b'/multisense/pad/x', callback_x)
osc.bind(b'/multisense/pad/y', callback_y)

# Bind the touchUP event to reset the joystick
osc.bind(b'/multisense/pad/touchUP', callback_touch_up)

# Keep the script running (simulate 1000 seconds of listening)
sleep(1000)

# Stop the OSC server after the sleep period
osc.stop()  # Stop the default socket
