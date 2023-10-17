
# VERSION: 2.0.0
# implement audio live stream from server.  

import socket
import struct ## new
import pickle
from ssh_connect import SSHServer
import time

from PyQt5.QtCore import QThread


from AudioCapturer import AudioCapturer

class AudioClient(QThread):
    def __init__(self, log_label, host="", port=""):
        super().__init__()
        self.return_val = b'00'
        self.host = host
        self.port = port
        self._run_flag = False
        self.sshServer = SSHServer()
        self.log_label = log_label
        self.audio_capturer = AudioCapturer()

    def setHost(self, host, port):
        self.stop()
        self.host = host
        self.port = port

    def run(self):
        print('run it audio')
        if(self.host == "" or self.port == ""):
            print("no value, returning")
            return
        print("connecting")
        print(self.host)
        print(self.port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(5)

        try:
            self.client_socket.connect((self.host, self.port))
            print("connected to audio server. it was already running")
        except:
            self.sshServer.start(self.host, 'drone', 'drones')
            msg = self.sshServer.runAudioServer()
            time.sleep(3)
            
            try:
                self.client_socket.connect((self.host, self.port))
                print("connected to audio server. it was NOT running")

            except:
                print("failed to connect / audio")
                self.log_label.appendPlainText('Failed to Connect to audio on ' + self.host + '. Please try again \n' + str(msg))
                return
            
        self.audio_capturer.open(False, True)

        extra_data = b''
        payload_size = struct.calcsize(">L")
        print("client: payload size: " + str(payload_size))
        self._run_flag = True
        payload_size = struct.calcsize(">L")

        while self._run_flag:
            data = b''
            #print("looping in audio")
            while len(data) < payload_size:
                try:
                    data += self.client_socket.recv(payload_size)
                except socket.timeout:
                    print("there was a socket timeout error in audio thread 1")
                    print("exiting audio feed")
                    self.client_socket.close()
                    self.audio_capturer.close()
                    self._run_flag = False #does nothing
                    return

                # receive image row data form client socket
                packed_msg_size = data[:payload_size] #grab the length of the frame that was sent
            
            msg_size = struct.unpack(">L", packed_msg_size)[0]  #unpack the length of the frame so it is readable
            data = b''

            while len(data) < msg_size:
                try:
                    if(msg_size - len(data) < 4096):
                        data += self.client_socket.recv(msg_size - len(data))                #this will grab to the end of the frame.  still need to grab to the end of the data
                    else:
                        data += self.client_socket.recv(4096)
                except socket.timeout:
                    self._run_flag = False
                    print("there was a socket timeout error in audio thread 2")
                    print("exiting audio feed")
                    self.client_socket.close()
                    self.audio_capturer.close()
                    self._run_flag = False #does nothing
                    return


            frame_data = data[:msg_size]                        #this is the frame data
            

            try:
                packed_extra_data_size = self.client_socket.recv(4)
            except socket.timeout:
                print("there was a socket timeout error in audio thread 3")
                print("exiting audio feed")
                self.client_socket.close()
                self.audio_capturer.close()
                self._run_flag = False #does nothing
                return                

            extra_data_size = struct.unpack(">L", packed_extra_data_size)[0]
            packed_extra_data = b''
            self.results = None
            if(extra_data_size > 0):
                while(len(packed_extra_data) < extra_data_size):
                    try:
                        if(extra_data_size - len(packed_extra_data) < 4096):
                            packed_extra_data += self.client_socket.recv(extra_data_size - len(packed_extra_data))
                        else:
                            packed_extra_data += self.client_socket.recv(4096)
                    except socket.timeout:
                        print("there was a socket timeout error in audio thread 4")  
                        print("exiting audio feed")
                        self.client_socket.close()
                        self.audio_capturer.close()
                        self._run_flag = False #does nothing
                        return
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
        print("exiting audio feed")
        self.client_socket.close()
        self.audio_capturer.close()

    def stop(self):
        print("stopping client")
        self._run_flag = False

