import ffmpeg
from django.test import TestCase


# Create your tests here.
class TestVideoUpload(TestCase):
    def test_scale_filter(self):
        input_path = r"F:\resource\videos\2023\04\16\12\17\ff026f23cfc25910b80c3bf76cf66165.mp4"
        output_path = r"F:\resource\videos\2023\04\16\12\17\ff026f23cfc25910b80c3bf76cf66165_640x360_test.mp4"
        input_ = ffmpeg.input(input_path)
        output = ffmpeg.filter(input_.video, "scale", "640x360").output(input_.audio, output_path)
        print(output.get_args())
