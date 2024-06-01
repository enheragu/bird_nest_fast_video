#!/usr/bin/env python3
# encoding: utf-8

"""
    All the code involved in finding movement timetags in all requested videos
"""

import os
from multiprocessing import Pool
from more_itertools import chunked

import time
from datetime import timedelta
import math
import cv2
import numpy as np

from utils.log_utils import logCoolMessage, log, bcolors
from utils.yaml_utils import parseYaml, dumpYaml
from utils.ThreadVideoStream import ThreadVideoCapture, ThreadVideoWriter

def_debug_mask = False
def_frame_skip = 5
"""
    Scale speed of video based on detected movement in the image
    frame_skip: do not process all frames to go a bit faster
    threshold: threshold for motion detector
    
"""
def process_video(input_path, threshold=4):

    start = time.time()
    cap = ThreadVideoCapture(input_path)
        
    fps = cap.stream.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.stream.get(cv2.CAP_PROP_FRAME_COUNT))
    
    log(f"- Processing {input_path}: {round(fps)} FPS")
    
    segment_size = math.ceil(total_frames / os.cpu_count())  # Number of frames per segment
    segment_size = total_frames
    args = [(max(start_frame - 5, 0), min(start_frame + segment_size + 5, total_frames - 1), input_path, threshold, cap) for start_frame in range(0, total_frames, segment_size)]
    
    timestamps = []
    for arg in args:
        timestamps.extend(process_segment(arg))

    timestamp_dict = {input_path: {'timestamps':sorted(timestamps), 'fps':round(fps), 'frames':total_frames}}
    # log(f"Timestamps: {timestamp_dict}")
    
    log(f"  Finished timestamp extraction for {input_path}, took {str(timedelta(seconds=time.time()-start))} (h:min:sec.mil).")
    return timestamp_dict

def process_segment(args):
    global frame_skip
    start_frame, end_frame, input_path, threshold, cap = args
    timestamps = []
    
    cap.stream.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_width = int(cap.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.start() # Start frame aquisition once all set/get operations are done

    motion_detected = False
    
    # fgbg = cv2.createBackgroundSubtractorKNN(history=300, detectShadows=False)
    fgbg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=False)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)) 

    for frame_count in range(start_frame, end_frame + 1):
        frame = cap.read()
                
        if frame_count % frame_skip == 0:
            # Just removes parts of image that has no motion (wall and ceil)
            x0,y0 = 0,0
            x1,y1 = 680,230
            frame = frame[y1:frame_height-100, x1:frame_width-150]
            roi_width, roi_height, _ = frame.shape
            # Reduce resolution to make background processing faster
            frame = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA)

            motion_mask = fgbg.apply(frame)
            # motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)   
            motion_mask = cv2.erode(motion_mask,kernel,iterations=2)
            motion_mask = cv2.dilate(motion_mask,kernel,iterations=2)

            motion = np.sum(motion_mask) > threshold

            if motion > 0:
                # if not motion_detected:
                motion_detected = True
                timestamps.append(frame_count)
                color = (0,255,0)
            else:
                motion_detected = False
                color = (0,0,255)

            if def_debug_mask and motion_detected:
                ff_mask = motion_mask
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale = 2
                thickness = 2
                cv2.putText(ff_mask, f'frame: {frame_count} ({motion_detected})', (15, 65), fontFace=font, fontScale=scale, color=color, thickness=thickness)
                cv2.imshow('motion_mask', ff_mask) 
                
                ff_orig = frame
                cv2.putText(ff_orig, f'frame: {frame_count} ({motion_detected})', (15, 65), fontFace=font, fontScale=scale, color=color, thickness=thickness)
                cv2.imshow('original_video', ff_orig)
                
                k = cv2.pollKey()
                if k == ord('q') or k == ord('Q') or k == 27:
                    return timestamps
            
            
    cap.release()
    return timestamps

def handleTimetags(video_files, timestamps_cache_yaml, max_workers, debug_mask, frame_skip, timestamp_videos_black_list = []):
    global def_debug_mask, def_frame_skip
    start = time.time()

    def_debug_mask = debug_mask 
    def_frame_skip = frame_skip

    logCoolMessage('Extract timestamps from videofiles')
    timestamp_dict = {}
    if os.path.exists(timestamps_cache_yaml):
        log(f"File {timestamps_cache_yaml} already exists, parse data from it.")
        timestamp_dict = parseYaml(timestamps_cache_yaml)
        log(f"A total of {len(timestamp_dict.keys())} timetagged videos parsed.", bcolors.OKCYAN)

    # Ignored blacklist and set to be accelerated at full speed :)
    for file in video_files:
        ignore = False
        for pattern in timestamp_videos_black_list:
            if pattern in file and file not in list(timestamp_dict.keys()):
                stream = cv2.VideoCapture(file)
                fps = stream.get(cv2.CAP_PROP_FPS)
                total_frames = int(stream.get(cv2.CAP_PROP_FRAME_COUNT))
                stream.release()
                timestamp_dict[file] = {'timestamps': [0], 'fps': round(fps), 'total_frames': total_frames}

    # Recompute those that are missing
    video_files = [i for i in video_files if i not in timestamp_dict.keys()]
    
    log(f"Timestamps from {len(video_files)} videos that need update.", bcolors.OKCYAN)#: {[file.split('/')[-4:] for file in video_files]}")
    
    ## Ensure it stores computed data from time to time to avoid...issues...
    slice_size = max_workers*3 if max_workers*3 < len(video_files) else len(video_files)
    processed = 0
    for video_slice in chunked(video_files, slice_size):
        with Pool(max_workers) as pool:
            results = pool.map(process_video, video_slice)

            for result in results:
                timestamp_dict.update(result)

        # pbar.update(slice_size)
        processed += slice_size
        log(f"Partial save: processed {processed}/{len(video_files)} videos.", bcolors.OKCYAN)
        dumpYaml(timestamps_cache_yaml, timestamp_dict, 'w')
    
    log(f"Handled timetags for {len(timestamp_dict.keys())} videos, took {str(timedelta(seconds=time.time()-start))} (h:min:sec.mil).")
    return timestamp_dict