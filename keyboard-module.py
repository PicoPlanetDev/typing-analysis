import keyboard
import time

def on_press(event):
    print(event.name)

keys = ['q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m', ' ']
for key in keys:
    keyboard.on_press_key(key, on_press)

while True:
    time.sleep(100000) # wait for a very long time