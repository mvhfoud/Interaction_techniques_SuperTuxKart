#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 18:50:51 2024

@author: maxime
"""

import time
import threading
from pynput.keyboard import Key, Controller
from multiprocessing import Process, Value, Array
#from playsound import playsound
#from oscpy.server import OSCThreadServer

#import cv2
#import keyboard
import numpy as np
import vgamepad as vg


tick_sound_zone = 0.2
do_tick = False
#tick_sound = AudioSegment.from_wav("tick2.wav")

def play_accel(accel_state):
    if accel_state == 0:
        keyboard.release(Key.up)
        
        # keyboard.press(Key.down)
        # time.sleep(1)
        
        keyboard.release(Key.down)
    
    elif accel_state == 1:
        keyboard.press(Key.up)
        keyboard.release(Key.down)
    
    elif accel_state == -1:
        keyboard.press(Key.down)
        keyboard.release(Key.up) 
        
    return accel_state


def press_boost(duration):
    def boost_thread(duration):
        keyboard.press('n')
        time.sleep(duration)
        keyboard.release('n')
        
    
    threading.Thread(target=boost_thread, args=(duration,)).start()
    
def press_object():
    def object_thread():
        keyboard.press(Key.space)
        time.sleep(0.016)
        keyboard.release(Key.space)
        
    
    threading.Thread(target=object_thread, args=()).start()
    
def press_rescue():
    def rescue_thread():
        keyboard.press(Key.backspace)
        time.sleep(0.016)
        keyboard.release(Key.backspace)
        
    
    threading.Thread(target=rescue_thread, args=()).start()

# def tick_sound():
#     threading.Thread(target=playsound, args=("tick2.wav",), daemon=True).start()
    

def release_direction():
    keyboard.release(Key.left)
    keyboard.release(Key.right)

def counter_drift(drift_direction, current_steer_command):
    _dir = (Key.left if drift_direction == -1 else Key.right)
    counter_dir = (Key.right if drift_direction == -1 else Key.left)
    
    release_direction()
    time.sleep(0.016)
    keyboard.press(_dir)
    time.sleep(0.1)
    keyboard.press("v")
    time.sleep(0.016)
    keyboard.release(_dir)
    
    start_drift_time = time.time()
    #temps que le turbo jaune charge
    while (time.time() - start_drift_time) < 1.0:
        current_steer = current_steer_command.value
        
        #drift a gauche
        if drift_direction == -1:
            counter_steer = (current_steer + 0.5) * 2
        #drift a droite
        elif drift_direction == 1:
            counter_steer = (current_steer - 0.5) * 2
            
            
        counter_steer = np.clip(counter_steer, -1, 1)
        joystick_play(counter_steer)
        time.sleep(0.016)
        
    
    keyboard.release("v")
    # release_direction()
    
def apply_steer_curve(val, deadzone=0.02, power=1):
    d = deadzone
    val = np.clip(val, -1, 1)
    new_val = max(0, (abs(val)**power - d) * ((1+d) / (1-d**2))) * np.sign(val)
    return new_val  
        
def orient_to_steer(orient, joystick_deadzone):
    steer = -3*orient
    steer = apply_steer_curve(steer, deadzone=joystick_deadzone)
    return steer

def joystick_play(steer):
    gamepad.left_joystick_float(x_value_float=steer, y_value_float=0.0) 
    gamepad.update()
    
# def new_matrix_state(*matrix_state):
#     global phone_orient

#     phone_orient = matrix_state[1]
#     #print(phone_orient)

gamepad = vg.VX360Gamepad()
keyboard = Controller()

# if __name__ == '__main__':
#     joystick_deadzone = 0.1
#     osc = OSCThreadServer()
    
#     # You can also use an \*nix socket path here
#     sock = osc.listen(address='0.0.0.0', port=8000, default=True)
    
#     osc.bind(b'/gyrosc/rmatrix', new_matrix_state)
    
#     drift_thread = None
#     drift_state = 0
    
#     drift_commands_queue = []
#     current_steer_command = Value('d', 0.0)
    
#     last_drift_time = time.time()
#     last_time = time.time()
#     yaw_offset = 0
#     is_playing = False 
    
#     phone_orient = 0
#     last_steer = 0 
#     steer = 0
#     img = None
#     while True:
#         steer = orient_to_steer(phone_orient, joystick_deadzone)
#         current_steer_command.value = steer
        
#         if ((steer > -tick_sound_zone and last_steer < -tick_sound_zone) or
#             (steer < tick_sound_zone and last_steer > tick_sound_zone)) and do_tick:
#             pass
#             #tick_sound()
        
#         #si on est en train de drift
#         if drift_state == 0:
#             joystick_play(steer)
#         #sinon, on est pas en train de drift et c'est le thread qui tourne
        
#         last_steer = steer
        
            
#     osc.stop()  # Stop the default socket           