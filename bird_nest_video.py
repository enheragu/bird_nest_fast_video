#!/usr/bin/env python3
# encoding: utf-8

"""
    Process large files from security camera to filter and make a fast video version of
    birds makings its nest :)
"""

import os
import cv2
import numpy as np
import tqdm
from multiprocessing import Pool
import math
import yaml

import moviepy.editor as mp
import subprocess

import time
from datetime import timedelta

from utils.log_utils import log, bcolors, logCoolMessage
from utils.yaml_utils import parseYaml, dumpYaml
from utils.ThreadVideoStream import ThreadVideoCapture, ThreadVideoWriter

from find_videos import handleVideoSearch
from find_timetags import handleTimetags
from find_frames import handleIntervals, handleFrames
from accelerate import handleAcceleration


# Configuration of paths 
# input_video_path = '/run/user/1000/gvfs/smb-share:server=enheragu-server.local,share=eeha/cámara_terraza/202405'
input_video_path = './raw_videos/202405'
input_video_extension = '.mp4'
output_video_path = './processed_videos/'


# Night videos are ignored when extracting timetags. No movement :)
timestamp_videos_black_list = ['/23h/','/00h/','/01h/','/02h/','/03h/','/04h/','/05h/','/06h/']

# Max workers to use in multiprocessing
# Acceleration takes less memory so it can actually use more CPU cores
max_workers = os.cpu_count() - 1  # Use the number of CPU cores available
max_workers_accelerate = os.cpu_count() - 1


# Debug mask with window display showing results
debug_mask = False


# Options to configure output
frame_skip=8
acceleration_factor_slow=140
acceleration_factor_fast=4000
timelapse_acceleration_factor=12000
before_seconds=1
after_seconds=1


# Flags to activate/deactivate parts of SW
video_search = True
timestamp_search = True
acceleartion = True
concatenate = True


# Filenames for cach files
videofiles_cache_yaml = './cache/videofiles.chache.yaml' # File with all the videos that are to be included
timestamps_cache_yaml = './cache/timestams.chache.yaml'  # Timestamp info about videos to be accelerated
frames_cache_yaml = './cache/frames.chache.yaml'         # Specific frames to take once accelerated
frames_timelapse_cache_yaml = './cache/frames_timelapse.chache.yaml'         # Specific frames to take once accelerated in timelapse
ffmpeg_cache_file = './cache/ffmpeg_video_list.txt'      # Videos to be concatenated by ffmpeg
failed_ffmpg_videos = './cache/error_videos.cache.yaml'  # Video list that is not correct and is excluded from ffmpeg concatenation

# Output FPS
new_fps = 50



if __name__ == "__main__":
    log(f'Flag {video_search = }')
    log(f'Flag {timestamp_search = }')
    log(f'Flag {acceleartion = }')
    log(f'Flag {concatenate = }')

    if debug_mask:
        cv2.namedWindow("motion_mask", cv2.WINDOW_NORMAL) 
        cv2.resizeWindow('motion_mask', 900,700)

        cv2.namedWindow("original_video", cv2.WINDOW_NORMAL) 
        cv2.resizeWindow('original_video', 900,700)

        max_workers=1
        max_workers_accelerate=1


    ## CHECK FOR ALL VIDEO FILES AND GETS PATHS
    if video_search:
        video_files = handleVideoSearch(videofiles_cache_yaml, input_video_path, input_video_extension, max_workers)
    
    ## CHECKS ALL VIDEOS AND GETS TIMESTAMPS WITH MOVEMENT
    if timestamp_search:
        timestamp_dict = handleTimetags(video_files, timestamps_cache_yaml, max_workers, debug_mask, frame_skip, timestamp_videos_black_list)

    ## ACCELERATES EACH VIDEO BASED ON COMPUTED TIMESTAMPS
    if acceleartion:
        logCoolMessage('Video acceleration')
        timestamp_dict = handleIntervals(timestamp_dict, max_workers, timestamps_cache_yaml, before_seconds, after_seconds)
        frames_dict = handleFrames(timestamp_dict, frames_cache_yaml, new_fps, acceleration_factor_slow, acceleration_factor_fast)
        
        output_video_name = f'{output_video_path}/slow_x{acceleration_factor_slow}_fast_x{acceleration_factor_fast}_complete_video.mp4'
        handleAcceleration(frames_dict, output_video_name, new_fps, acceleration_factor_fast, acceleration_factor_slow)

        output_video_name = f'{output_video_path}/fast_x{timelapse_acceleration_factor}_timelapse.mp4'
        frames_dict_timelapse = handleFrames(timestamp_dict, frames_timelapse_cache_yaml, new_fps, timelapse_acceleration_factor, timelapse_acceleration_factor)
        handleAcceleration(frames_dict_timelapse, output_video_name, new_fps, timelapse_acceleration_factor, timelapse_acceleration_factor, include_slow = False)

    # ## CONCATENATE ALL RESULTING VIDEOS
    # if concatenate:
    #     output_video_name = f'{output_video_path}/slow{acceleration_factor_slow}_fast{acceleration_factor_fast}_complete_video.mp4'
    #     logCoolMessage('Video concatenation')
    #     video_list = sorted(search_videos((output_video_path, '_hd.mp4'), startswith=f'slow{acceleration_factor_slow}_fast{acceleration_factor_fast}_'))
        
    
    #     # Check that videos are correct!
    #     videos = []
    #     failed = []
    #     for video in video_list:
    #         try:
    #             mp.VideoFileClip(video)
    #             videos.append(video)
    #         except KeyError as e:
    #             failed.append(video)
    #             # log(f"KeyError::Exception for {video}, might be empty: {e}")
    #         except OSError as e: 
    #             failed.append(video)
    #             if 'MoviePy error' in str(e):
    #                 pass
    #                 # log(f"Moviepy::Exception for {video}, might be empty: {e}")
    #             else:
    #                 log(f"OSError::Exception for {video}, might be empty: {e}")
        
    #     dumpYaml(failed_ffmpg_videos, failed)

    #     # Ejecutar el comando FFmpeg
    #     # Escribir la lista de nombres de archivos de video en un archivo de texto
    #     with open(ffmpeg_cache_file, 'w') as f:
    #         for video in videos:
    #             f.write(f"file '{video}'\n")
    #     cmd_ffmpeg = ['ffmpeg', '-fflags', '+igndts', '-y', '-f', 'concat', '-safe', '0', '-i', f'{ffmpeg_cache_file}', '-c', 'copy', f'{output_video_name}']
    #     subprocess.run(cmd_ffmpeg)

    
    if debug_mask:
        cv2.destroyAllWindows()