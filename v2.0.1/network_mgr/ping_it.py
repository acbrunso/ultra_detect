
from threading import Thread
import platform    # For getting the operating system name
import subprocess  # For executing a shell command
import time
from PyQt5.QtCore import pyqtSignal, QThread

class NetworkManager(QThread):
    change_pixmap_signal = pyqtSignal(bool)
    
    def __init__(self, txtHost):
        super().__init__()
        #self.change_pixmap_signal = pyqtSignal(bool)

        self._run_flag = False
        self.txtHost = txtHost
        self.bad_ping_count = 0

    def run(self): 

        self._run_flag = True
        while(self._run_flag == True):
            self.ping(self.txtHost)

    def ping(self, host):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        """
          #for idx, txtHost in enumerate(self.txtHosts):
              
            # Option for the number of packets as a function of
        param = '-n' if platform.system().lower()=='windows' else '-c'
        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param, '1', host.toPlainText()]

        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            #print(output)
        except subprocess.CalledProcessError as e:
            # Handle any errors or exceptions here
            #print("Command failed with error:", e)
            output = 'could not find'  # You can set output to a default value or handle errors differently

        is_up = True
        if 'could not find' in output:
            is_up = False
        if 'unreachable' in output:
            is_up = False

        if(is_up == False):
            self.bad_ping_count +=1
        else:
            self.reset()
        
        #up_status_label.repaint()
        self.change_pixmap_signal.emit(is_up)


       

    def reset(self):
        self.bad_ping_count = 0



    def stop(self):
        self._run_flag = False
        


