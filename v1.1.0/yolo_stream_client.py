


# VERSION 1.1.0

from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton

from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
import socket
import struct ## new
import pickle


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.return_val = b'00'

    def run(self):
        HOST='raspberrypi16'
        PORT=8485


        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]

        data = b''
        payload_size = struct.calcsize(">L")
        while self._run_flag:
            while len(data) < payload_size:
                data += client_socket.recv(4096)
                if not data:
                    cv2.destroyAllWindows()
                    #conn,addr=s.accept()
                    continue
            # receive image row data form client socket
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            while len(data) < msg_size:
                data += client_socket.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            # unpack image using pickle 
            frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            self.change_pixmap_signal.emit(frame)
            client_socket.sendall(self.return_val)
            self.return_val = b'00'
            #cv2.imshow('client',frame)
            cv2.waitKey(1)



    def toggle_predictions(self):
        self.return_val = b'aa'

        

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Detection Command Center")
        self.disply_width = 640
        self.display_height = 480
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
        # create a text label
        self.textLabel = QLabel('Webcam')

        self.button1 = QPushButton(self)
        self.button1.setText("Connect")
        self.button1.clicked.connect(self.open_event)

        self.button2 = QPushButton(self)
        self.button2.setText("Close Stream")
        self.button2.clicked.connect(self.closeEvent)

        self.btn_toggle_predictions = QPushButton(self)
        self.btn_toggle_predictions.setText("Toggle Predictions")
        self.btn_toggle_predictions.clicked.connect(self.toggle_predictions)


        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.textLabel)
        vbox.addWidget(self.button1)
        vbox.addWidget(self.button2)
        vbox.addWidget(self.btn_toggle_predictions)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

       

    def toggle_predictions(self, event):
        self.thread.toggle_predictions()

    def open_event(self, event):
         # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        #event.accept()



    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())