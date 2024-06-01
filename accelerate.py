#!/usr/bin/env python3
# encoding: utf-8

"""
    Given a set of frames for each video generates new videos with that data
"""

import os
import cv2

import time
from datetime import timedelta

from utils.ThreadVideoStream import ThreadVideoCapture, ThreadVideoWriter

from utils.log_utils import log, bcolors, logCoolMessage
from utils.yaml_utils import parseYaml, dumpYaml

# def accelerate_video(input_video_path, output_video_path, timestamps, acceleration_factor_slow, acceleration_factor_fast, before_seconds=10, after_seconds=10):
#     global new_fps

#     start = time.time()
#     log(f"- Accelerating output {output_video_path}")
#     cap = ThreadVideoCapture(input_video_path)
    
#     fps = cap.stream.get(cv2.CAP_PROP_FPS)
#     total_frames = int(cap.stream.get(cv2.CAP_PROP_FRAME_COUNT))
#     frame_width = int(cap.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
#     frame_height = int(cap.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     cap.start() # Start frame aquisition once all set/get operations are done
    
#     out = ThreadVideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), new_fps, (frame_width, frame_height))
#     out.start()

#     font = cv2.FONT_HERSHEY_SIMPLEX
#     scale = 1
#     thickness = 2
#     text_size, _ = cv2.getTextSize(f'>>x{acceleration_factor_fast}', font, scale, thickness)
#     text_width, text_height = text_size
#     x = frame_width - text_width - 10  # 10 pixel margin
#     y = text_height + 10  # 10 pixel margin
    
#     intervals = []
#     if len(timestamps) > 1:
#         for timestamp in timestamps[1:]: # Ignore the 0 added when background detector started
#             start_interval = int(timestamp - before_seconds * new_fps)
#             end_interval = int(timestamp + after_seconds * new_fps)
#             intervals.append((start_interval, end_interval))

#         # Ordenar los intervalos por el punto de inicio
#         intervals.sort(key=lambda x: x[0])

#         # Merge overlapping intervals:
#         merged_intervals = [intervals[0]]
#         for interval in intervals[1:]:
#             if interval[0] <= merged_intervals[-1][1]:
#                 merged_intervals[-1] = (merged_intervals[-1][0], max(interval[1], merged_intervals[-1][1]))
#             else:
#                 merged_intervals.append(interval)
    
#     else:
#         merged_intervals = [[math.inf, math.inf]]
        
#     # log(f"Non-Overlapping Intervals: {merged_intervals}")
#     timestamp_index = 0
#     interval = merged_intervals[timestamp_index]
#     for frame_count in range(total_frames):
#         frame = cap.read()

#         in_interval = False
        
#         if frame_count >= interval[0] and frame_count <= interval[1]:
#             in_interval = True
#         elif frame_count > interval[1]:
#             timestamp_index = min(timestamp_index+1, len(merged_intervals)-1)
#             interval = merged_intervals[timestamp_index]
            
#         if not in_interval:
#             # log(f"[{frame_count}] not in_interval")
#             if frame_count % int(acceleration_factor_fast*new_fps/fps) == 0:
#                 cv2.putText(frame, f'>>x{acceleration_factor_fast}', (x, y), font, scale, (0,0,255), thickness)
#                 out.write(frame)

#         elif in_interval:
#             if frame_count % int(acceleration_factor_slow*new_fps/fps) == 0:
#                 cv2.putText(frame, f'>>x{acceleration_factor_slow}', (x, y), font, scale, (0,255,0), thickness)
#                 out.write(frame)
    
#     # Liberar recursos
#     cap.release()
#     out.release()

#     log(f"  Finished {output_video_path}, took {str(timedelta(seconds=time.time()-start))} (h:min:sec.mil).")


def handleAcceleration(frames_dict, output_video_name, new_fps, acceleration_factor_fast, acceleration_factor_slow):
    start = time.time()


    cap = cv2.VideoCapture(list(frames_dict.keys())[0])
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()


    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1
    thickness = 2
    text_size, _ = cv2.getTextSize(f'>>x{acceleration_factor_fast}', font, scale, thickness)
    text_width, text_height = text_size
    x = frame_width - text_width - 10  # 10 pixel margin
    y = text_height + 10  # 10 pixel margin


    out = ThreadVideoWriter(output_video_name, cv2.VideoWriter_fourcc(*'mp4v'), new_fps, (frame_width, frame_height))
    out.start()
    for video, frames in frames_dict.items():
        if '17d' not in video and '18d' not in video and '19d' not in video:
            continue
        
        cap = cv2.VideoCapture(video)
        for frame_index in frames:
            cap.set(cv2.CAP_PROP_FRAME_COUNT, frame_index[1])
            ret, frame = cap.read()
            if not ret:
                log(f"Problem reading frame from {video}", bcolors.ERROR)
            
            if frame_index[0] == 'f':
                cv2.putText(frame, f'>>x{acceleration_factor_fast}', (x, y), font, scale, (0,0,255), thickness)
            elif frame_index[0] == 's':
                cv2.putText(frame, f'>>x{acceleration_factor_slow}', (x, y), font, scale, (0,255,0), thickness)

            out.write(frame)
    out.release()
    
    log(f"Accelerated video {output_video_name} videos, took {str(timedelta(seconds=time.time()-start))} (h:min:sec.mil).")
    