import cv2
import mediapipe as mp
import numpy as np
import math
import vgamepad as vg
import time
from pynput.keyboard import Key, Controller
import threading

keyboard = Controller()
gamepad = vg.VX360Gamepad()

# ---------------- Additional Functions ----------------
def play_accel(accel_state):
    if accel_state == 0:
        keyboard.release(Key.up)
        keyboard.release(Key.down)
    elif accel_state == 1:
        keyboard.press(Key.up)
        keyboard.release(Key.down)
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
    threading.Thread(target=object_thread).start()

def press_rescue():
    def rescue_thread():
        keyboard.press(Key.backspace)
        time.sleep(0.016)
        keyboard.release(Key.backspace)
    threading.Thread(target=rescue_thread).start()

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,  # More accurate inference
    enable_segmentation=False,
    min_detectionmp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=0,  # Faster inference
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Shared data for threading
lock = threading.Lock()
shared_data = {
    "frame": None,
    "angle1": None,
    "angle2": None,
    "angle3": None,
    "poses_person1": {
        "are_hands_toward_camera": False,
        "are_hands_crossed": False,
        "is_one_hand_above_head": False,
        "are_two_hand_above_head": False
    },
    "poses_person2": {
        "are_hands_toward_camera": False,
        "are_hands_crossed": False,
        "is_one_hand_above_head": False,
        "are_two_hand_above_head": False
    },
    "poses_person3": {
        "are_hands_toward_camera": False,
        "are_hands_crossed": False,
        "is_one_hand_above_head": False,
        "are_two_hand_above_head": False
    },
    "bbox_person1": None,
    "bbox_person2": None,
    "bbox_person3": None,
    "width": None,
    "third_width": None
}

zero_angle = None
reset_angle = False

action_cooldown = 1.0
action_cooldown_timers = {
    "accel": 0,
    "object": 0,
    "rescue": 0,
    "boost": 0
}

def detect_additional_poses(landmarks):
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    left_wrist = landmarks[15]
    right_wrist = landmarks[16]
    left_pinky = landmarks[17]
    right_pinky = landmarks[18]

    toward_thresh = 0.2
    are_hands_toward_camera = ((left_shoulder.z - left_wrist.z > toward_thresh) and
                               (right_shoulder.z - right_wrist.z > toward_thresh))

    crossed_thresh = 0.17
    are_hands_crossed = (
        (np.linalg.norm([left_pinky.x - right_shoulder.x, left_pinky.y - right_shoulder.y]) < crossed_thresh) and
        (np.linalg.norm([right_pinky.x - left_shoulder.x, right_pinky.y - left_shoulder.y]) < crossed_thresh)
    )

    hands_above_head = [left_wrist.y < left_shoulder.y, right_wrist.y < right_shoulder.y]
    is_one_hand_above_head = (sum(hands_above_head) == 1)
    are_two_hand_above_head = (sum(hands_above_head) == 2)

    if are_hands_crossed or is_one_hand_above_head or are_two_hand_above_head:
        are_hands_toward_camera = False

    return {
        "are_hands_toward_camera": are_hands_toward_camera,
        "are_hands_crossed": are_hands_crossed,
        "is_one_hand_above_head": is_one_hand_above_head,
        "are_two_hand_above_head": are_two_hand_above_head
    }

def get_bounding_box(landmarks, roi_x_offset, roi_width, height):
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]

    if len(xs) == 0 or len(ys) == 0:
        return None

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    x_min = int(min_x * roi_width) + roi_x_offset
    x_max = int(max_x * roi_width) + roi_x_offset
    y_min = int(min_y * height)
    y_max = int(max_y * height)

    return (x_min, y_min, x_max, y_max)

def process_pose(pose_results, roi_x_offset, roi_shape, height):
    angle_deg = None
    current_poses = {
        "are_hands_toward_camera": False,
        "are_hands_crossed": False,
        "is_one_hand_above_head": False,
        "are_two_hand_above_head": False
    }
    bbox = None

    if pose_results.pose_landmarks:
        landmarks = pose_results.pose_landmarks.landmark
        # Calculate angle
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

        midpoint_shoulder = (
            int(((left_shoulder.x + right_shoulder.x) / 2) * roi_shape[1]) + roi_x_offset,
            int(((left_shoulder.y + right_shoulder.y) / 2) * height)
        )
        midpoint_hip = (
            int(((left_hip.x + right_hip.x) / 2) * roi_shape[1]) + roi_x_offset,
            int(((left_hip.y + right_hip.y) / 2) * height)
        )

        delta_x = midpoint_hip[0] - midpoint_shoulder[0]
        delta_y = midpoint_hip[1] - midpoint_shoulder[1]
        angle_rad = math.atan2(delta_y, delta_x)
        angle_deg = math.degrees(angle_rad)

        # Detect additional poses
        current_poses = detect_additional_poses(landmarks)

        # Get bounding box
        bbox = get_bounding_box(landmarks, roi_x_offset, roi_shape[1], height)

    return angle_deg, current_poses, bbox

def pose_thread_func():
    global zero_angle, reset_angle
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape

        third_width = width // 3
        left_roi = frame[:, :third_width]
        center_roi = frame[:, third_width:2*third_width]
        right_roi = frame[:, 2*third_width:]

        rgb_left = cv2.cvtColor(left_roi, cv2.COLOR_BGR2RGB)
        rgb_center = cv2.cvtColor(center_roi, cv2.COLOR_BGR2RGB)
        rgb_right = cv2.cvtColor(right_roi, cv2.COLOR_BGR2RGB)

        pose_results_left = pose.process(rgb_left)
        pose_results_center = pose.process(rgb_center)
        pose_results_right = pose.process(rgb_right)

        angle1, poses_p1, bbox_p1 = process_pose(pose_results_left, 0, left_roi.shape, height)
        angle2, poses_p2, bbox_p2 = process_pose(pose_results_center, third_width, center_roi.shape, height)
        angle3, poses_p3, bbox_p3 = process_pose(pose_results_right, 2*third_width, right_roi.shape, height)

        # Compute mean angle from available angles
        angles = [a for a in [angle1, angle2, angle3] if a is not None]
        if len(angles) > 0:
            mean_angle = sum(angles) / len(angles)
        else:
            mean_angle = zero_angle if zero_angle is not None else 0

        if reset_angle:
            zero_angle = mean_angle
            reset_angle = False

        if zero_angle is not None:
            angle_difference = mean_angle - zero_angle
        else:
            angle_difference = 0

        cv2.putText(frame, f"Angle Difference: {angle_difference:.2f}°",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

        with lock:
            shared_data["frame"] = frame
            shared_data["angle1"] = angle1
            shared_data["angle2"] = angle2
            shared_data["angle3"] = angle3
            shared_data["poses_person1"] = poses_p1
            shared_data["poses_person2"] = poses_p2
            shared_data["poses_person3"] = poses_p3
            shared_data["bbox_person1"] = bbox_p1
            shared_data["bbox_person2"] = bbox_p2
            shared_data["bbox_person3"] = bbox_p3
            shared_data["width"] = width
            shared_data["third_width"] = third_width

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()

pose_thread = threading.Thread(target=pose_thread_func, daemon=True)
pose_thread.start()

cv2.namedWindow('Human Detection', cv2.WINDOW_NORMAL)
print("Press 'C' to reset the zero angle.")
print("Press 'Q' or 'Esc' to quit.")

while True:
    with lock:
        frame = shared_data["frame"]
        angle1 = shared_data["angle1"]
        angle2 = shared_data["angle2"]
        angle3 = shared_data["angle3"]
        poses_person1 = shared_data["poses_person1"]
        poses_person2 = shared_data["poses_person2"]
        poses_person3 = shared_data["poses_person3"]
        bbox_p1 = shared_data["bbox_person1"]
        bbox_p2 = shared_data["bbox_person2"]
        bbox_p3 = shared_data["bbox_person3"]
        width = shared_data["width"]
        third_width = shared_data["third_width"]

    if frame is None:
        time.sleep(0.01)
        continue

    # Debug prints for each person's pose state
    print("Person 1:", poses_person1)
    print("Person 2:", poses_person2)
    print("Person 3:", poses_person3)

    # Steering Calculation
    angles = [a for a in [angle1, angle2, angle3] if a is not None]
    if len(angles) > 0:
        mean_angle = sum(angles) / len(angles)
    else:
        mean_angle = zero_angle if zero_angle is not None else 0

    if zero_angle is not None:
        angle_difference = mean_angle - zero_angle
    else:
        angle_difference = 0


    angle_difference = max(min(angle_difference, 15), -15)
    joystick_x = angle_difference / 15
    joystick_y = 0.0

    # Update joystick for steering
    gamepad.left_joystick_float(x_value_float=joystick_x, y_value_float=joystick_y)
    gamepad.update()

    # Acceleration and actions logic
    any_two_hands_above = (poses_person1["are_two_hand_above_head"] or 
                           poses_person2["are_two_hand_above_head"] or
                           poses_person3["are_two_hand_above_head"])

    any_one_hand_above = (poses_person1["is_one_hand_above_head"] or 
                          poses_person2["is_one_hand_above_head"] or
                          poses_person3["is_one_hand_above_head"])

    any_hands_toward_camera = (poses_person1["are_hands_toward_camera"] or 
                               poses_person2["are_hands_toward_camera"] or
                               poses_person3["are_hands_toward_camera"])

    any_hands_crossed = (poses_person1["are_hands_crossed"] or
                         poses_person2["are_hands_crossed"] or
                         poses_person3["are_hands_crossed"])

    current_time = time.time()

    # Boost logic
    if any_two_hands_above:
        keyboard.press('n')
        play_accel(0)
    else:
        # Once hands are no longer above, release 'n'
        keyboard.release('n')
    
    if any_one_hand_above:
        # If one hand above, no acceleration
        if current_time - action_cooldown_timers["accel"] > action_cooldown:
            play_accel(0)
            action_cooldown_timers["accel"] = current_time
    else:
        # Otherwise accelerate
        if current_time - action_cooldown_timers["accel"] > action_cooldown:
            play_accel(1)
            action_cooldown_timers["accel"] = current_time

    if any_hands_toward_camera:
        if current_time - action_cooldown_timers["object"] > action_cooldown:
            press_object()
            action_cooldown_timers["object"] = current_time

    if any_hands_crossed:
        if current_time - action_cooldown_timers["rescue"] > action_cooldown:
            press_rescue()
            action_cooldown_timers["rescue"] = current_time

    # Draw bounding boxes
    if bbox_p1 is not None:
        x_min, y_min, x_max, y_max = bbox_p1
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        cv2.putText(frame, "Person 1", (x_min, y_min-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    if bbox_p2 is not None:
        x_min, y_min, x_max, y_max = bbox_p2
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        cv2.putText(frame, "Person 2", (x_min, y_min-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    if bbox_p3 is not None:
        x_min, y_min, x_max, y_max = bbox_p3
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        cv2.putText(frame, "Person 3", (x_min, y_min-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    # Display the ROI limits on the screen if we have the width and third_width
    if width is not None and third_width is not None:
        cv2.putText(frame, f"Left ROI: x 0 - {third_width}", (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Center ROI: x {third_width} - {2*third_width}", (10, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Right ROI: x {2*third_width} - {width}", (10, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow('Human Detection', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('c') or key == ord('C'):
        time.sleep(3)
        with lock:
            reset_angle = True
    elif key == ord('q') or key == 27:
        print("Exiting...")
        break

cv2.destroyAllWindows()
pose.close()