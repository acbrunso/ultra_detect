

# VERSION 1.2.0


import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import argparse

import socketserver
import struct
import cv2
import io
import socket
import struct
import time
import pickle
import numpy as np
#import imutils
#import tensorflow as tf
from ultralytics import YOLO


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def toggle_predict(self):
        if(self.predict == True):
            self.predict = False
        else:
            self.predict = True
        
    def handle_resp(self, data):
        if(data == b'aa'):
            print('button clicked')
            self.toggle_predict()
            return 'aa'
        elif(data == b'ab'):
            print('second button clicked')
            return 'ab'
        elif(data == b'ac'):
            return 'exit'
        else:
            return b'00'
            
    def handle(self):
            
        self.predict = False
        data = b""
        payload_size = struct.calcsize(">L")
        print("payload_size: {}".format(payload_size))

        img_counter = 0
        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]


        cap = cv2.VideoCapture(0)
        model = YOLO('yolov8n.pt')

        while cap.isOpened():
            success, frame = cap.read()
            #frame = imutils.resize(frame, width=320)
            extra_data = b''
            if success:
                if(self.predict == True):
                    if img_counter%10==0:
                        results = model(frame, imgsz=320, verbose=False)
                        annotated_frame = results[0].plot()
                        extra_data = pickle.dumps(results)

                    else:
                        annotated_frame = frame
                    img_counter+=1
                

                else:
                    annotated_frame = frame
                res, img = cv2.imencode('.jpg', annotated_frame, encode_param)
                
                data = pickle.dumps(img, 0)
                size = len(data)
                #print(len(data))
                
                extra_data_size = len(extra_data)
                #print(extra_data_size)
                self.request.sendall(struct.pack(">L", size) + data + struct.pack(">L", extra_data_size) + extra_data)
                #print('sent it all')
                r = self.handle_resp(self.request.recv(2).strip())
                #print('received the response')
                if(r == 'exit'):
                    break
                #cv2.imshow('server',annotated_frame)

            else:
                continue
        cap.release()
        cv2.destroyAllWindows()





if __name__ == "__main__":
    HOST = "0.0.0.0"
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-p', '--port', required = True)
    args = parser.parse_args()
    PORT = int(args.port)
    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        print('serving')
        server.serve_forever()
        
