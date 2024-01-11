import os
import torch
import torchvision
import torchvision.transforms as transforms
import defog.utils as utils
from .dataloader import CycleDataset
from .generators import define_Gen
import ffmpeg
from fractions import Fraction

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tmp_path = os.path.join(os.path.join(base_path, 'resource'), 'tmp')


class DefogModel:
    def __init__(self, video_path):
        self.fps = None
        self.video_path = video_path
        self.video_save_path = os.path.dirname(video_path)
        self.checkpoint_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cho.ckpt')
        self.dataset_dir = os.path.join(self.video_save_path, 'input_image')
        self.output_image_path = os.path.join(self.video_save_path, 'defog_image')
        self.batch_size = 1
        self.gpu_ids = [0]
        self.crop_height = 480
        self.crop_width = 480
        self.norm = 'instance'
        self.no_dropout = 'store_true'
        self.ngf = 64
        self.ndf = 64

    def video2image(self):
        info = ffmpeg.probe(self.video_path)
        vs = next(c for c in info['streams'] if c['codec_type'] == 'video')
        self.fps = float(Fraction(vs['r_frame_rate']))
        if not os.path.exists(self.dataset_dir):
            os.makedirs(self.dataset_dir)
        try:
            ffmpeg.input(self.video_path).output(os.path.join(self.dataset_dir, '%d.jpg'), r=self.fps,
                                                 pattern_type='glob').run(capture_stdout=True, capture_stderr=True)
        except Exception as e:
            print(e)

    def image2video(self):
        try:
            ffmpeg.input(os.path.join(self.output_image_path, '%d.jpg'), framerate=self.fps) \
                .output(os.path.join(self.video_save_path, 'defog.mp4')).run(capture_stdout=True, capture_stderr=True)
        except Exception as e:
            print(e)
        return os.path.join(self.video_save_path, 'defog.mp4')

    def inference(self):
        transform = transforms.Compose(
            [transforms.Resize((self.crop_height, self.crop_width)),
             transforms.ToTensor(),
             transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])])

        a_test_data = CycleDataset(dataset_name=self.dataset_dir, transform=transform)
        a_test_loader = torch.utils.data.DataLoader(a_test_data, batch_size=self.batch_size, shuffle=False,
                                                    num_workers=0)

        Gab = define_Gen(input_nc=3, output_nc=3, ngf=self.ngf, netG='resnet_9blocks', norm=self.norm,
                         use_dropout=not self.no_dropout, gpu_ids=self.gpu_ids)
        Gba = define_Gen(input_nc=3, output_nc=3, ngf=self.ngf, netG='resnet_9blocks', norm=self.norm,
                         use_dropout=not self.no_dropout, gpu_ids=self.gpu_ids)

        # utils.print_networks([Gab, Gba], ['Gab', 'Gba'])

        try:
            ckpt = utils.load_checkpoint('%s' % self.checkpoint_path)  # /latest.ckpt
            Gab.load_state_dict(ckpt['Gab'])
            Gba.load_state_dict(ckpt['Gba'])
        except:
            print(' [*] No checkpoint!')
        """ run """
        Gab.eval()
        Gba.eval()
        print("test len:", len(a_test_loader))
        if not os.path.isdir(self.output_image_path):
            os.makedirs(self.output_image_path)
        with torch.no_grad():
            for i, a_real in enumerate(a_test_loader):
                a_real_test = utils.cuda(a_real)
                b_fake_test = Gba(a_real_test)
                # 用于输出单张图片，需要修改batch为1
                pic = (b_fake_test.data + 1) / 2.0
                torchvision.utils.save_image(pic, os.path.join(self.output_image_path) + '/{}.jpg'.format(i),
                                             nrow=self.batch_size)
