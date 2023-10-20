# VERSION: 2.0.1
# added basic network manager and some other nicities


import paramiko
import time
class SSHServer:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def runAudioServer(self):
        print('running ssh audio connect')
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('python /home/drone/Desktop/ultra_detect/v2.0.1/yoho_audio_svr.py -p 8486 &')
        msg = self.get_error(ssh_stderr)
        self.ssh.close()
        return msg


    def runVideoServer(self):
        print('running ssh video connect')
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('python /home/drone/Desktop/ultra_detect/v2.0.1/yolo_stream_svr.py -p 8485 &')
        msg = self.get_error(ssh_stderr)
        self.ssh.close()
        return msg


    def start(self, host, username, password):
        self.ssh.connect(host, username=username, password=password)
        #print(ssh_stderr.read().decode())

        #print(ssh_stdin.read().decode())
        #time.sleep(5)
        #print(ssh_stdout.read().decode())

        #print(ssh_stderr.read().decode())

    def stop(self):
        self.ssh.close()



    def reboot(self):
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('sudo reboot')


    def get_error(self, ret):
        timeout = 3
        endtime = time.time() + timeout
        while not ret.channel.eof_received:
            time.sleep(1)
            if time.time() > endtime:
                ret.channel.close()
                return 0
        return ret.read().decode()
