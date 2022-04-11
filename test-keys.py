import cv2

img = cv2.imread('hand-ids.png') # load a dummy image

while(True):
    cv2.imshow('img',img)
    k = cv2.waitKey(33)
    if k==27:    # Esc key to stop
        break
    elif k==-1:  # normally -1 returned,so don't print it
        continue
    else:
        print(k) # else print its value

# Space: 32
# Esc: 27
# Backspace: 8
# Enter: 13
# Tab: 9
# C: 99
# F: 102