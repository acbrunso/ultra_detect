
# VERSION: 2.0.0
# implement audio live stream from server.  

import socket
import struct ## new
import pickle
from ssh_connect import SSHServer
import time

from PyQt5.QtCore import pyqtSignal, QThread


from AudioCapturer import AudioCapturer
from Connection_Status import Connection_Status

class AudioClient(QThread):

    change_connect_btn_signal = pyqtSignal(bool)




    def __init__(self, log_label, host="", port=""):
        super().__init__()
        self.return_val = b'00'
        self.host = host
        self.port = port
        self._run_flag = False
        self.sshServer = SSHServer()
        self.log_label = log_label
        self.audio_capturer = AudioCapturer()
        self.up_status_flag = Connection_Status.PENDING

    def connect(self, host, port):
        self.stop()
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
        self.client_socket.settimeout(5)

        try:
            self.client_socket.connect((self.host, self.port))
            print("connected to audio server. it was already running")
            self.up_status_flag = Connection_Status.CONNECTED

        except:
            self.sshServer.start(self.host, 'drone', 'drones')
            msg = self.sshServer.runAudioServer()
            time.sleep(3)
            
            try:
                self.client_socket.connect((self.host, self.port))
                print("connected to audio server. it was NOT running")
                self.up_status_flag = Connection_Status.CONNECTED

            except:
                print("failed to connect / audio")
                self.log_label.appendPlainText('Failed to Connect to audio on ' + self.host + '. Please try again \n' + str(msg))
                self.up_status_flag = Connection_Status.VIDEO_ERROR

                return False
            
        self.audio_capturer.open(False, True)            
        return self.get_audio()

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
    

    def get_audio(self):
        data = b''
        extra_data = b''
        #print("client: payload size: " + str(payload_size))
        payload_size = struct.calcsize(">L")
        #print("looping in audio")

        if((data := self.read(payload_size)) == -1):
            return False

        # receive image row data form client socket
        packed_msg_size = data[:payload_size] #grab the length of the frame that was sent
        
        msg_size = struct.unpack(">L", packed_msg_size)[0]  #unpack the length of the frame so it is readable
        data = b''

        if((data := self.read(msg_size)) == -1):
            return False
        
        frame_data = data[:msg_size]                        #this is the frame data
        
        if((packed_extra_data_size := self.read(4)) == -1):
            return False
                           
        extra_data_size = struct.unpack(">L", packed_extra_data_size)[0]
        packed_extra_data = b''
        self.results = None

        if(extra_data_size > 0):
            if((packed_extra_data := self.read(extra_data_size)) == -1):
                return False
                    
            extra_data = pickle.loads(packed_extra_data, fix_imports=True, encoding='bytes')
            self.results = extra_data

        #play the frame data on the speaker
        #print(frame_data)
        self.audio_capturer.write(frame_data)

        # unpack image using pickle 
        #frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        #frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        self.client_socket.sendall(self.return_val)
        self.return_val = b'00'   
        return True     

    def set_host(self, host, port):
        self.host = host
        self.port = port

    def run(self):
       
        print("connecting on audio")



        if not self.connect(self.host, self.port):
            print('failed to connect to audio')
            self.change_connect_btn_signal.emit(False)
            return
        
        self.change_connect_btn_signal.emit(True)


        self._run_flag = True
        while self._run_flag:

            resp = self.get_audio()
            if(resp == False):
                break

            
        print("exiting audio feed")
        self.change_connect_btn_signal.emit(False)

        self.client_socket.close()
        self.audio_capturer.close()

    def stop(self):
        print("stopping audio client")
        self._run_flag = False
        self.up_status_flag = Connection_Status.PENDING        

        #self.wait()

