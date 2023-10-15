import paramiko
import time
class SSHServer:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def start(self, host, username, password):
        self.ssh.connect(host, username=username, password=password)
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('python /home/drone/Desktop/ultra_detect/v1.2.2/yolo_stream_svr.py -p 8485')
        #print(ssh_stdin.read().decode())
        #time.sleep(5)
        #print(ssh_stdout.read().decode())
        self.ssh.close()

        #print(ssh_stderr.read().decode())
    def stop(self):
        self.ssh.close()