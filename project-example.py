import cv2
import HandTrackingModule as htm
 
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
detector = htm.handDetector()
while True:
    success, img = cap.read()
    img = detector.findHands(img, draw=False)
    lmList = detector.findPosition(img, draw=True)
    if len(lmList) != 0:
        print(lmList[4])

    cv2.imshow("Image", img)
    if cv2.waitKey(1) == ord('q'): break