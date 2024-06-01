#!/usr/bin/env python3
# encoding: utf-8

"""
    All the code involved in finding requested videos and storing file with them
"""

import os
from multiprocessing import Pool

from utils.log_utils import logCoolMessage, log, bcolors
from utils.yaml_utils import parseYaml, dumpYaml

# First find all videos to be processed
def search_videos(args, startswith = ''):
    root, extension = args
    video_files = []
    for root, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(extension) and file.startswith(startswith):
                video_files.append(os.path.join(root, file))
    return video_files

def find_videos(directory, extension, max_workers):
    
    subdirectories = [os.path.join(directory, d) for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    args = [(subdir, extension) for subdir in subdirectories]

    video_files = []
    with Pool(max_workers) as pool:
        video_files = pool.map(search_videos, args)
        # for result in tqdm.tqdm(pool.imap_unordered(search_videos, args), total=len(args)):
        #     video_files.append(result)
          
    
    # Flatten the list of lists returned by pool.map
    video_files = [file for sublist in video_files for file in sublist]
    
    return video_files


def handleVideoSearch(videofiles_cache_yaml, input_video_path, input_video_extension):
    logCoolMessage('Search for all video files')
    video_files = []
    if os.path.exists(videofiles_cache_yaml):
        log(f"File {videofiles_cache_yaml} already exists, parse data from it.")
        video_files = parseYaml(videofiles_cache_yaml)
    else:
        log(f"Search video files in  {input_video_path}.")
        video_files = find_videos(input_video_path, input_video_extension)
        dumpYaml(videofiles_cache_yaml, video_files, 'w')
    log(f"A total of {len(video_files)} video files found.", bcolors.OKCYAN)

    return video_files