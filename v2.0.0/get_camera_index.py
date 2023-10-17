import cv2
for i in range(10):
    cap = cv2.VideoCapture(i) 
    if(cap.isOpened()):
          print(str(i) + " is open")
          cap.release() 
    else:
          print(str(i) + " is NOT open")

    
