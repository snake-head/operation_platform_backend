import os

import requests
from django.core.management import BaseCommand
from apps.video.models import Video, CaptionAudio
import hashlib


class Command(BaseCommand):
    help = '将视频caption转化wav文件'

    def add_arguments(self, parser):
        parser.add_argument('id', type=str, help='视频id')

    def handle(self, *args, **options):
        video_id = options['id']
        url = 'http://172.16.200.93:30810/synthesize'
        video = Video.objects.get(id=video_id)
        save_dir = '/data/videos/audio'
        os.makedirs(save_dir, exist_ok=True)
        caption = video.metadata['caption']
        for cap in caption:
            time = cap['time']
            # if time < 1000:
            #     continue
            text = cap['text']

            # 检查 CaptionAudio 中是否已存在相同的 text
            if CaptionAudio.objects.filter(text=text).exists():
                self.stdout.write(
                    f"Skip processing as entry already exists for text: {text}")
                continue

            md5_hash = hashlib.md5(text.encode()).hexdigest()
            save_path = save_dir + '/' + md5_hash + '.wav'
            self.stdout.write(save_path)

            data = {
                "text": text,
                "save_path": save_path
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                response_data = response.json()  # 解析返回的 JSON 数据
                audio_path = response_data.get('audio_path')  # 获取 audio_path 值

                # 创建 CaptionAudio 记录
                CaptionAudio.objects.create(text=text, audioUrl=audio_path.replace("https://omentor.vico-lab.com:3443/", ''))

                self.stdout.write(audio_path)
            else:
                self.stdout.write(
                    f"Error: Received status code {response.status_code}")