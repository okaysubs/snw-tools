ffmpeg32 -y -i MV000_0002_stage1a.avs -vf subtitles=MV000_0002_960.ass,vflip -vcodec rawvideo MV000_0002_960.avi
ffmpeg32 -y -i MV000_0002_stage1b.avs -vcodec rawvideo -pix_fmt bgr24 -t 45 kfx1.avi
ffmpeg32 -y -i MV000_0002_stage1b.avs -vcodec rawvideo -pix_fmt bgr24 -ss 45 kfx2.avi
del MV000_0002_960.avi
