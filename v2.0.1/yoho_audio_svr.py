

# VERSION: 2.0.1
# added basic network manager and some other nicities


import argparse

import socketserver
import struct

import struct
import gc

from AudioCapturer import AudioCapturer


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """




    def handle_resp(self, data):
        if(data == b'aa'):
            print('button clicked')
            return b'aa'
        elif(data == b'ab'):
            print('second button clicked')
            return b'ab'
        else:
            return b'00'
            
    def handle(self):
            
        data = b''
        r = b''

        audio_capturer = AudioCapturer()
        audio_capturer.open(True, False)
        audio_capturer.start()
        while True:
            if(audio_capturer.stopped):
                audio_capturer.close()
                break

            frame = audio_capturer.frame
            extra_data = b''

          
            data = frame 
            size = len(data)
            #print(size)
            extra_data_size = len(extra_data)
            try:
                self.request.sendall(struct.pack(">L", size) + data + struct.pack(">L", extra_data_size) + extra_data)
                r = self.handle_resp(self.request.recv(2).strip())
            except (ConnectionResetError, BrokenPipeError):
                audio_capturer.close()
                break
        print('leaving yoho_audio_server and waiting for next connection')
        del audio_capturer
        gc.collect()
            

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
        #serving the audio server forever causes segfaults in portaudio. so we have to disconnect the whole server, and
        #reconnect it each time. Dumb, but that's the only way I'm able to get it to work. Clearly, there are some garbage
        #collection issues with python.  The segfault happens on the pyaudio.PyAudio() call in AudioCapturer.py.
        server.handle_request()
        #server.serve_forever()
        
