#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programme principale pour controller le jeu avec l'orientation de la chaise et les gestes
Utilise le script "chair_control" pour gerer les inputs envoyes au jeu 
et le scrit "hand_commands" pour detecter les postions de la personne sur la chaise

La camera est positionee au format portrait pour avoir un plus grand champ de vision vertical

"new_matrix_state" est un callback qui recoit l'angle du telephone et qui tourne en simulant un joystick
Dans la boucle principale une image est capturee, les landmarks sont detectes, la postion de la personne est determinee

"""

import cv2
import mediapipe as mp
import time
import threading
from multiprocessing import Value
from oscpy.server import OSCThreadServer

from chair_control import (play_accel, press_boost, press_object, press_rescue, 
                           counter_drift, orient_to_steer, joystick_play)

from hand_commands import detect_pose


#Une deadzone a 0 permet a l'utilisateur d'avoir un feedback plus rapide
#de la rotation exacte de la chaise
joystick_deadzone = 0.0
    
def new_matrix_state(*matrix_state):
    global drift_state
    global current_steer_command  

    phone_orient = matrix_state[1]
    steer = orient_to_steer(phone_orient, joystick_deadzone)
    current_steer_command.value = steer
    
    #Si on est pas en train de drift
    if drift_state == 0:
        joystick_play(steer)
        
    #Sinon, on en train de drift et c'est le thread "drift_thread" qui s'occupe de tourner
    

#On utilise la matrice de rotation envoyee par OSC    
osc = OSCThreadServer()
sock = osc.listen(address='0.0.0.0', port=8000, default=True)
osc.bind(b'/gyrosc/rmatrix', new_matrix_state)

drift_thread = None
drift_state = 0 #-1 = drift a gauche; 0 = pas de drift; 1 = drift a droite

drift_commands_queue = []
current_steer_command = Value('d', 0.0)
last_drift_time = time.time()

last_pose_label = None

cap = cv2.VideoCapture(2)
#La taille de l'image est reduite pour augmenter les performances 
#De la detection des landmarks et diminuer le delai de detection de la position
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

#mp_pose.Pose realise la detection des gestes
with mp_pose.Pose(
    min_detection_confidence=0.2,
    min_tracking_confidence=0.2,
    smooth_landmarks=True,
    model_complexity=0) as pose:
  while cap.isOpened():
    success, image = cap.read()
    if not success:
      continue

    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    if not results.pose_landmarks:
        continue
    
    #On obtient les landmarks de la personne
    landmarks = results.pose_landmarks.landmark
    
    #On en deduis dans quelle position il est
    pose_label = detect_pose(landmarks)
    
    #Si on ne drift plus et que le thread de drift s'est termine
    if drift_state != 0 and not drift_thread.is_alive():
        #On reset les variables associes au drift
        drift_thread = None
        drift_state = 0
        last_drift_time = time.time()
    
    #Si l'utilisateur change de position
    if last_pose_label is None or pose_label != last_pose_label:
        #On joue l'input associe a la nouvelle position
        
        if pose_label == "HANDS_SHOULDER":
            play_accel(accel_state=0)
            
        elif pose_label == "HANDS_KNEE":
            play_accel(accel_state=1)
        
        elif pose_label == "HANDS_HIPS":
            press_boost(0.5)
            play_accel(accel_state=1)
        
        elif pose_label == "HANDS_KNEE_CROSS":
            press_object()
            
        elif pose_label == "HANDS_SHOULDER_CROSS":
            press_rescue()
    
        elif (pose_label in ["RIGHT_HAND_ABOVE_KNEE", "LEFT_HAND_ABOVE_KNEE"] and
              len(drift_commands_queue) < 1):
            #les commandes de drift sont ajoutes a une file
            #cela permet d'enchainer les drifts plus facilement
            drift_commands_queue.append((pose_label=="LEFT_HAND_ABOVE_KNEE",
                                         pose_label=="RIGHT_HAND_ABOVE_KNEE"))
            
        last_pose_label = pose_label
    
    #Si on a une commande de drift dans la file et qu'on n'est pas en train de drifter
    #Il faut attendre au minimum 0.6s pour pouvoir drifter a nouveau apres la fin d'un drift
    if len(drift_commands_queue) > 0 and (
            drift_state == 0 and (time.time() - last_drift_time) > 0.6):
        #On effectue le drift
        
        left_drift_cmd, right_drift_cmd = drift_commands_queue.pop(0)
        
        #Les drifts sont executes dans un thread pour ne pas perturber la boucle principale du programme
        
        if left_drift_cmd:
            drift_thread = threading.Thread(
                target=counter_drift,
                name="Drift thread",
                args=(-1, current_steer_command)
            )
            drift_thread.start()
            drift_state = -1
            
        elif right_drift_cmd:
            drift_thread = threading.Thread(
                target=counter_drift,
                name="Drift thread",
                args=(1, current_steer_command)
            )
            drift_thread.start()
            drift_state = 1
    
    #Dessine les landmarks sur l'image ainsi que la position detectee
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    
    cv2.putText(image, f"Pose: {pose_label}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    image = cv2.resize(image, None, fx=0.5, fy=0.5)
    cv2.imshow('MediaPipe Pose', image)
    if cv2.waitKey(1) & 0xFF == 27:
      break 
  
cap.release()
cv2.destroyAllWindows()











































