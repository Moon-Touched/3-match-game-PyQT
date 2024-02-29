import cv2
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal

class GameStateMachine(QObject):
    refill_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.state = "Init"
        self.refill_done.connect(self.on_refill_done)

        


