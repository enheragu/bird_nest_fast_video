#!/usr/bin/env python3
# encoding: utf-8

"""
    Find specific time intervals for fast/slow execution and then extract specific frames to use for each video
"""

import math
from multiprocessing import Pool

import time
from datetime import timedelta

from utils.yaml_utils import parseYaml, dumpYaml
from utils.log_utils import log

"""
    Computes time intervals for a given entry
"""
def updateIntervals(args):
    video_input, data_dict, before_seconds, after_seconds = args

    intervals = []
    timestamps = data_dict['timestamps']
    if len(timestamps) > 1:
        for timestamp in timestamps[1:]: # Ignore the 0 added when background detector started
            start_interval = int(timestamp - before_seconds * data_dict['fps'])
            end_interval = int(timestamp + after_seconds * data_dict['fps'])
            intervals.append([start_interval, end_interval])

        # Ordenar los intervalos por el punto de inicio
        intervals.sort(key=lambda x: x[0])

        # Merge overlapping intervals:
        merged_intervals = [intervals[0]]
        for interval in intervals[1:]:
            if interval[0] <= merged_intervals[-1][1]:
                merged_intervals[-1] = [merged_intervals[-1][0], max(interval[1], merged_intervals[-1][1])]
            else:
                merged_intervals.append(interval)
    
    else:
        merged_intervals = [[math.inf, math.inf]]

    data_dict['merged_intervals'] = merged_intervals
    result_dict = {video_input: data_dict}
    
    return result_dict

"""
    Computes time interval based on movement detected timetags. Intervals are stored in the same data dict and file
"""
def handleIntervals(timestamp_dict, max_workers, timestamps_cache_yaml, before_seconds, after_seconds):

    start = time.time()
    with Pool(max_workers) as pool:
        args_list = [(video, data_dict, before_seconds, after_seconds) for video, data_dict in timestamp_dict.items()]
        results = pool.map(updateIntervals, args_list)

        for result in results:
            timestamp_dict.update(result)
    
    dumpYaml(timestamps_cache_yaml, timestamp_dict, 'w')
    
    log(f"Handled frame intervals for {len(timestamp_dict.keys())} videos, took {str(timedelta(seconds=time.time()-start))} (h:min:sec.mil).")
    return timestamp_dict



"""
    Handles frames taking into account general frame count but adds local frame inedx for each video to be later concatenated
"""
def handleFrames(timestamp_dict, frames_cache_yaml, new_fps, acceleration_factor_slow, acceleration_factor_fast):
    
    start = time.time()

    frames_dict = {}
    
    frame_count_general = 0
    for video, data_dict in timestamp_dict.items():
        merged_intervals = data_dict['merged_intervals']
        fps = data_dict['fps']

        frames = []
        
        timestamp_index = 0
        interval = merged_intervals[timestamp_index]
        
        for frame_count in range(data_dict['total_frames']):

            in_interval = False
            
            if frame_count >= interval[0] and frame_count <= interval[1]:
                in_interval = True
            elif frame_count > interval[1]:
                timestamp_index = min(timestamp_index+1, len(merged_intervals)-1)
                interval = merged_intervals[timestamp_index]

            if not in_interval:
                # log(f"[{frame_count}] not in_interval")
                if frame_count_general % int(acceleration_factor_fast*fps/new_fps) == 0:
                    frames.append(['f', frame_count])

            elif in_interval:
                if frame_count_general % int(acceleration_factor_slow*fps/new_fps) == 0:
                    frames.append(['s', frame_count])   
            
            frame_count_general+=1

        frames_dict[video] = frames

    dumpYaml(frames_cache_yaml, frames_dict, 'w')
    
    log(f"Handled frames for {len(timestamp_dict.keys())} videos, took {str(timedelta(seconds=time.time()-start))} (h:min:sec.mil).")
    return frames_dict