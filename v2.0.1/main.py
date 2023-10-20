# VERSION: 2.0.1
# added basic network manager and some other nicities

import sys

from PyQt5 import QtGui
from ssh_connect import SSHServer
from Connection_Status import Connection_Status
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QPushButton,
    QWidget,
    QLabel,
    QPlainTextEdit,
    QComboBox,
    QMessageBox
)
from PyQt5.QtCore import pyqtSlot, Qt, QThread
from PyQt5.QtGui import QPixmap
import sys
import cv2
import numpy as np

from yolo_video_client import VideoClient
from yoho_audio_client import AudioClient
from network_mgr.ping_it import NetworkManager

class Window(QWidget):
    def make_image_tile(self, hostname, row, col, id):
        row = row*2
        self.image_labels.append(QLabel(self))
        self.image_labels[-1].resize(self.cam_width, self.cam_height)


        self.txtHosts.append(QPlainTextEdit())
        self.txtHosts[-1].setFixedHeight(25)
        self.txtHosts[-1].appendPlainText(hostname)

        self.comboOptions.append(QComboBox())
        self.comboOptions[-1].addItem("Reboot PI")
        self.comboOptions[-1].activated.connect(lambda: self.rebootPI(hostname))





        '''
        0  0
        1  3
        2  6
        3  9
        '''
        self.outer_right_layout.addWidget(self.txtHosts[-1], row, col*3, 1,1, alignment=Qt.AlignTop)
        self.up_status_labels.append(QLabel(self))
        self.up_status_labels[-1].setText("DOWN")
        self.network_mgrs.append(NetworkManager(self.txtHosts[-1]))
        self.network_mgrs[-1].change_pixmap_signal.connect(lambda x: self.update_network_status(x, id))


        self.outer_right_layout.addWidget(self.up_status_labels[-1], row, col*3+1, 1, 1, alignment=Qt.AlignTop)        
        self.outer_right_layout.addWidget(self.comboOptions[-1], row, col*3+2, 1,1, alignment=Qt.AlignTop)

        self.outer_right_layout.addWidget(self.image_labels[-1], row, col*3, 1,3)
        self.video_threads.append(VideoClient(self.image_labels[-1], self.logWidget))
        self.video_threads[-1].change_pixmap_signal.connect(lambda x: self.update_image(x, id))
        self.video_threads[-1].change_connect_btn_signal.connect(lambda x: self.toggle_connect_txt(x, id))

        self.audio_threads.append(AudioClient(self.image_labels[-1]))
        self.audio_threads[-1].change_connect_btn_signal.connect(lambda x: self.toggle_connect_txt(x, id))

        self.btnConnects.append(QPushButton("Connect"))
        self.btnConnects[-1].clicked.connect(lambda: self.toggle_video_audio_connect_event(id))
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
        self.video_threads = []
        self.audio_threads = []
        self.btnConnects = []
        self.btn_toggle_predictions = []
        self.btnRecords = []
        self.txtHosts = []
        self.comboOptions = []
        self.up_status_labels = []
        self.logWidget = QPlainTextEdit()
        self.network_mgrs = []

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


        self.make_image_tile('raspberrypi13', 0, 0, 0)
        self.make_image_tile('raspberrypi2', 0, 1, 1)
        self.make_image_tile('raspberrypi3', 0, 2, 2)
        self.make_image_tile('raspberrypi4', 1, 0, 3)
        self.make_image_tile('raspberrypi5', 1, 1, 4)
        self.make_image_tile('raspberrypi6', 1, 2, 5)
        self.make_image_tile('raspberrypi7', 2, 0, 6)
        self.make_image_tile('raspberrypi8', 2, 1, 7)
        self.make_image_tile('raspberrypi9', 2, 2, 8)

        for net_mgr in self.network_mgrs:
            net_mgr.start()  

            

        self.btnMasterRecord = QPushButton("Record")
        self.btnMasterRecord.clicked.connect(lambda: self.record_events())
        
        self.outer_left_layout.addWidget(self.btnMasterRecord, 0, 0)


        self.logWidget.setReadOnly(True)
        self.outer_left_layout.addWidget(self.logWidget, 1, 0)
       


        # Set the layout on the application's window
        self.outer_layout.addLayout(self.outer_left_layout,0,0)
        self.outer_layout.addLayout(self.outer_right_layout,0,1)
        self.setLayout(self.outer_layout)

    def rebootPI(self, host):
        #create msgbox
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Are you sure you would like to reboot the pi?")
        msgBox.setWindowTitle("Reboot")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #msgBox.buttonClicked.connect(msgButtonClick)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Ok:
            print('Rebooting PI')
            ssh = SSHServer()
            ssh.start(host, 'drone', 'drones')
            ssh.reboot()        
        else:
            print('action cancelled')



    

    def toggle_predictions(self, idx):
        if(self.video_threads[idx].predicting == True):
            self.btn_toggle_predictions[idx].setText("Predict")
            self.btn_toggle_predictions[idx].setStyleSheet("background-color : light gray")
        else:
            self.btn_toggle_predictions[idx].setText("Predicting")
            self.btn_toggle_predictions[idx].setStyleSheet("background-color : green")
        self.video_threads[idx].toggle_predictions()
        #self.audio_threads[window].toggle_predictions()

    
    def toggle_video_audio_connect_event(self, idx):
            #if we are already connected and running, we need to disconnect and change the text back to "Connect"
            if(self.video_threads[idx]._run_flag == True):
                self.video_threads[idx]._run_flag = False
                self.audio_threads[idx]._run_flag = False
                self.btnConnects[idx].setText("Connect")
                self.btnConnects[idx].setStyleSheet("background-color : light gray")            

            else:
                self.btnConnects[idx].setText("Connecting")
                self.btnConnects[idx].repaint()
                self.video_threads[idx].set_host(self.txtHosts[idx].toPlainText(), 8485)
                self.audio_threads[idx].set_host(self.txtHosts[idx].toPlainText(), 8486)
                #resp1 = self.video_threads[idx].connect(self.txtHosts[idx].toPlainText(), 8485)
                #resp2 = self.audio_threads[idx].connect(self.txtHosts[idx].toPlainText(), 8486)  
                self.video_threads[idx].start()  
                self.audio_threads[idx].start()


                





    def record_events(self):
        for idx, btn in enumerate(self.btnRecords):
            self.record_event(idx)

    def record_event(self, idx):
        status = self.video_threads[idx].record()
        if(self.btnRecords[idx].text() == "Record" and status == True):
            self.btnRecords[idx].setText("Recording")
            self.btnRecords[idx].setStyleSheet("background-color : red") 

        else:
            self.btnRecords[idx].setText("Record")
            self.btnRecords[idx].setStyleSheet("background-color : light gray") 

    @pyqtSlot(bool)
    def toggle_connect_txt(self, tgl, idx):
        if(not tgl):
            #self.audio_threads[idx].client_socket.close()
            self.audio_threads[idx].stop()
            self.video_threads[idx].stop()
            #self.video_threads[idx].client_socket.close()
            self.btnConnects[idx].setText("Connect")
            self.btnConnects[idx].setStyleSheet("background-color : light gray") 

        else:
            if(self.audio_threads[idx].up_status_flag == Connection_Status.PENDING or self.video_threads[idx].up_status_flag == Connection_Status.PENDING):
                print("waiting on either audio or video to finish connecting")
                return

            self.btnConnects[idx].setText("Connected")
            self.btnConnects[idx].setStyleSheet("background-color : green") 

    @pyqtSlot(bool)
    def update_network_status(self, is_up, idx):
         #is_up = subprocess.call(command) == 0
        if(is_up):
            self.up_status_labels[idx].setText('UP')
            self.up_status_labels[idx].setStyleSheet('background-color: green')
        else:
            if(idx == 0):
                print("we had a bad ping")
            self.up_status_labels[idx].setText('DOWN')
            self.up_status_labels[idx].setStyleSheet('background-color: red')
            if(self.network_mgrs[idx].bad_ping_count == 5):
                self.video_threads[idx]._run_flag = False
                self.audio_threads[idx]._run_flag = False
                self.network_mgrs[idx].reset()
                self.btnConnects[idx].setText("Connect")
                self.btnConnects[idx].setStyleSheet("background-color : light gray")            



    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img, idx):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_labels[idx].setPixmap(qt_img)

        update, log = self.video_threads[idx].populate_log()
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
        #for network_mgr in self.network_mgrs:
        print("Stopping network manager")
        self.network_mgr.stop()
        #pass

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())