

# VERSION: 1.2.1
#implrement threading

import sys
import socket
import struct ## new
import pickle

from PyQt5 import QtGui

from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QPushButton,
    QWidget,
    QLabel,
    QPlainTextEdit
)
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtGui import QPixmap
import sys
import cv2
import numpy as np

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, image_label, host = "", port = ""):
        super().__init__()
        self.return_val = b'00'
        self.host = host
        self.port = port
        self.results = None
        self.image_label = image_label
        self.record_it = False
        self.fps = 20.0
        self._run_flag = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def setHost(self, host, port):
        self.stop()
        self.host = host
        self.port = port

    def run(self):
        print('run it')
        if(self.host == "" or self.port == ""):
            print("no value, returning")
            return
        print("connecting")
        print(self.host)
        print(self.port)
        self.client_socket.settimeout(5)

        try:
            self.client_socket.connect((self.host, self.port))
        except:
            print("failed to connect")
            return

        extra_data = b''
        payload_size = struct.calcsize(">L")
        print("payload size: " + str(payload_size))
        self._run_flag = True

        while self._run_flag:
            data = b''

            while len(data) < payload_size:
                data += self.client_socket.recv(payload_size)
                if not data:
                    cv2.destroyAllWindows()
                    continue
            
            # receive image row data form client socket
            packed_msg_size = data[:payload_size]               #grab the length of the frame that was sent
            msg_size = struct.unpack(">L", packed_msg_size)[0]  #unpack the length of the frame so it is readable
            data = b''
            while len(data) < msg_size:
                if(msg_size - len(data) < 4096):
                    data += self.client_socket.recv(msg_size - len(data))                #this will grab to the end of the frame.  still need to grab to the end of the data
                else:
                    data += self.client_socket.recv(4096)
            frame_data = data[:msg_size]                        #this is the frame data
            

            packed_extra_data_size = self.client_socket.recv(4)
            
            extra_data_size = struct.unpack(">L", packed_extra_data_size)[0]
            packed_extra_data = b''
            self.results = None
            if(extra_data_size > 0):
                while(len(packed_extra_data) < extra_data_size):
                    if(extra_data_size - len(packed_extra_data) < 4096):
                        packed_extra_data += self.client_socket.recv(extra_data_size - len(packed_extra_data))
                    else:
                        packed_extra_data += self.client_socket.recv(4096)
                extra_data = pickle.loads(packed_extra_data, fix_imports=True, encoding='bytes')
                self.results = extra_data

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
            for result in self.results:
                for box in result.boxes:
                    resp+=result.names[int(box.cls[0])] + '\n'
            if(resp.replace('\n','') == ''):
                return False, ''
            return True, resp

        return False, resp
        

    def toggle_predictions(self):
        self.return_val = b'aa'

        


    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        print("stopping client")
        self._run_flag = False
        self.wait()

class Window(QWidget):
    def make_image_tile(self, hostname, row, col, id):
        row = row*2
        self.image_labels.append(QLabel(self))
        self.image_labels[-1].resize(self.cam_width, self.cam_height)

        self.txtHosts.append(QPlainTextEdit())
        self.txtHosts[-1].setFixedHeight(25)
        self.txtHosts[-1].appendPlainText(hostname)

        '''
        0  0
        1  3
        2  6
        3  9
        '''
        self.outer_right_layout.addWidget(self.txtHosts[-1], row, col*3, 1,3, alignment=Qt.AlignTop)

        self.outer_right_layout.addWidget(self.image_labels[-1], row, col*3, 1,3)
        self.threads.append(VideoThread(self.image_labels[-1]))
        self.threads[-1].change_pixmap_signal.connect(lambda x: self.update_image(x, id))


        self.btnConnects.append(QPushButton("Connect"))
        self.btnConnects[-1].clicked.connect(lambda: self.open_event(id))
        self.outer_right_layout.addWidget(self.btnConnects[-1], row+1, col*3)

        '''
        0  ->  0
        1  ->  2
        2  ->  4
        3  ->  6
        4  ->  8
        '''

        self.btnRecords.append(QPushButton("Record"))
        self.btnRecords[-1].clicked.connect(lambda: self.record_event(id))
        self.outer_right_layout.addWidget(self.btnRecords[-1], row+1, col*3+1)
        '''
        0 -> 1    0*3+1
        1 -> 4    1*3+1
        2 -> 7    2*3+1
        3 -> 10   3*3+1
        4 -> 13
        '''

        self.btn_toggle_predictions.append(QPushButton(self))
        self.btn_toggle_predictions[-1].setText("Predict")
        self.btn_toggle_predictions[-1].clicked.connect(lambda: self.toggle_predictions(id))
        self.outer_right_layout.addWidget(self.btn_toggle_predictions[-1],row+1, col*3+2)
        '''
        0 -> 2    0*3+1
        1 -> 5    1*3+1
        2 -> 8    2*3+1
        3 -> 11   3*3+1
        4 -> 14
        '''


    def __init__(self):
        super().__init__()
        self.tile_count = 0
        self.cam_width = 320
        self.cam_height = 240
        self.threads = []
        self.btnConnects = []
        self.btn_toggle_predictions = []
        self.btnRecords = []
        self.txtHosts = []
        self.setWindowTitle("Drone Detection Command Center")
        # Create a QGridLayout instance
        self.image_labels = []



        self.outer_layout = QGridLayout()
        self.outer_left_layout = QGridLayout()
        self.outer_right_layout = QGridLayout()

        for i in range(6):
            self.outer_right_layout.setColumnMinimumWidth(i, int(self.cam_width/3))
        

        self.outer_right_layout.setRowMinimumHeight(0, self.cam_height)
        self.outer_right_layout.setRowMinimumHeight(2, self.cam_height)
        self.outer_right_layout.setRowMinimumHeight(4, self.cam_height)


        self.make_image_tile('raspberrypi1', 0, 0, 0)
        self.make_image_tile('raspberrypi2', 0, 1, 1)
        self.make_image_tile('raspberrypi3', 0, 2, 2)
        self.make_image_tile('raspberrypi4', 1, 0, 3)
        self.make_image_tile('raspberrypi5', 1, 1, 4)
        self.make_image_tile('raspberrypi6', 1, 2, 5)
        self.make_image_tile('raspberrypi7', 2, 0, 6)
        self.make_image_tile('raspberrypi8', 2, 1, 7)
        self.make_image_tile('raspberrypi9', 2, 2, 8)

        self.btnMasterRecord = QPushButton("Record")
        self.btnMasterRecord.clicked.connect(lambda: self.record_events())
        
        self.outer_left_layout.addWidget(self.btnMasterRecord, 0, 0)


        self.logWidget = QPlainTextEdit()
        self.logWidget.setReadOnly(True)
        self.outer_left_layout.addWidget(self.logWidget, 1, 0)
       


        # Set the layout on the application's window
        self.outer_layout.addLayout(self.outer_left_layout,0,0)
        self.outer_layout.addLayout(self.outer_right_layout,0,1)
        self.setLayout(self.outer_layout)

    def toggle_predictions(self, window):
        self.threads[window].toggle_predictions()

    def open_event(self, idx):
         # create the video capture thread
        #self.threads.append(VideoThread(host, port))
        # connect its signal to the update_image slot
        # start the thread
        self.threads[idx].setHost(self.txtHosts[idx].toPlainText(), 8485)
        self.threads[idx].start()

    def record_events(self):
        for idx, btn in enumerate(self.btnRecords):
            self.record_event(idx)

    def record_event(self, idx):
        status = self.threads[idx].record()
        if(self.btnRecords[idx].text() == "Record" and status == True):
            self.btnRecords[idx].setText("Recording")
            self.btnRecords[idx].setStyleSheet("background-color : red") 

        else:
            self.btnRecords[idx].setText("Record")
            self.btnRecords[idx].setStyleSheet("background-color : light gray") 


    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img, idx):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_labels[idx].setPixmap(qt_img)

        update, log = self.threads[idx].populate_log()
        if(update):
            self.logWidget.appendPlainText(log)
            
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.cam_width, self.cam_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
    def closeEvent(self, event):
        #for thd in self.threads:
        #    thd.shutdown()
        pass
        #print("closing w1")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())