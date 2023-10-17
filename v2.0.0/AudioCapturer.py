from threading import Thread
import pyaudio
import gc

#filename = './ultra_detect/v1.3/mpro_horizontal_rasp10_p2.wav'

# Set chunk size of 1024 samples per data frame
RESPEAKER_RATE = 16000
RESPEAKER_INDEX = 1
RESPEAKER_WIDTH = 2
RESPEAKER_CHANNELS = 1
CHUNK = 4096

# Open the sound file 
#wf = wave.open(filename, 'rb')
class AudioCapturer:

    def __init__(self):
        # Create an interface to PortAudio
        print("\niniting audio Capturer")
        self.frame = b''
        self.stopped = False
        self.test = "bbb"


    def open(self, input, output):
        print("initing pyAudio")
        self.p = pyaudio.PyAudio()
        print('inited pyaudio')
        self.stream = self.p.open(format = self.p.get_format_from_width(RESPEAKER_WIDTH),
                channels = RESPEAKER_CHANNELS,
                rate = RESPEAKER_RATE,
                input = input, # 'input = True' indicates that the sound will be captured
                output = output, # 'output = True' indicates that the sound will be played
                input_device_index=RESPEAKER_INDEX,)
        print("opened pyaudio")

    def start(self):
        Thread(target=self.read, args=()).start()

    def read(self):
        while not self.stopped:
            try:
                self.frame = self.stream.read(CHUNK)
            except:
                #print("no frame read from audio source")
                self.test = "aaa"
                self.stopped = True
                #self.close()
        print("audio read just stopped. thread closing")
            

    
    def write(self, data):
        return self.stream.write(data)

    def close(self):
        print('closing audio capture')
        print(self.test)
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        #del self.p
        #gc.collect()


