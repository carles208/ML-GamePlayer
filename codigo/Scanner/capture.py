import pygetwindow as gw
import pyautogui
import cv2
import numpy as np

class Capturer:
    def __init__(self, name, delay, activateDelay):
        self.windowName = name
        self.delay = delay
        self.activateDelay = activateDelay
        self.captureBuffer = self.captureIMG()

    def captureIMG(self):
        windows = gw.getWindowsWithTitle(self.windowName)
        window = windows[0]

        if(window.isMinimized):
            window.restore()
        
        window.activate()
        if self.activateDelay:
            pyautogui.sleep(self.delay)
        screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))

        self.captureBuffer = screenshot

        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def setDelay(self, newDelay):
        self.delay = newDelay
    
    def toggleDelay(self, opt):
        self.activateDelay = opt

    def setWindow(self, windowName):
        self.windowName = windowName