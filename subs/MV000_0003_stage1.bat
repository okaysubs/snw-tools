ffmpeg32 -y -i MV000_0003-hardsub.avs -vf vflip -vcodec rawvideo -pix_fmt bgr24 -t 55 prolog1.avi
ffmpeg32 -y -i MV000_0003-hardsub.avs -vf vflip -vcodec rawvideo -pix_fmt bgr24 -ss 55 prolog2.avi
