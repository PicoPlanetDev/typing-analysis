import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 60)

fourcc = cv2.VideoWriter_fourcc('X','V','I','D')
videoWriter = cv2.VideoWriter('recording.avi', fourcc, 60.0, (1280,720))

while (True):
    ret, frame = cap.read()
    if ret:
        cv2.imshow('video', frame)
        videoWriter.write(frame)

    if cv2.waitKey(1) == 27: break

cap.release()
videoWriter.release()
cv2.destroyAllWindows()