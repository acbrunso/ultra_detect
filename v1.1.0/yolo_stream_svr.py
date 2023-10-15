

# VERSION 1.1.0

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'


import cv2
import io
import socket
import struct
import time
import pickle
import numpy as np

from ultralytics import YOLO


HOST=''
PORT=8485

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

s.bind((HOST,PORT))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn,addr=s.accept()

data = b""
payload_size = struct.calcsize(">L")
print("payload_size: {}".format(payload_size))

#cam = cv2.VideoCapture(0)
img_counter = 0
encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]


cap = cv2.VideoCapture(0)
model = YOLO('yolov8n.pt')

predict = False

        

while cap.isOpened():
    success, frame = cap.read()
    if success:
        if(predict == True):
            if img_counter%10==0:
                results = model(frame, imgsz=320, verbose=False)
                annotated_frame = results[0].plot()
                extra_data = pickle.dumps(results)

            else:
                annotated_frame = frame
            img_counter+=0
        else:
            annotated_frame = frame
        res, img = cv2.imencode('.jpg', annotated_frame, encode_param)
        data = pickle.dumps(img, 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data)
        r = conn.recv(2).strip()
        if(r == b'aa' and predict == True):
            print('toggling off')
            print(r)
            predict = False
        elif(r == b'aa' and predict == False):
            print('toggling on')
            print(r)
            predict = True
        #if running gui on the pi, you can uncomment this line to see video on the pi also
        #cv2.imshow('server',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break
cap.release()
cv2.destroyAllWindows()
conn.close()



