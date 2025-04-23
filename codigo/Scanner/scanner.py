from capture import Capturer
import cv2 as cv
import time

class Scanner:
    def __init__(self, windowName, delay, activateDelay):
        self.capturer = Capturer(windowName, delay, activateDelay)
    
    def startScanner(self):
        while True:
            capture = self.capturer.captureIMG()
            cv.imshow("screen", capture)
            cv.waitKey(1)


scan = Scanner("Galaga ", 0.01, True)
scan.startScanner()