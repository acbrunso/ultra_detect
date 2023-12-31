
# VERSION: 2.0.0
# implement audio live stream from server.  

import socket
import struct ## new
import pickle
from ssh_connect import SSHServer
import time


from PyQt5.QtCore import pyqtSignal, QThread
import sys
import cv2
import numpy as np
from Connection_Status import Connection_Status

from YMessenger import YMessenger

class VideoClient(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    change_connect_btn_signal = pyqtSignal(bool)

    def __init__(self, image_label, log_label, host = "", port = ""):
        super().__init__()
        self.return_val = b'00'
        self.host = host
        self.port = port
        self.results = None
        self.image_label = image_label
        self.record_it = False
        self.fps = 20.0
        self._run_flag = False
        self.sshServer = SSHServer()
        self.log_label = log_label
        self.predicting = False
        self.up_status_flag = Connection_Status.PENDING

    
    def connect(self, host, port):
        self.stop()
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(5)

        try:
            self.client_socket.connect((self.host, self.port))
            self.up_status_flag = Connection_Status.CONNECTED
            print("connected to video server. it was already running")
        except:
            self.sshServer.start(self.host, 'drone', 'drones')
            msg = self.sshServer.runVideoServer()
            time.sleep(3)
            try:
                print("trying to connect to " + str(self.host) + ". " + str(self.port))
                self.client_socket.connect((self.host, self.port))
                print("connected to video server. it was NOT running")
                self.up_status_flag = Connection_Status.CONNECTED
            except:
                print("failed to connect / video")
                self.log_label.appendPlainText('Failed to Connect to video on ' + self.host + '. Please try again.\n' + str(msg))
                self.up_status_flag = Connection_Status.VIDEO_ERROR
                return False

        return self.get_video()  


    def read(self, msg_size):
        data = b''
        while(len(data) < msg_size):
            try:
                if(msg_size - len(data) < 4096):
                    data += self.client_socket.recv(msg_size - len(data))                #this will grab to the end of the frame.  still need to grab to the end of the data
                else:
                    data += self.client_socket.recv(4096)  
            except(socket.timeout):
                print("there was a socket timeout error in video thread 1")
                self.client_socket.close()
                #self.audio_capturer.close()
                self._run_flag = False #does nothing
                self.up_status_flag = Connection_Status.SOCKET_TIMEOUT
                return -1 
            except(ConnectionAbortedError):
                print("there was a Connection Aborted error in video thread 1")
                self.client_socket.close()
                #self.audio_capturer.close()
                self._run_flag = False #does nothing
                self.up_status_flag = Connection_Status.CONNECTION_ABORTED
                return -1 
           
        return data
    
    def get_video(self):
        data = b''
        extra_data = b''
        payload_size = struct.calcsize(">L")
        #print("client: payload size: " + str(payload_size))        
        if((data := self.read(payload_size)) == -1):
            return False

        # receive image row data from client socket
        packed_msg_size = data[:payload_size]               #grab the length of the frame that was sent
        msg_size = struct.unpack(">L", packed_msg_size)[0]  #unpack the length of the frame so it is readable
        data = b''
        if((data := self.read(msg_size)) == -1):
            return False

        frame_data = data[:msg_size]                        #this is the frame data      

        #it was breaking here before
        if((packed_extra_data_size := self.read(4)) == -1):
            return False        
        
        extra_data_size = struct.unpack(">L", packed_extra_data_size)[0]
        #print("extra data size: " + str(extra_data_size))
        packed_extra_data = b''
        self.results = None
        if(extra_data_size > 0):
            if((packed_extra_data := self.read(extra_data_size)) == -1):
                return False
             
            extra_data = pickle.loads(packed_extra_data, fix_imports=True, encoding='bytes')
            self.results = extra_data

        if(len(frame_data) == 0):
            #this line will hit if the camera is disconnected
            print("camera not detected, breaking")
            blk_img = np.zeros((480, 640, 3), dtype=np.uint8)    
            self.change_pixmap_signal.emit(blk_img)
            self.up_status_flag = Connection_Status.VIDEO_ERROR
            self.client_socket.close()            
            print(self.results)
            return False
        # unpack image using pickle 
        frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        self.change_pixmap_signal.emit(frame)
        if(self.record_it == True):
            if(self.recording == False):
                self.recording = True
                self.start_recording(frame)
            self.out.write(frame)



        self.client_socket.sendall(self.return_val)
        self.return_val = b'00'  
        return True                 

    def set_host(self, host, port):
        self.host = host
        self.port = port

    def run(self):
        print('run it video')

        print("connecting")

        if not self.connect(self.host, self.port):
            print('failed to connect to video')
            self.change_connect_btn_signal.emit(False)
            return
        
        self.change_connect_btn_signal.emit(True)

        


        self._run_flag = True

        while self._run_flag:

            resp = self.get_video()           
            if(resp == False):
                break


            
            

        blk_img = np.zeros((480, 640, 3), dtype=np.uint8)    
        self.change_pixmap_signal.emit(blk_img)
        self.change_connect_btn_signal.emit(False)
        print("exiting video feed")
        self.client_socket.close()


    def start_recording(self, frame):
        print("start recording")
        fshape = frame.shape
        fheight = fshape[0]
        fwidth = fshape[1]
        print(fwidth , fheight)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(self.host + '_output.avi',fourcc, self.fps, (fwidth,fheight))

    def record(self):
        #if no video stream is running, we don't need to record.
        if(self._run_flag == False):
            return False
        
        if(self.record_it):
            print("self.record_it")
            self.record_it = False
            self.out.release()
            return False
        else:
            print("else self.record_it == false")
            self.record_it = True
            self.recording = False
            return True
        

    def populate_log(self):
        resp = ""
        if self.results is not None:
            print("we have a value in results")
            if(isinstance(self.results, list)):
                #print("populate log with predictions")
                for result in self.results:
                    for box in result.boxes:
                        resp+=result.names[int(box.cls[0])] + '\n'
                if(resp.replace('\n','') == ''):
                    return False, ''
                return True, resp
            else:
                print("Message returned from server")
                return True, self.results.message
        #else:
            #print("no results to populate log with")
        return False, resp
        

    def toggle_predictions(self):
        self.return_val = b'aa'
        if(self.predicting == True):
            self.predicting = False
        else:
            self.predicting = True

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        print("stopping video client")
        self._run_flag = False
        self.up_status_flag = Connection_Status.PENDING        
        #self.wait()

