import os
import shutil
import threading
from pathlib import Path
from typing import Sequence

import ffmpeg
from rest_framework.viewsets import ModelViewSet

from apps.video.models import StatusEnum
from service.multipart_file_upload import MultipartFileUploadService
from defog.defog import DefogModel


def extract_ext(file_path: str):
    if "." not in file_path:
        raise ValueError("there is not a ext name in the file path")

    return file_path.rsplit(".", 1)


class VideoUploadService(MultipartFileUploadService):

    def generate_mpd_path(self, video_path: str, file_hash: str):
        parent_dir = Path(video_path).parent
        dash_dir = os.path.join(parent_dir, f'dash_{file_hash}')
        if not os.path.exists(dash_dir):
            os.makedirs(dash_dir)
        # mpd_path = os.path.join(dash_dir, "stream.mpd")
        # ffmpeg进行dash分片时，最后一级的路径分隔符必须是'/'，即使windows平台也是如此，上面一行的写法在windows平台会出现问题，疑似为ffmpeg的bug
        mpd_path = dash_dir + "/stream.mpd"
        return mpd_path

    def generate_poster_path(self, video_path: str, file_hash: str):
        parent_dir = Path(video_path).parent
        poster_path = os.path.join(parent_dir, f'{file_hash}_poster.png')
        return poster_path

    def move_to_db_dictionary(self, origin_video_path: str):
        target_dir = self._get_upload_dir("videos")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        target_path = shutil.move(origin_video_path, os.path.join(target_dir, os.path.basename(origin_video_path)))
        return target_path

    def video_process(self, input_path: str, mpd_path: str, poster_path: str, video_id: str, operator: ModelViewSet):
        def time_consuming_process():
            # step0 为视频生成首帧封面
            self.generate_video_poster(input_path, poster_path)
            # todo step1 将原视频交给去雾模型进行演算
            # step2 将去雾视频转换为其它分辨率，共3个分辨率以供选择(1920x1080, 1280x720, 640x360)
            # multi_resolution_output = self.resolution_conversion(input_path, ['1920x1080', '1280x720', '640x360'])
            multi_resolution_output = self.resolution_conversion_new(input_path, ['1920x1080', '1280x720', '640x360'],
                                                                     ['8M', '4.5M', '1.5M'])

            if_defog = False
            if if_defog:
                defog_video_path = self.defog_video(input_path)
                multi_resolution_output_defog = self.resolution_conversion_new(defog_video_path,
                                                                               ['1920x1080', '1280x720', '640x360'],
                                                                               ['8.1M', '4.6M', '1.6M'])
                # step3 将原视频和去雾视频转为dash(异步)
                self.convert2dash(multi_resolution_output + multi_resolution_output_defog, mpd_path)
            else:
                self.convert2dash(multi_resolution_output, mpd_path)

            # 更新数据库状态
            operator.get_queryset().filter(videoId=video_id).update(
                status=StatusEnum.FINISHED.value,
                resolutionVersion='1920x1080,1280x720,640x360',
                metadata={
                    'phase': [
                        {
                            'time': 1,
                            'text': '准备阶段',
                        },
                        {
                            'time': 3,
                            'text': '第一阶段',
                        }
                    ],
                }
            )

        threading.Thread(target=time_consuming_process).start()

    def convert2dash(self, input_path_list: Sequence[str], mpd_path: str):
        input_list = [ffmpeg.input(file_path) for file_path in input_path_list]
        ffmpeg.output(*input_list, mpd_path, vcodec="h264", acodec="aac", preset="veryfast", seg_duration=5,
                      adaptation_sets="id=0,streams=v id=1,streams=a", f="dash").run(quiet=True)

    def resolution_conversion(self, input_path: str, target_resolution_list: Sequence[str]):
        file_path_, ext = extract_ext(input_path)
        output_list = []
        output_path_list = []

        # 检查音频流是否存在
        probe = ffmpeg.probe(input_path)
        has_audio = any(stream.get('codec_type') == 'audio' for stream in probe['streams'])

        for target_resolution in target_resolution_list:
            output_path = f'{file_path_}_{target_resolution}.{ext}'
            print(output_path)
            output_path_list.append(output_path)
            input_ = ffmpeg.input(input_path)
            video = ffmpeg.filter(input_.video, "scale", target_resolution)
            if has_audio:
                output = video.output(input_.audio, output_path)
            else:
                output = video.output(output_path)
            output_list.append(output)

        ffmpeg.merge_outputs(*output_list).run(quiet=False)
        return output_path_list

    def resolution_conversion_new(self, input_path: str, target_resolution_list: Sequence[str],
                                  target_bv_list: Sequence[str]):
        file_path_, ext = extract_ext(input_path)
        output_list = []
        output_path_list = []

        # 检查音频流是否存在
        probe = ffmpeg.probe(input_path)
        has_audio = any(stream.get('codec_type') == 'audio' for stream in probe['streams'])

        for i, target_resolution in enumerate(target_resolution_list):
            output_path = f'{file_path_}_{target_resolution}.{ext}'
            print(output_path)
            output_path_list.append(output_path)
            input_ = ffmpeg.input(input_path)
            video = input_.video.filter('scale', target_resolution).filter('setdar', '16/9')

            if has_audio:
                output = video.output(input_.audio, output_path, b=target_bv_list[i])
            else:
                output = video.output(output_path, b=target_bv_list[i])
            output_list.append(output)

        ffmpeg.merge_outputs(*output_list).run(quiet=False)
        return output_path_list

    def generate_video_poster(self, video_path: str, poster_path: str):
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

    def defog_video(self, input_path: str):
        defog_model = DefogModel(input_path)
        defog_model.video2image()
        defog_model.inference()
        defog_video_path = defog_model.image2video()
        return defog_video_path
