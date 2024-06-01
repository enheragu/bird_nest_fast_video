#!/usr/bin/env python3
# encoding: utf-8

## ThreadVideoCapture from https://pyimagesearch.com/2017/02/06/faster-video-file-fps-with-cv2-videocapture-and-opencv/

from threading import Thread, Lock
import time
from queue import Queue

import cv2

from utils.log_utils import log

class ThreadVideoBase:
    def __init__(self, path, queueSize):
        self.video_path = path

        # initialize the queue used to store frames to write
        self.Q = Queue(maxsize=queueSize)
        self.stopped = False

        self.lock = Lock()

    def start(self):
        # start a thread to read frames from the file video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        time.sleep(0.5)
        return self

    def update(self):
        raise NotImplementedError(f"This method has to be reimplemented in child {type(self).__name__} class")

    def more(self):
        # return True if there are still frames in the queue
        return self.Q.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        with self.lock:
            self.stopped = True
    
    def isStopped(self):
        with self.lock:
            return self.stopped
        
    def release(self):
        self.stop()
        time.sleep(0.5)
        self.stream.release()

class ThreadVideoWriter(ThreadVideoBase):
    def __init__(self, path, format, fps, size, queueSize=100):
        super().__init__(path, queueSize)

        self.stream = cv2.VideoWriter(path, format, fps, size)

    
    def update(self):
        while True:
            if self.isStopped():
                return
            
            if not self.Q.empty():
                self.stream.write(self.Q.get())

    def write(self, frame):
        self.Q.put(frame)

class ThreadVideoCapture(ThreadVideoBase):
    def __init__(self, path, queueSize=100):
        super().__init__(path, queueSize)
        # initialize the file video stream along with the boolean
        # used to indicate if the thread should be stopped or not
        self.stream = cv2.VideoCapture(path)

        if not self.stream.isOpened():
            log(f"Error opening video {path}")
            return

    def update(self):
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.isStopped():
                return
            
            # otherwise, ensure the queue has room in it
            if not self.Q.full():
                # read the next frame from the file
                (grabbed, frame) = self.stream.read()
                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
                if not grabbed:
                    self.stop()
                    return
                # add the frame to the queue
                self.Q.put(frame)
                            
    def read(self):
        # return next frame in the queue
        while self.Q.empty() and not self.isStopped():
            time.sleep(0.5)
        return self.Q.get()
