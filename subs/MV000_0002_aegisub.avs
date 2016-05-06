#v=ImageSource("E:\dev\usc1\%04d.png", start=32, end=2721, fps=29.97002997002997002997002997003, use_DevIL=true)
#a=BlankClip(31, 960, 544, "rgb24", 30000, 1001).KillAudio()
#b=BlankClip(39, 960, 544, "rgb24", 30000, 1001).KillAudio()
#a+v+b
#info(v)

ImageSource("E:\dev\usc1\%04d.png", start=1, end=2760, fps=29.97002997002997002997002997003, use_DevIL=true)
ConvertToRGB24("Rec601").ConvertToYV12()