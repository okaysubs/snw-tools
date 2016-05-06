LoadPlugin("C:\Users\ed\bin\xy-VSFilter.dll")

function f(clip c, int n)
{
    # take frame before n and copy over n
    c.FreezeFrame(n, n, n-1)
}
function r(clip c, int n)
{
    # take frame after n and copy over n
    c.FreezeFrame(n, n, n+1)
}

a=ImageSource("E:\dev\usc\%04d.png", start=1, end=3300, fps=29.97002997002997002997002997003, use_DevIL=true).ConvertToRGB24()
a=a.TextSub("E:\dev\snw\work\PSP_GAME\USRDIR\mv\MV000_0003.ass")
a=a.Spline16Resize(480, 272)

a=a.f(1).f(5).f(16).f(20).f(31).f(74).f(78).f(89).f(93).r(92).r(96).r(128).f(133).f(138).r(143).r(148).f(153).f(158).f(163).r(168).r(170).r(272).r(283).r(287).r(790).r(792).r(795).r(797).f(799).r(801).r(804).FreezeFrame(809,809,811).r(810).r(814).r(817).FreezeFrame(819,819,821).r(820).f(1204).r(1241).r(1885).r(1889).r(1915).r(1919).f(2097).f(2112).f(2144).r(2155).r(2199)

#b=ImageSource("E:\dev\isc\%04d.png", start=1, end=3300, fps=29.97002997002997002997002997003, use_DevIL=true).ConvertToRGB24()
#b=b.TextSub("E:\dev\snw\work\PSP_GAME\USRDIR\mv\MV000_0003.ass")
#b=b.Spline16Resize(480, 272)

#StackHorizontal(a,b)
#Spline16Resize(1920,544)

a
