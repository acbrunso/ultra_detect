from threading import Thread
import cv2

class VideoGet:
    """
    Class that continuously gets frames from a VideoCapture object
    with a dedicated thread.
    """

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.isOpened = self.stream.isOpened()
        self.message = ""
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def getMessage(self):
        return self.message
    
    def start(self):    
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        if(self.isOpened == False):
            print("unable to locate camera")
            self.message = "Unable to locate camera. Perhaps it needs to be reconnected"
            self.stop()
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def stop(self):
        self.stopped = True
        print("releasing")
        self.stream.release()