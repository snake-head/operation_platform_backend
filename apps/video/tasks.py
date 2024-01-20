from typing import Sequence

import ffmpeg
from celery import shared_task

from apps.video.models import StatusEnum, Video
from defog.defog import DefogModel
import logging
logger = logging.getLogger(__name__)


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


@shared_task(bind=True)
def video_process(self, input_path: str, mpd_path: str, video_id: str):
    try:
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
    except Exception as e:
        self.retry(exc=e, countdown=4, max_retries=4)

