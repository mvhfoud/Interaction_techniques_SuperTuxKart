from oscpy.server import OSCThreadServer
from time import sleep
import numpy as np
from pynput.keyboard import Key, Controller
import time


"""
Controls the car using the gyroscope of the phone
We used the GyrOSC app on an Iphone
And we used pynput.keyboard.Controller to simulate the key presses
The steering is controlled by the roll of the phone and the acceleration by the pitch
THe steering is discrete and is done by simulating keyboard keys
GyroOSC app doesn't have tactile support so we decided have the following interactions :
Shake the phone to the side to throw an object
Shake the phone up and down to be rescued
"""

keyboard = Controller()

def play_accel(accel):
    #No acceleration
    if accel == 0:
        keyboard.release(Key.up)
        keyboard.release(Key.down)
    
    #Forward acceleration
    elif accel == 1:
        keyboard.press(Key.up)
        keyboard.release(Key.down)
    
    #Backward acceleration
    elif accel == -1:
        keyboard.press(Key.down)
        keyboard.release(Key.up) 
        

def play_turn_discrete(turn):
    #Go straight
    if turn == 0:
        keyboard.release(Key.left)
        keyboard.release(Key.right)
    
    #Turn right
    elif turn == 1:
        keyboard.press(Key.right)
        keyboard.release(Key.left)
    
    #Turn left
    elif turn == -1:
        keyboard.press(Key.left)
        keyboard.release(Key.right)
        
        
def continuous_to_discrete(val, threshold):
    #we take a continuous value and determine the discrete value associcated using a threshold
    if -threshold < val < threshold:
        ret = 0
    elif val < -threshold:
        ret = -1
    else:
        ret = 1
        
    return ret

def new_gyro_state(*gyro_state):
    pitch, roll, yaw = gyro_state
    pitch_thresh = 0.3
    roll_thresh = 0.3
    
    accel_cmd = -1 * continuous_to_discrete(pitch, pitch_thresh)
    turn_cmd = continuous_to_discrete(roll, roll_thresh)

    play_accel(accel_cmd)
    play_turn_discrete(turn_cmd)

def new_accel_state(*accel_state):
    accel_state = np.array(accel_state)
    side_accel = accel_state[0]
    up_accel = accel_state[2]
    
    #shake the phone to the side and an object is thrown
    if abs(side_accel) > 1:
        keyboard.press(Key.space)
        time.sleep(0.03)
        keyboard.release(Key.space)
    
    #shake the phone up and down the side and you are rescued
    if abs(up_accel) > 1:
        keyboard.press(Key.backspace)
        time.sleep(0.03)
        keyboard.release(Key.backspace)
    
def new_buttons_state(*buttons_state):
    #not used
    button_id, button_state = buttons_state

osc = OSCThreadServer()

# You can also use an \*nix socket path here
sock = osc.listen(address='0.0.0.0', port=8000, default=True)

osc.bind(b'/gyrosc/gyro', new_gyro_state)
osc.bind(b'/gyrosc/accel', new_accel_state)
osc.bind(b'/gyrosc/button', new_buttons_state)

sleep(1000)
osc.stop()  # Stop the default socket

