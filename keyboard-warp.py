import copy
from turtle import position
from charset_normalizer import detect
import cv2
import numpy as np
import HandTrackingModule as htm
import pickle
import keyboard

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap. set(cv2.CAP_PROP_FPS, 60)

def collect_points():
    """Collect corner points of the keyboard in left to right order,
    starting from the top left corner as follows:
    1 2
    3 4
    """
    def mouse_event(event,x,y,flags,param):
        nonlocal points
        if event == cv2.EVENT_LBUTTONUP:
            points.append([x,y])

    print("Select four corners of the keyboard in the following order:")
    print("1 2")
    print("3 4")
    print("Press 'f' to finish")
    cv2.namedWindow("calibration")
    cv2.setMouseCallback('calibration', mouse_event)
    points = []
    while True:
        success, img = cap.read()
        for point in points:
            cv2.circle(img, point, 5, (0,0,255), -1)
        num_points = len(points)
        if num_points == 4:
            cv2.line(img, points[0], points[1], (0,255,0), 2)
            cv2.line(img, points[1], points[3], (0,255,0), 2)
            cv2.line(img, points[3], points[2], (0,255,0), 2)
            cv2.line(img, points[2], points[0], (0,255,0), 2)
        cv2.imshow("calibration", img)
        if cv2.waitKey(1) == ord('f'): break
    cv2.destroyWindow("calibration")
    return points

# keyboard is 435x123 millimeters
# 1280x720 pixels
# 1000x283 pixels keyboard
# 2.3x ratio
# 280 extra space on the left and right = 140 per side

def get_warp_matrix(points):
    keyboard_width, keyboard_height = 1000, 283
    image_width, image_height = 1280, 720
    x_offset = (image_width-keyboard_width)/2
    inputPts = np.float32(points)
    outputPts = np.float32([[x_offset,image_height-keyboard_height],
                            [image_width-x_offset,image_height-keyboard_height],
                            [x_offset,image_height],
                            [image_width-x_offset,image_height]])
    matrix = cv2.getPerspectiveTransform(inputPts, outputPts)
    return matrix

def warp_image(img, matrix):
    return cv2.warpPerspective(img, matrix, (1280,720))

def get_key_positions(matrix):
    def mouse_event(event,x,y,flags,param):
        if event == cv2.EVENT_LBUTTONUP:
            positions.append([x,y])

    positions = []

    print("Click Q W A Z")

    cv2.namedWindow("keyboard")
    cv2.setMouseCallback('keyboard', mouse_event)
    while True:
        success, img = cap.read()

        img = warp_image(img, matrix)

        for position in positions:
            cv2.circle(img, position, 5, (0,0,255), -1)

        cv2.imshow("keyboard", img)

        if cv2.waitKey(1) == ord("f"):
            cv2.destroyWindow("keyboard")
            return positions

# Fingers
# 4 = thumb
# 8 = index
# 12 = middle
# 16 = ring
# 20 = pinky

def get_position_from_lmList(lmList, finger):
    return lmList[finger][1:]

def extend_finger_position(lmList, finger):
    THUMB_MULTIPLIER = 0
    INDEX_MULTIPLIER = 0.2
    MIDDLE_MULTIPLIER = 0.1
    RING_MULTIPLIER = 0.2
    PINKY_MULTIPLIER = 0.3
    if finger == 4: multiplier = THUMB_MULTIPLIER
    elif finger == 8: multiplier = INDEX_MULTIPLIER
    elif finger == 12: multiplier = MIDDLE_MULTIPLIER
    elif finger == 16: multiplier = RING_MULTIPLIER
    elif finger == 20: multiplier = PINKY_MULTIPLIER
    end = lmList[finger][1:]
    start = lmList[finger-1][1:]
    change = [end[0]-start[0], end[1]-start[1]]
    change = [change[0]*multiplier, change[1]*multiplier]
    return [round(end[0]+change[0]), round(end[1]+change[1])]

def convert_letter_to_number(letter):
    return ord(letter) - ord('a') # uses ASCII codes which start at 97 for a

def hook_key_presses(detection):
    keys = ['q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m', ' ']
    for key in keys:
        keyboard.on_press_key(key, detection.on_key_pressed)

class key_detection():
    def __init__(self):
        self.detector = htm.handDetector()
        self.init_data()

    def calibrate(self):
        points = collect_points()
        self.matrix = get_warp_matrix(points)
        key_positions = get_key_positions(self.matrix)
        self.calibration = self.get_key_spacing(key_positions)
        return self.matrix, self.calibration

    def save_calibration(self):
        file_matrix = open('matrix.pkl', 'wb')
        pickle.dump(self.matrix, file_matrix)

        file_calibration = open('calibration.pkl', 'wb')
        pickle.dump(self.calibration, file_calibration)

    def load_calibration(self):
        self.matrix = pickle.load(open('matrix.pkl', 'rb'))
        self.calibration = pickle.load(open('calibration.pkl', 'rb'))
        self.q_position = self.calibration[4]
        self.horizontal_spacing = self.calibration[0]
        self.vertical_spacing = self.calibration[1]
        self.middle_offset = self.calibration[2]
        self.bottom_offset = self.calibration[3]
        return self.matrix, self.calibration

    def get_key_spacing(self, positions):
        self.q_position = positions[0]
        self.horizontal_spacing = positions[1][0] - positions[0][0]
        self.vertical_spacing = positions[2][1]-positions[0][1]
        #self.top_offset = 0
        self.middle_offset = positions[2][0]-positions[0][0]
        self.bottom_offset = positions[3][0]-positions[0][0]
        return self.horizontal_spacing, self.vertical_spacing, self.middle_offset, self.bottom_offset, self.q_position
    
    def evaluate_key(self, position):
        TOP_ROW = ['q','w','e','r','t','y','u','i','o','p']
        MIDDLE_ROW = ['a','s','d','f','g','h','j','k','l']
        BOTTOM_ROW = ['z','x','c','v','b','n','m']
        SPACE = 'space'
        relative_position = [position[0]-self.q_position[0], position[1]-self.q_position[1]]
        vertical_index = relative_position[1]/self.vertical_spacing
        #print(vertical_index)
        if vertical_index < 0.5:
            row = TOP_ROW
        elif vertical_index > 0.5 and vertical_index < 1.5:
            relative_position[0] -= self.middle_offset
            row = MIDDLE_ROW
        elif vertical_index > 1.5 and vertical_index < 2.5:
            relative_position[0] -= self.bottom_offset
            row = BOTTOM_ROW
        elif vertical_index > 2.5 and vertical_index < 4:
            self.key = SPACE
            return self.key
        else:
            return None
        horizontal_index = relative_position[0]/self.horizontal_spacing
        if round(horizontal_index) < 0 or round(horizontal_index) > len(row)-1: return None
        self.key = row[round(horizontal_index)]
        return self.key    

    def find_hands(self, img):
        return self.detector.findHands(img, draw=False)

    def get_lmLists(self, img):
        self.valid_lmLists = []
        try:
            lmList1 = self.detector.findPosition(img, handNo=0, draw=False)
            self.valid_lmLists.append(lmList1)
        except: pass
        try:
            lmList2 = self.detector.findPosition(img, handNo=1, draw=False)
            self.valid_lmLists.append(lmList2)
        except: pass
        return img

    def get_fingers_keys(self):
        self.fingers_keys = []
        self.finger_positions = []
        for hand,lmList in enumerate(self.valid_lmLists):
            if len(lmList) > 1:
                fingers = [4,8,12,16,20] # thumb, index, middle, ring, pinky end points
                self.finger_positions = [extend_finger_position(lmList, finger) for finger in fingers]

                for finger,position in enumerate(self.finger_positions):                    
                    key = self.evaluate_key(position)
                    if key != None:
                        self.fingers_keys.append([hand,finger,key,position])
        return self.fingers_keys

    def draw_fingers_debug(self, img):
        for i in range(len(self.fingers_keys)):
            position = self.fingers_keys[i][3]
            cv2.circle(img, position, 5, (0,0,255), -1) # show the extended position
            cv2.putText(img, self.fingers_keys[i][2], position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        return img

    def init_data(self):
        self.finger_keys = []
        #TODO: Convert this loop to a comprehension
        for hand in range(2):
            self.finger_keys.append([])
            for finger in range(0,5):
                self.finger_keys[hand].append([])
        
        self.key_fingers = []
        for i in range(28):
            self.key_fingers.append([])

    def collect_data(self, hand_id, finger_id, pressed_key):
        self.finger_keys[hand_id][finger_id].append(pressed_key)
        if pressed_key == "space":
            self.key_fingers[27].append([hand_id,finger_id])
        self.key_fingers[convert_letter_to_number(pressed_key)].append([hand_id,finger_id])

    def on_key_pressed(self, event):
        pressed_key = event.name
        fingers_keys = self.get_fingers_keys()
        # index = [finger for finger,key_data in enumerate(fingers_keys) \
        #     for key in key_data if key==pressed_key]
        indexes = [finger for finger,key_data in enumerate(fingers_keys) if key_data[2]==pressed_key]
        # for finger,key_data in enumerate(fingers_keys):
        #     if key_data[2] == pressed_key:
        #         index = finger
        #         break
        for index in indexes:
            finger_id = fingers_keys[index][1]
            hand_id = fingers_keys[index][0]
            self.collect_data(hand_id, finger_id, pressed_key)
            print(hand_id, finger_id, pressed_key)

def remove_duplicates(data):
    data_copy = copy.deepcopy(data)
    for hand in range(2):
        for finger in range(5):
            data_copy[hand][finger] = list(set(data[hand][finger]))
    return data_copy
    

def interactive_interpret_data(finger_keys, key_fingers):
    def start():
        print('Interactive mode')
        print('Send exit to quit')
        while True:
            user_input = input()
            if user_input == 'exit': break
            if user_input == 'keysbyfingers': show_letters_by_fingers(finger_keys)
            if user_input == 'fingersbykeys': show_fingers_by_letters(key_fingers)
    
    def show_letters_by_fingers(finger_keys):
        print("Type a finger to see its data, or type exit")
        print("Format like this hand_id,finger_id")
        print("Where hand_id 0 is right hand, 1 is left hand")
        print("Where finger_id 0 is thumb, 1 is index, 2 is middle, 3 is ring, 4 is pinky")
        clean_finger_keys = remove_duplicates(finger_keys)
        while True:
            user_input = input()
            if user_input == 'exit': break
            try:
                hand_id, finger_id = [int(x) for x in user_input.split(',')]
                print(clean_finger_keys[hand_id][finger_id])
            except:
                print("Invalid input")
    
    def show_fingers_by_letters(key_fingers):
        while True:
            user_input = input()
            if user_input == 'exit': break
            try:
                key = user_input
                print(key_fingers[convert_letter_to_number(key)])
            except:
                print("Invalid something")
    
    start()
    

def main(run_calibration=False):
    detection = key_detection()

    if run_calibration:
        matrix, calibration = detection.calibrate()
        detection.save_calibration()
    else:
        try:
            matrix, calibration = detection.load_calibration()
        except:
            main(run_calibration=True)

    hook_key_presses(detection)

    cv2.namedWindow("main")
    while True:
        success, img = cap.read()
        img = warp_image(img, matrix)

        img = detection.find_hands(img)
        img = detection.get_lmLists(img)
        fingers_keys = detection.get_fingers_keys()
        img = detection.draw_fingers_debug(img)

        flipped = cv2.flip(img, -1) # Flip the image for display

        cv2.imshow("main", flipped)
        keyboard_input = cv2.waitKey(1)
        if keyboard_input == 27:
            cv2.destroyWindow("main")
            interactive_interpret_data(detection.finger_keys, detection.key_fingers)
            break
        if keyboard_input == 99:
            cv2.destroyWindow("main")
            main(run_calibration=True)
            break
    
main()

cap.release()
cv2.destroyAllWindows()