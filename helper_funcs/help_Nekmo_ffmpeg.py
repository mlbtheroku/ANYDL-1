#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


import asyncio
import os
import time
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import subprocess


async def place_water_mark(input_file, output_file, water_mark_file):
    watermarked_file = output_file + ".watermark.png"
    metadata = extractMetadata(createParser(input_file))
    width = metadata.get("width")
    # https://stackoverflow.com/a/34547184/4723940
    shrink_watermark_file_genertor_command = [
        "ffmpeg",
        "-i", water_mark_file,
        "-y -v quiet",
        "-vf",
        "scale={}*0.5:-1".format(width),
        watermarked_file
    ]
    # print(shrink_watermark_file_genertor_command)
    process = await asyncio.create_subprocess_exec(
        *shrink_watermark_file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    commands_to_execute = [
        "ffmpeg",
        "-i", input_file,
        "-i", watermarked_file,
        "-filter_complex",
        # https://stackoverflow.com/a/16235519
        # "\"[0:0] scale=400:225 [wm]; [wm][1:0] overlay=305:0 [out]\"",
        # "-map \"[out]\" -b:v 896k -r 20 -an ",
        "\"overlay=(main_w-overlay_w):(main_h-overlay_h)\"",
        # "-vf \"drawtext=text='@FFMovingPictureExpertGroupBOT':x=W-(W/2):y=H-(H/2):fontfile=" + Config.FONT_FILE + ":fontsize=12:fontcolor=white:shadowcolor=black:shadowx=5:shadowy=5\"",
        output_file
    ]
    # print(commands_to_execute)
    process = await asyncio.create_subprocess_exec(
        *commands_to_execute,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    return output_file


async def take_screen_shot(video_file, output_directory, ttl):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = output_directory + \
        "/" + str(time.time()) + ".jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    # width = "90"
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None

# https://github.com/Nekmo/telegram-upload/blob/master/telegram_upload/video.py#L26

async def cult_small_video(video_file, output_directory, start_time, end_time):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = output_directory + \
        "/" + str(round(time.time())) + ".mp4"
    file_genertor_command = [
        "ffmpeg",
        "-i",
        video_file,
        "-ss",
        start_time,
        "-to",
        end_time,
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None


async def generate_screen_shots(
    video_file,
    output_directory,
    is_watermarkable,
    wf,
    min_duration,
    no_of_photos
):
    metadata = extractMetadata(createParser(video_file))
    duration = 0
    if metadata is not None:
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
    if duration > min_duration:
        images = []
        ttl_step = duration // no_of_photos
        current_ttl = ttl_step
        for looper in range(0, no_of_photos):
            ss_img = await take_screen_shot(video_file, output_directory, current_ttl)
            current_ttl = current_ttl + ttl_step
            if is_watermarkable:
                ss_img = await place_water_mark(ss_img, output_directory + "/" + str(time.time()) + ".jpg", wf)
            images.append(ss_img)
        return images
    else:
        return None

async def exa_audio(download_location, message_id, video_file):
    ffprobe_cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
               "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", video_file]
    print(video_file)
    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
    audio_files = []
    # os.makedirs(str(message_id))
    if len(result.stderr.strip()) < 6:
        num_audio_tracks = len(result.stdout.strip().split('\n'))
        for i in range(num_audio_tracks):
            file_ext = result.stdout.strip().split('\n')[i]
            output_audio_file = f"{download_location}audio_{i+1}.{file_ext}"
            audio_files.append(output_audio_file)
            audio_extract = ["ffmpeg", "-loglevel", "warning", "-i", video_file, "-map", f"0:a:{i}",  "-c", "copy", "-vn", "-hide_banner", output_audio_file]
            subprocess.run(audio_extract)
        # Wait for the subprocess to finish
        return audio_files
    else:
        return None
