# -*- coding: utf-8 -*-
"""
Script that determines the rotation of the head and turns the car accordingly
The other actions are not implented here
mediapipe detects the mesh of the face in 3d and from that
the angle of the face in the 3-axis of rotation are computed  
vgamepad is used to emulate a joysitck
"""

import cv2
import numpy as np
import time
import vgamepad as vg

import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2


def draw_landmarks_on_image(rgb_image, detection_result):
  face_landmarks_list = detection_result.face_landmarks
  annotated_image = np.copy(rgb_image)

  # Loop through the detected faces to visualize.
  for idx in range(len(face_landmarks_list)):
    face_landmarks = face_landmarks_list[idx]

    # Draw the face landmarks.
    face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    face_landmarks_proto.landmark.extend([
      landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
    ])

    mp.solutions.drawing_utils.draw_landmarks(
        image=annotated_image,
        landmark_list=face_landmarks_proto,
        connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp.solutions.drawing_styles
        .get_default_face_mesh_tesselation_style())
    mp.solutions.drawing_utils.draw_landmarks(
        image=annotated_image,
        landmark_list=face_landmarks_proto,
        connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp.solutions.drawing_styles
        .get_default_face_mesh_contours_style())
    mp.solutions.drawing_utils.draw_landmarks(
        image=annotated_image,
        landmark_list=face_landmarks_proto,
        connections=mp.solutions.face_mesh.FACEMESH_IRISES,
          landmark_drawing_spec=None,
          connection_drawing_spec=mp.solutions.drawing_styles
          .get_default_face_mesh_iris_connections_style())

  return annotated_image

        
        
def joystick_play(yaw):
    joystick_deadzone = 0.2
    
    steer = yaw/16
    if abs(steer) < joystick_deadzone:
        steer = 0
    else:
        steer = (steer - 0.2*np.sign(steer))*1.25
        
    steer = np.clip(steer, -1, 1)
    gamepad.left_joystick_float(x_value_float=steer, y_value_float=0.0) 
    gamepad.update()
    return steer


cap = cv2.VideoCapture(0)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

#keyboard = Controller()

gamepad = vg.VX360Gamepad()

last_time = time.time()
is_playing = False 
while True:
    
    ret, img = cap.read()
    if not ret:
        break
    
    img = cv2.cvtColor(cv2.flip(img, 1), cv2.COLOR_BGR2RGB)
    img.flags.writeable = False
    results = face_mesh.process(img)
    img.flags.writeable = True
    
    #code from https://github.com/niconielsen32/ComputerVision/blob/master/headPoseEstimation.py
    #used to determine the face orientation
    img_h, img_w, img_c = img.shape
    face_3d = []
    face_2d = []
    keypoints = [33, 263, 1, 61, 291, 199]
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            for idx, lm in enumerate(face_landmarks.landmark):
                if idx in keypoints:
                    x, y = int(lm.x * img_w), int(lm.y * img_h)

                    # Get the 2D Coordinates
                    face_2d.append([x, y])

                    # Get the 3D Coordinates
                    face_3d.append([x, y, lm.z])       
            
            face_2d = np.array(face_2d, dtype=np.float64)
            face_3d = np.array(face_3d, dtype=np.float64)

            # The camera matrix
            focal_length = 1 * img_w

            cam_matrix = np.array([ [focal_length, 0, img_h / 2],
                                    [0, focal_length, img_w / 2],
                                    [0, 0, 1]])

            # The distortion parameters
            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            # Solve PnP
            success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)

            # Get rotational matrix
            rmat, jac = cv2.Rodrigues(rot_vec)

            # Get angles
            angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

            # Get the rotation degree
            pitch = angles[0] * 360
            yaw = angles[1] * 360
            roll = angles[2] * 360
        
            mp_drawing.draw_landmarks(
                image=img,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=drawing_spec,
                connection_drawing_spec=drawing_spec)
            
        yaw_offset = 0
        yaw += yaw_offset
        #determines the steer value from -1 to 1
        steer = joystick_play(yaw)
    
        #used to visualize the face mesh and the current input
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        m = img_w//2
        if steer < 0: 
            cv2.rectangle(img, (m-int(steer*-m), 0), (m, 50), (200, 0, 255), -1) #red box
        else:
            cv2.rectangle(img, (m, 0), (m+int(steer*m), 50), (255, 100, 0), -1) #blue box
    
        
        cv2.imshow("visualisation", img)
        k = cv2.waitKey(1)
        if (k & 0xFF) == ord('q'):
            break 
    
    new_time = time.time()
    #print(f"fps : {1/(new_time-last_time):.3f}")
    last_time = new_time
    
cv2.destroyAllWindows()
cap.release()










































