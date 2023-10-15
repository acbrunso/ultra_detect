from threading import Thread
import cv2
from ultralytics import YOLO


class YOLOPredictor:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, results=None):
        self.results = results
        self.stopped = True
        self.model = YOLO('yolov8n.pt')
        self.frame = ""

    def start(self, frame):
        self.stopped = False
        print("starting predictor")
        #threading.Thread(target=test, args=(arg1,), kwargs={'arg2':arg2}).start()
        self.frame = frame
        Thread(target=self.predict, args=()).start()
        return self

    def predict(self):
        while not self.stopped:
            print("predicting")
            self.results = self.model(self.frame, imgsz=320, verbose=False)
            self.annotated_frame = self.results[0].plot()

    def stop(self):
        self.stopped = True