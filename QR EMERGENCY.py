import numpy as np
from djitellopy import tello
import cv2
from pyzbar.pyzbar import decode
from time import sleep
#import moveZ
me = tello.Tello()
me.connect()
print(me.get_battery())
me.streamon()
me.takeoff()

# me.send_rc_control(0, 0, -5, 0)

cap = cv2.VideoCapture(1)
hsvVals = [0,0,238,179,255,255] ##color
sensors = 3
threshold = 0.2
width, height = 480, 360

senstivity = 3 # if number is high less sensitive
weight = [-25, -15, 0, 15, 25]
          ##0   1   2   3   4
fSpeed = 15
curve = 0

def get_qr():
    my_data = "null"
    image = me.get_frame_read().frame

    for barcode in decode(image):
        my_data = barcode.data.decode('utf-8')
        print(" QR : " + my_data)

    return my_data

def thresholding(img): ##camera
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([hsvVals[0],hsvVals[1],hsvVals[2]])
    upper = np.array([hsvVals[3],hsvVals[4],hsvVals[5]])
    mask = cv2.inRange(hsv, lower, upper)
    return mask

def getContours(imgThres, img): ##bulatan tgh
    cx = 0
    contours, hieracrhy = cv2.findContours(imgThres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        biggest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(biggest)
        cx = x + w // 2
        cy = y + h // 2
        cv2.drawContours(img, biggest, -1, (255, 0, 255), 7)
        cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

    return cx


def getSensorOutput(imgThres, sensors): ##split three different section
    imgs = np.hsplit(imgThres, sensors)
    totalPixels = (img.shape[1] // sensors) * img.shape[0]
    senOut = []
    for x, im in enumerate(imgs):
        pixelCount = cv2.countNonZero(im)
        if pixelCount > threshold*totalPixels:
            senOut.append(1)
        else:
            senOut.append(0)
        #cv2.imshow(str(x), im)
    #print(senOut)
    return senOut


def senCommands(senOut, cx):
    global curve

    ## TRANSLATION
    lr = (cx - width // 2)// senstivity
    lr = int(np.clip(lr, -10, 10))
    if lr <2 and lr > -2: lr = 0   ##kalau error

    ##Rotation
    if   senOut == [1, 0, 0]: curve = weight[0]
    elif senOut == [1, 1, 0]: curve = weight[1]
    elif senOut == [0, 1, 0]: curve = weight[2]
    elif senOut == [0, 1, 1]: curve = weight[3]
    elif senOut == [0, 0, 1]: curve = weight[4]

    elif senOut == [0, 0, 0]: curve = weight[2]   ##
    elif senOut == [1, 1, 1]: curve = weight[2]
    elif senOut == [1, 0, 1]: curve = weight[2]


    me.send_rc_control(lr, fSpeed, 0, curve)


noQr = 0
while True:
    #_, img = cap.read()
    img = me.get_frame_read().frame
    img = cv2.resize(img, (width, height))
    img = cv2.flip(img, 0)

    imgThres = thresholding(img)
    cx = getContours(imgThres, img) ## for translation
    senOut = getSensorOutput(imgThres, sensors) ## Rotation
    #get_qr()
    kod = get_qr()


    if kod[0] == 'N' and noQr == 0:  ##---->
      print("QR 1")
      sleep(2)
      me.rotate_counter_clockwise(90)
      me.move_forward(50)
      noQr=noQr+1
    elif kod[0] == 'N' and noQr == 1: ##  ^
      sleep(2)
      me.move_up(50)
      me.move_forward(50)
      sleep(2)
      # me.move_down(50)
      print("QR no 2")
      noQr = noQr + 1
    elif kod[0] == 'N' and noQr == 2: ##  ^
      me.move_down(50)
      me.move_forward(50)
      print("QR no 3")
      noQr = noQr + 1
    elif kod[0] == 'W' and noQr == 3:  ##<--------->
        sleep(2)
        me.rotate_counter_clockwise(90)
        me.move_forward(50)
        # me.rotate_clockwise(180)
        # me.land()
        print("QR no 4")
        noQr = noQr + 1
    #
    #
    #
    print(me.get_battery())
    senCommands(senOut, cx)
    cv2.imshow("Output", img)
    cv2.imshow("Path", imgThres)
    cv2.waitKey(1)
