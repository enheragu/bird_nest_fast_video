#!/usr/bin/env python3
# encoding: utf-8

import threading 

class ThreadSafeCounter:
    def __init__(self, value = 0, max = None):
        self.lock = threading.Lock()
        self.value = 0
        self.max = max

    def increment(self):
        with self.lock:
            self.value += 1

    def get_value(self):
        with self.lock:
            return self.value

    def __str__(self):
        with self.lock:
            if self.max:
                return f'{self.value}/{self.max}'
            else:
                return f'{self.value}'

    def __iadd__(self, other):
        with self.lock:
            self.value += other
            return self

    def __int__(self):
        with self.lock:
            return self.value

    def __get__(self, instance, owner):
        with self.lock:
            return int(self)