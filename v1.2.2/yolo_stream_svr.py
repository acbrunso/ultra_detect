

# VERSION: 1.2.2
# implement ssh connect to start server on pi if it is not running already


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

from VideoThreading.CountsPerSec import CountsPerSec
from VideoThreading.VideoGet import VideoGet
from VideoThreading.YOLOPredictor import YOLOPredictor

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def toggle_predict(self, frame):
        if(self.predictor.stopped):
            #self.predict = False
            self.predictor.start(frame)

        else:
            #self.predict = True
            #print("stopping predictor")
            self.predictor.stop()

        
    def handle_resp(self, data):
        if(data == b'aa'):
            print('button clicked')
            #self.toggle_predict()
            return b'aa'
        elif(data == b'ab'):
            print('second button clicked')
            return b'ab'
        else:
            return b'00'
            
    def handle(self):
            
        self.predict = False
        data = b""
        r = b''
        payload_size = struct.calcsize(">L")
        print("payload_size: {}".format(payload_size))

        img_counter = 0
        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]


        #cap = cv2.VideoCapture(0)
        model = YOLO('yolov8n.pt')
        video_getter = VideoGet().start()
        cps = CountsPerSec().start()
        self.predictor = YOLOPredictor()
        while True:
            if video_getter.stopped:# or video_shower.stopped:
                #video_shower.stop()
                video_getter.stop()
                break
            frame = video_getter.frame
            frame = CountsPerSec.putIterationsPerSec(frame, cps.countsPerSec())
            cps.increment()

            extra_data = b''
            #print(r)
            if(r == b'aa'):
                print("toggle_predict")
                self.toggle_predict(frame)

            if(self.predictor.stopped == False):
                if img_counter%10==0:
                    results = self.predictor.results
                    self.predictor.frame = frame
                    if(results is not None):
                        #sending back an annotated frame only gives us 2 per second
                        #even though it is multithreaded. not sure why
                        annotated_frame = frame #self.predictor.annotated_frame
                        extra_data = pickle.dumps(results)
                    else:
                        annotated_frame = frame
                else:
                    annotated_frame = frame
                img_counter+=1
            

            else:
                annotated_frame = frame
            res, img = cv2.imencode('.jpg', annotated_frame, encode_param)
            
            data = pickle.dumps(img, 0)
            size = len(data)
            
            extra_data_size = len(extra_data)
            try:
                self.request.sendall(struct.pack(">L", size) + data + struct.pack(">L", extra_data_size) + extra_data)
                #self.request.sendall(struct.pack(">L", size) + data + struct.pack(">L", 0))
                r = self.handle_resp(self.request.recv(2).strip())
            except (ConnectionResetError, BrokenPipeError):
                video_getter.stop()
                self.predictor.stop()
            
           
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
        
