from oscpy.server import OSCThreadServer
from time import sleep
import numpy as np
import pynput
from pynput.keyboard import Key
import vgamepad
import time

"""
Controls the car using the gyroscope of the phone
We used the GyrOSC app on an Iphone
And we used pynput.keyboard.Controller to simulate the key presses
The steering is controlled by the roll of the phone and the acceleration by the pitch
THe steering is continuous by emulating a joystick
GyroOSC app doesn't have tactile support so we decided have the following interactions :
Shake the phone to the side to throw an object
Shake the phone up and down to be rescued
"""

keyboard_controller = pynput.keyboard.Controller()
joystick_controller = vgamepad.VX360Gamepad()

def play_accel_discrete(accel):
    #No acceleration
    if accel == 0:
        keyboard_controller.release(Key.up)
        keyboard_controller.release(Key.down)
    
    #Forward acceleration
    elif accel == 1:
        keyboard_controller.press(Key.up)
        keyboard_controller.release(Key.down)
    
    #Backward acceleration
    elif accel == -1:
        keyboard_controller.press(Key.down)
        keyboard_controller.release(Key.up) 
        

def play_turn_discrete(steer):
    #go straght
    if steer == 0:
        keyboard_controller.release(Key.left)
        keyboard_controller.release(Key.right)
    
    #turn right
    elif steer == 1:
        keyboard_controller.press(Key.right)
        keyboard_controller.release(Key.left)
    
    #turn left
    elif steer == -1:
        keyboard_controller.press(Key.left)
        keyboard_controller.release(Key.right)
        

def play_turn_continuous(steer):
    #steer is a float from -1 to 1, from left to right
    joystick_controller.left_joystick_float(x_value_float=steer, y_value_float=0.0) 
    joystick_controller.update()
        
        
def clip_and_apply_deadzone(val):
    #a way to add a deadzone to the steering so you can go perfectly straight
    deadzone = 0.1
    if abs(val) < deadzone:
        val = 0
    else:
        val = (val - 0.2*np.sign(val))*1.25
        
    val = np.clip(val, -1, 1)
    return val
        
def continuous_to_discrete(val, threshold):
    #we take a continuous value and determine the discrete value associcated
    if -threshold < val < threshold:
        ret = 0
    elif val < -threshold:
        ret = -1
    else:
        ret = 1
        
    return ret

def new_gyro_state(*gyro_state):
    pitch, roll, yaw = gyro_state
    pitch_thresh = 0.2
    
    accel_cmd = -1 * continuous_to_discrete(pitch, pitch_thresh)
    turn_cmd = clip_and_apply_deadzone(roll*2)
    
    play_accel_discrete(accel_cmd)
    play_turn_continuous(turn_cmd)

def new_accel_state(*accel_state):
    accel_state = np.array(accel_state)
    side_accel = accel_state[0]
    up_accel = accel_state[2]
    
    #shake the phone to the side and an object is thrown
    if abs(side_accel) > 1:
        keyboard_controller.press(Key.space)
        time.sleep(0.03)
        keyboard_controller.release(Key.space)
    
    #shake the phone up and down the side and you are rescued
    if abs(up_accel) > 1:
        keyboard_controller.press(Key.backspace)
        time.sleep(0.03)
        keyboard_controller.release(Key.backspace)
    
def new_buttons_state(*buttons_state):
    #not used here
    button_id, button_state = buttons_state

osc = OSCThreadServer()

# You can also use an \*nix socket path here
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

osc.bind(b'/gyrosc/gyro', new_gyro_state)
osc.bind(b'/gyrosc/accel', new_accel_state)
osc.bind(b'/gyrosc/button', new_buttons_state)

sleep(1000)
osc.stop()  # Stop the default socket

