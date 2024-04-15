from django.conf import settings
from django.core.management.base import BaseCommand
from apps.video.models import Video, StatusEnum

import argparse
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Sequence

import ffmpeg
from celery import shared_task

from defog.defog import DefogModel

MEDIA_ROOT = settings.MEDIA_ROOT


def extract_ext(file_path: str):
    if "." not in file_path:
        raise ValueError("there is not a ext name in the file path")

    return file_path.rsplit(".", 1)


def resolution_conversion_new(input_path: str,
                              target_resolution_list: Sequence[str],
                              target_bv_list: Sequence[str]):
    file_path_, ext = extract_ext(input_path)
    output_list = []
    output_path_list = []

    # 检查音频流是否存在
    probe = ffmpeg.probe(input_path)
    has_audio = any(
        stream.get('codec_type') == 'audio' for stream in probe['streams'])

    for i, target_resolution in enumerate(target_resolution_list):
        output_path = f'{file_path_}_{target_resolution}.{ext}'
        print(output_path)
        output_path_list.append(output_path)
        input_ = ffmpeg.input(input_path, hwaccel='cuda')
        video = input_.video.filter('scale', target_resolution).filter(
            'setdar', '16/9')

        if has_audio:
            output = video.output(input_.audio, output_path,
                                  vcodec='h264_nvenc', b=target_bv_list[i])
        else:
            output = video.output(output_path, vcodec='h264_nvenc',
                                  b=target_bv_list[i])
        output_list.append(output)

    ffmpeg.merge_outputs(*output_list).run(quiet=True)
    return output_path_list


def defog_video(input_path: str):
    defog_model = DefogModel(input_path)
    defog_model.video2image()
    defog_model.inference()
    defog_video_path = defog_model.image2video()
    return defog_video_path


def convert2dash(input_path_list: Sequence[str], mpd_path: str):
    input_list = [ffmpeg.input(file_path, hwaccel='cuda') for file_path in input_path_list]
    ffmpeg.output(*input_list, mpd_path, vcodec='h264_nvenc', acodec="aac",
                  seg_duration=5,
                  adaptation_sets="id=0,streams=v id=1,streams=a",
                  f="dash").run(quiet=True)


def generate_poster_path(video_path: str, file_hash: str):
    parent_dir = Path(video_path).parent
    poster_path = os.path.join(parent_dir, f'{file_hash}_poster.png')
    return poster_path


def video_process(input_path: str, mpd_path: str, video_id: str):
    # self.generate_video_poster(input_path, poster_path)
    # todo step1 将原视频交给去雾模型进行演算
    # step2 将去雾视频转换为其它分辨率，共3个分辨率以供选择(1920x1080, 1280x720, 640x360)
    # multi_resolution_output = self.resolution_conversion(input_path, ['1920x1080', '1280x720', '640x360'])
    multi_resolution_output = resolution_conversion_new(input_path, ['1920x1080', '1280x720', '640x360'], ['8M', '4.5M', '1.5M'])

    if_defog = False
    if if_defog:
        defog_video_path = defog_video(input_path)
        multi_resolution_output_defog = resolution_conversion_new(
            defog_video_path,
            ['1920x1080', '1280x720', '640x360'],
            ['8.1M', '4.6M', '1.6M'])
        # step3 将原视频和去雾视频转为dash(异步)
        convert2dash(
            multi_resolution_output + multi_resolution_output_defog, mpd_path)
    else:
        convert2dash(multi_resolution_output, mpd_path)

    # 更新数据库状态
    video = Video.objects.get(videoId=video_id)
    video.status = StatusEnum.FINISHED.value
    video.resolutionVersion = '1920x1080,1280x720,640x360'
    video.save()


def generate_video_path():
    while True:
        # 获取当前时间
        now = datetime.now()

        # 构建路径
        video_path = os.path.join(
            "/data/videos",
            # "D:\\Project_Code\\video-site\\script",
            str(now.year),
            str(now.month).zfill(2),
            str(now.day).zfill(2),
            str(now.hour).zfill(2),
            str(now.minute).zfill(2)
        )

        # 检查路径是否已存在
        if not os.path.exists(video_path):
            os.makedirs(video_path)
            break

    return video_path


def move_video(video_path, folder_path):
    # 移动文件
    new_video_path = shutil.move(video_path, folder_path)
    return new_video_path


def generate_mpd_path(video_path: str, file_hash: str):
    parent_dir = Path(video_path).parent
    dash_dir = os.path.join(parent_dir, f'dash_{file_hash}')
    if not os.path.exists(dash_dir):
        os.makedirs(dash_dir)
    # mpd_path = os.path.join(dash_dir, "stream.mpd")
    # ffmpeg进行dash分片时，最后一级的路径分隔符必须是'/'，即使windows平台也是如此，上面一行的写法在windows平台会出现问题，疑似为ffmpeg的bug
    mpd_path = dash_dir + "/stream.mpd"
    return mpd_path


def generate_video_poster(video_path: str, poster_path: str):
    probe = ffmpeg.probe(video_path)
    video_duration = float(probe['format']['duration'])
    if video_duration >= 60.0:  # 大于等于1分钟
        time_point = "00:01:00"
    else:  # 小于1分钟
        time_point = "00:00:00"
    try:
        ffmpeg.input(video_path, ss=time_point).output(poster_path, vframes=1).run(quiet=True)
    except ffmpeg.Error as e:
        print("An error occurred while generating the video poster: {0}".format(e))



class Command(BaseCommand):
    help = '手动上传视频后，使用此命令在命令行中处理'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='视频路径')
        parser.add_argument('course', type=str, help='course id')

    def handle(self, *args, **options):
        source_path = options['path']
        course_id = options['course']
        folder_path = generate_video_path()
        file_hash = str(int(time.time()))
        folder_path = os.path.join(folder_path, file_hash+'.mp4')

        target_path = move_video(source_path, folder_path)
        poster_path = generate_poster_path(target_path, file_hash)
        mpd_path = generate_mpd_path(target_path, file_hash)
        video_id = 'vid_{}'.format(file_hash)

        video_data = {
            "videoId": video_id,
            "videoName": os.path.basename(source_path),
            "videoUrl": os.path.relpath(mpd_path, MEDIA_ROOT),
            "coverImgUrl": os.path.relpath(poster_path, MEDIA_ROOT),
            "courseId": course_id,
            "status": StatusEnum.PROCESSING.value
        }
        new_video = Video.objects.create(**video_data)
        print(new_video)

        generate_video_poster(target_path, poster_path)
        video_process(target_path, mpd_path, video_id)
        # 这里可以访问模型和执行脚本逻辑