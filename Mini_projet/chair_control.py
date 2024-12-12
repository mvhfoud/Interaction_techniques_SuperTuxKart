#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programme contenant les fonctions utiles pour interagir avec le jeu
(accelerer vers l'avant ou l'arriere, boost, lancer objet, rescue, tourner en utilisant le joystick)

Les fonctions qui consistent a appuyer et relacher un bouton sont lances via un thread
pour ne pas impacter la boucle pricipale
"""

import time
import threading
from pynput.keyboard import Key, Controller
from multiprocessing import Value
from oscpy.server import OSCThreadServer


import numpy as np
import vgamepad as vg

sens = 2.5
joy_curve_power = 1.15

def play_accel(accel_state):
    if accel_state == 0:
        keyboard.release(Key.up)
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
    

def release_direction():
    keyboard.release(Key.left)
    keyboard.release(Key.right)
    


def counter_drift(drift_direction, current_steer_command):
    """
    Fonction executee dans un thread pour drift
    Le drift est declenche quand on leve la main gauche ou droite
    Pour augmenter la performance du setup ce drift a une direction en fonction de la main levee
    Le drift dure automatiquement 1s pour permettre d'avoir le boost jaune en sortie de drift
    Ce thread connait la valeur courante de steering "current_steer_command" qui est une variable partagee
    Cette valeur est utilisee pour changer le steering de sorte a ce que tourner dans la direction
    opposee au drift soit plus simple (c'est pour ca que la fonction s'appele conter_steer)
    """
    
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
            #le steering change pour tourner plus facilement dans la direction opposée au drift
            counter_steer = (current_steer + 0.5) * 2
        #drift a droite
        elif drift_direction == 1:
            counter_steer = (current_steer - 0.5) * 2
            
            
        counter_steer = np.clip(counter_steer, -1, 1)
        joystick_play(counter_steer)
        time.sleep(0.016)
        
    
    keyboard.release("v")

def apply_steer_curve(val, deadzone=0.1, power=1):
    """
    Permet d'ajouter une deadzone au joystick pour pouvoir aller tout droit plus facilement,
    d'appliquer une puissance a la courbe (ex x**1.2) pour avoir plus de precision vers le centre de la courbe,
    de clip les valeurs entre -1 et 1 (-1 = completement a gauche, 1 = completement a droite)
    """
    d = deadzone
    val = np.clip(val, -1, 1)
    #J'ai utilise le site desmos.com pour m'aider a trouver cette fonction
    new_val = max(0, (abs(val)**power - d) * ((1+d) / (1-d**2))) * np.sign(val)
    return new_val  
        
def orient_to_steer(orient, joystick_deadzone):
    """L'orientation du telephone est convertie en valeur de steer"""
    steer = -sens*orient
    steer = apply_steer_curve(steer, deadzone=joystick_deadzone, power=joy_curve_power)
    return steer

def joystick_play(steer):
    """Pour tourner en utilsant le joystick virtuel"""
    gamepad.left_joystick_float(x_value_float=steer, y_value_float=0.0) 
    gamepad.update()
    
def new_matrix_state(*matrix_state):
    """Recoit via OSC l'orientation du telephone"""
    global phone_orient

    phone_orient = matrix_state[1]

gamepad = vg.VX360Gamepad()
keyboard = Controller()

if __name__ == '__main__':
    #Si on veut juste tester la direction via l'angle du telephone
    
    joystick_deadzone = 0.1
    osc = OSCThreadServer()
    
    sock = osc.listen(address='0.0.0.0', port=8000, default=True)
    
    osc.bind(b'/gyrosc/rmatrix', new_matrix_state)
    
    phone_orient = 0
    while True:
        steer = orient_to_steer(phone_orient, joystick_deadzone)
    osc.stop()  # Stop the default socket           