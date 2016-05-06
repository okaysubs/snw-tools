using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.IO;
using System.Diagnostics;

/* GamePatcher SNW Edition v1.0
 * MIT-Licensed, 2016-05-06, ed <irc.rizon.net>
 * https://github.com/okaysubs/snw-tools
 */

namespace GamePatcher
{
    public partial class Form1 : Form
    {
        const int L_CK = 16;
        const int L_SZ = 8;
        long EXE_END = -1;
        Timer opentimer;
        string[] openqueue = null;
        public Form1()
        {
            InitializeComponent();
            opentimer = new Timer();
            opentimer.Interval = 100;
            opentimer.Tick += opentimer_Tick;
        }

        void updatecheck()
        {
            try
            {
                string cver = "x";
                this.Invoke((MethodInvoker)delegate { cver = label7.Text.Substring(1); });
                System.Net.Sockets.TcpClient tc = new System.Net.Sockets.TcpClient();
                tc.Connect("api.ocv.me", 80);
                var s = tc.GetStream();
                var msg = Encoding.UTF8.GetBytes(
                    "GET /snw HTTP/1.1\r\n" +
                    "Host: api.ocv.me\r\n" +
                    "User-Agent: GamePatcher/" + cver + "\r\n" +
                    "Connection: close\r\n" +
                    "\r\n");
                s.Write(msg, 0, msg.Length);
                s.Flush();
                var sb = new StringBuilder();
                var buf = new byte[8192];
                while (true)
                {
                    int i = s.Read(buf, 0, buf.Length);
                    if (i <= 0) break;
                    sb.Append(Encoding.UTF8.GetString(buf, 0, i));
                }
                //MessageBox.Show(sb.ToString());
                string res = sb.ToString();
                if (!res.Contains("_CurrentVersion_"))
                {
                    MessageBox.Show("Failed to check for updates!\r\n\r\nWhatever, let's patch.");
                }
                else if (!res.Contains("_CurrentVersion_" + cver + "_"))
                {
                    if (DialogResult.Yes == MessageBox.Show(
                        "Update available at  https://ocv.me/snw\r\n\r\n" +
                        "Abort and visit website?", "New version",
                        MessageBoxButtons.YesNo, MessageBoxIcon.Warning))
                    {
                        web();
                    }
                }
                else st("No updates available");
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Failed to check for updates!\r\n\r\nWhatever, let's patch.",
                    "hey", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }
        byte[] md5xor(byte[] org, bool dec = false)
        {
            byte seed = 0xed;
            for (int a = 0; a < org.Length; a++)
            {
                byte old = org[a];
                org[a] ^= seed;
                if (dec) seed = old;
                else seed = org[a];
            }
            return org;
        }

        double progress;
        double progressi;
        double progressn;
        bool bgmReady = false;
        System.Reflection.Assembly _me;
        string tempdir = "";
        bool showmus;

        Color fade(Color c1, Color c2, double w) //weight
        {
            return Color.FromArgb(
                (int)(c1.R * w) + (int)(c2.R * (1 - w)),
                (int)(c1.R * w) + (int)(c2.R * (1 - w)),
                (int)(c1.R * w) + (int)(c2.R * (1 - w)));
        }
        FontStyle hasFont(string fontName)
        {
            if (hasFont(fontName, FontStyle.Regular)) return FontStyle.Regular;
            if (hasFont(fontName, FontStyle.Bold)) return FontStyle.Bold;
            if (hasFont(fontName, FontStyle.Italic)) return FontStyle.Italic;
            return FontStyle.Strikeout;
        }
        bool hasFont(string fontName, FontStyle style)
        {
            using (var test = new Font(fontName, 8, style))
            {
                return 0 == string.Compare(fontName, test.Name,
                    StringComparison.InvariantCultureIgnoreCase);
            }
        }

        void decryptEboot(string path, string errmsg)
        {
            var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
            var ms = new MemoryStream();
            try
            {
                new PSPFormatDecryptor(fs).Decrypt(ms);
                ms.Position = 0;
                fs.Dispose();
                fs = new FileStream(path, FileMode.Create, FileAccess.Write);
                ms.WriteTo(fs);
            }
            catch (Exception ex)
            {
                if (!string.IsNullOrEmpty(errmsg))
                    MessageBox.Show(errmsg + ex.Message);
            }
            fs.Dispose();
            ms.Dispose();
        }

        bool stopfading = false;
        private void Form1_Load(object sender, EventArgs e)
        {
            if (false)
            {
                Timer tfds = new Timer();
                tfds.Interval = 1000;
                tfds.Start();
                tfds.Tick += delegate(object oa, EventArgs ob)
                {
                    tfds.Stop();
                    string me = Application.StartupPath + "\\";
                    decryptEboot(me + "eboot.bin", "whoops");
                    MessageBox.Show("k");
                };
                return;
            }

            if (false)
            {
                Timer tfds = new Timer();
                tfds.Interval = 1000;
                tfds.Start();
                tfds.Tick += delegate(object oa, EventArgs ob)
                {
                    this.Hide();
                    tfds.Stop();
                    Program.popception();
                };
            }

            string[] fonts = {
                "Consolas",
                "Lucida Console",
                "Liberation Mono"
            };
            string fontname = "";
            FontStyle fontstyle = FontStyle.Regular;
            foreach (string f in fonts)
            {
                fontstyle = hasFont(f);
                if (fontstyle != FontStyle.Strikeout)
                {
                    fontname = f;
                    break;
                }
            }
            TextBox tb = new TextBox();
            Font font = !string.IsNullOrEmpty(fontname) ?
                new System.Drawing.Font(fontname, tb.Font.SizeInPoints * 1.1f, fontstyle) :
                new System.Drawing.Font(FontFamily.GenericMonospace, tb.Font.SizeInPoints);
            tb.Font = font;
            int ht = tb.Height;
            tb.Dispose();
            _installer.Font = font;
            //p_status.SendToBack();



            _loaderS.Width = 0;
            _team.Visible = false;
            _me = System.Reflection.Assembly.GetExecutingAssembly();

            bool cockblock = false;
            Timer t = new Timer();
            t.Interval = 100;
            t.Start();
            t.Tick += delegate(object oa, EventArgs ob)
            {
                if (cockblock) return;
                cockblock = true;
                t.Stop();
                killMusic();
                //cdex();

                st("Checking for updates ...");
                new System.Threading.Thread(new System.Threading.ThreadStart(updatecheck)).Start();

                Color cp = _pane1.BackColor;
                Color cb = _loaderB.BackColor;
                Color cf = _loaderS.BackColor;
                _loaderC.ForeColor = fade(cp, cf, 0.2);
                _loaderB.BackColor = fade(cp, cb, 0.4);
                _loaderS.BackColor = fade(cp, cf, 0.4);
                cp = _pane1.BackColor;
                cb = _loaderB.BackColor;
                cf = _loaderS.BackColor;

                _loaderC.Text = "Checking for errors ...";
                new System.Threading.Thread(new System.Threading.ThreadStart(md5thread)).Start();
                while (EXE_END == -1)
                {
                    _loaderS.Width = (int)(progress * _loaderB.Width);
                    Application.DoEvents();
                    System.Threading.Thread.Sleep(20);
                }



                if (File.Exists("okay.iso") &&
                    File.Exists("orig.iso") &&
                    DialogResult.Yes == MessageBox.Show(
                        "Found required ISO files, create new patch?\r\n\r\n" +
                        "orig.iso  should be the original VN\r\n" +
                        "okay.iso should be the final translated VN",
                        "Make patch",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Question)
                    )
                {
                    _pane1.SendToBack();
                    p_music.SendToBack();
                    creds.Visible = true;
                    _loaderB.Visible = _loaderC.Visible = _loaderS.Visible = false;
                    new System.Threading.Thread(new System.Threading.ThreadStart(patchthread)).Start();
                    return;
                }
                else if (EXE_END < 0)
                {
                    if (DialogResult.Yes == MessageBox.Show(
                        "This patch is corrupted!\r\n\r\n" +
                        //sum2text(chMD5) + " was expected\r\n" +
                        //sum2text(myMD5) + " was obtained\r\n\r\n" +
                        "Try downloading from  https://ocv.me/kks\r\n\r\n" +
                        "Visit website?",
                        "Bad patch",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Warning))
                        web();

                    if (File.Exists(Application.StartupPath + @"\snw_gp_archive\0.xd3"))
                        return;

                    System.Diagnostics.Process.GetCurrentProcess().Kill();
                }
                else st("Patcher integrity check OK");

                _loaderC.Text = "Extracting patch data ...";
                new System.Threading.Thread(new System.Threading.ThreadStart(exthread)).Start();
                while (!extracting && !bgmReady)
                {
                    System.Threading.Thread.Sleep(10);
                    Application.DoEvents();
                }
                while (extracting || bgmReady)
                {
                    _loaderS.Width = (int)(progress * _loaderB.Width);
                    if (bgmReady)
                    {
                        bgmReady = false;
                        showmus = true;
                        mu_grays_Click(mu_grays, null);
                        p_music.Visible = true;
                    }
                    Application.DoEvents();
                    System.Threading.Thread.Sleep(20);
                }
                p_music.BringToFront();
                _pane1.BringToFront();
                _open.Enabled = true;
                stopfading = false;
                contfocus();

                for (int a = 0; a < 10; a++)
                {
                    if (stopfading) break;
                    _loaderC.ForeColor = fade(cp, cf, a / 10.0);
                    _loaderB.BackColor = fade(cp, cb, a / 10.0);
                    _loaderS.BackColor = fade(cp, cf, a / 10.0);
                    System.Threading.Thread.Sleep(10);
                    Application.DoEvents();
                }
                _loaderC.Visible = false;
                _loaderB.Visible = false;
                _loaderS.Visible = false;

                cf = _team.ForeColor;
                cb = fade(cf, cp, 0.5);
                _team.ForeColor = _team.BackColor;
                _teambar.BackColor = _team.BackColor;
                _team.Visible = true;

                if (!string.IsNullOrEmpty(Program.SOURCE_ISO))
                    stopfading = true;

                for (int a = 0; a < 50; a++)
                {
                    if (stopfading) break;
                    _team.ForeColor = fade(cf, cp, a / 50.0);
                    _teambar.BackColor = fade(cb, cp, a / 50.0);
                    System.Threading.Thread.Sleep(10);
                    Application.DoEvents();
                }
                _team.ForeColor = fade(cf, cp, 1);
                _teambar.BackColor = fade(cb, cp, 1);

                if (!string.IsNullOrEmpty(Program.SOURCE_ISO))
                    openevent(new string[] { Program.SOURCE_ISO });
            };
            md5pb.Width = 0;
            md5pb.Height = panel4.Height;
            md5pb.Visible = true;
            progress = -1;
            progressi = 0;
            progressn = 1;
            Timer pt = new Timer();
            pt.Interval = 20;
            pt.Start();
            pt.Tick += delegate(object oa, EventArgs ob)
            {
                if (progress <= 0)
                {
                    if (md5pb.Width == 0)
                        return;

                    md5pb.Width = 0;
                    return;
                }
                double pv = (progress / progressn) + (progressi / progressn);
                md5pb.Width = panel4.Width - (int)Math.Round(panel4.Width * pv);
            };
        }

        void playNSF(string name)
        {
            new System.Threading.Thread(new System.Threading.ParameterizedThreadStart(actuallyPlayNSF)).Start(name);
        }

        void actuallyPlayNSF(object oname)
        {
            string name = (string)oname;
            killMusic();
            string run = "\\nsf\\chiptune.exe";
            if (!File.Exists(tempdir + run))
                tempdir = Application.StartupPath + "\\snw_gp_archive";

            System.Diagnostics.Process proc = new System.Diagnostics.Process();
            proc.StartInfo.WindowStyle = System.Diagnostics.ProcessWindowStyle.Hidden;
            proc.StartInfo.FileName = tempdir + run;
            proc.StartInfo.WorkingDirectory = tempdir + "\\nsf";
            proc.StartInfo.Arguments = name + ".nsf";
            proc.StartInfo.CreateNoWindow = true;
            proc.Start();
            return;
        }
        void killMusic()
        {
            System.Diagnostics.Process[] procs = System.Diagnostics.Process.GetProcessesByName("chiptune");
            for (int a = 0; a < procs.Length; a++)
            {
                procs[a].Kill();
            }
        }
        long toExtract = 0;
        bool extracting = false;
        void md5thread()
        {
            long lenTotal = 0;
            string binpath = Application.ExecutablePath;
            if (!string.IsNullOrEmpty(Program.TARGET_EXE))
                binpath = Program.TARGET_EXE;

            byte[] myMD5 = md5xor(md5sum(binpath, L_CK));
            byte[] chMD5 = new byte[myMD5.Length]; // both are L_CK long
            byte[] xxLEN = new byte[L_SZ];
            using (FileStream fs = new FileStream(binpath, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                fs.Seek(-chMD5.Length, SeekOrigin.End);
                fs.Read(chMD5, 0, chMD5.Length);

                fs.Seek(-(chMD5.Length + xxLEN.Length), SeekOrigin.End);
                fs.Read(xxLEN, 0, xxLEN.Length);

                lenTotal = fs.Length;
            }
            bool md5ok = true;
            for (int a = 0; a < myMD5.Length; a++)
            {
                if (myMD5[a] != chMD5[a])
                {
                    md5ok = false;
                    break;
                }
            }
            if (md5ok)
            {
                byte[] binLen = md5xor(xxLEN, true);
                EXE_END = BitConverter.ToInt64(binLen, 0);
                if (EXE_END < 0 || EXE_END > lenTotal)
                    MessageBox.Show("exe is way fucked");
            }
            else EXE_END = -2;
        }
        void exthread()
        {
            string[] temps = Environment.GetEnvironmentVariable("TEMP").Split(';');
            tempdir = temps[0].Trim();
            foreach (string temp in temps)
            {
                string fds = temp.Replace("\\", "/").ToLower();
                if (fds.Contains("/temp"))
                {
                    tempdir = temp.Trim();
                    break;
                }
            }
            foreach (string temp in temps)
            {
                string fds = temp.Replace("\\", "/").ToLower();
                if (fds.Contains("/temp") &&
                    fds.Contains("/appdata/"))
                {
                    tempdir = temp.Trim();
                    break;
                }
            }
            tempdir += "\\kengekit\\";

            while (true)
            {
                try
                {
                    Process[] procs = Process.GetProcessesByName("chiptune");
                    if (procs.Length < 1)
                        break;
                    procs[0].Kill();
                    Application.DoEvents();
                    System.Threading.Thread.Sleep(100);
                }
                catch { break; }
            }
            cleanup(true);
            try
            {
                Directory.CreateDirectory(tempdir);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error when extracting to:\r\n" + tempdir + "\r\n\r\nError message:\r\n" + ex.Message);
            }

            string chk = "(none)";
            try
            {
                chk = "Accessing DFC";
                //using (Stream stream = _me.GetManifestResourceStream("GamePatcher.res.patch.dfc"))
                string exefn = Application.ExecutablePath;
                if (!string.IsNullOrEmpty(Program.TARGET_EXE))
                    exefn = Program.TARGET_EXE;

                using (FileStream baseFStream = File.Open(exefn,
                    FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                    var stream = new StreamTruncate(baseFStream, L_CK + L_SZ);
                    stream.Seek(EXE_END, SeekOrigin.Begin);

                    chk = "Reading DFC header";
                    byte[] tmp = new byte[8];
                    stream.Read(tmp, 0, 4);
                    byte[] bheader = new byte[BitConverter.ToInt32(tmp, 0) - 4];
                    stream.Read(bheader, 0, bheader.Length);
                    MemoryStream msh = new MemoryStream(bheader);
                    msh.Read(tmp, 0, 4);

                    chk = "Parsing DFC header";
                    byte[][] filename = new byte[BitConverter.ToInt32(tmp, 0)][];
                    string[] files = new string[filename.Length];
                    long[] cLen = new long[filename.Length];
                    long[] eLen = new long[filename.Length];
                    int bgmPtr = 0;
                    toExtract = 0;

                    chk = "Parsing DFC header (segment 1)";
                    for (int a = 0; a < filename.Length; a++)
                    {
                        msh.Read(tmp, 0, 4);
                        filename[a] = new byte[BitConverter.ToInt32(tmp, 0)];
                    }
                    chk = "Parsing DFC header (segment 2)";
                    for (int a = 0; a < filename.Length; a++)
                    {
                        msh.Read(tmp, 0, 8);
                        cLen[a] = BitConverter.ToInt64(tmp, 0);
                        toExtract += cLen[a];
                    }
                    chk = "Parsing DFC header (segment 3)";
                    for (int a = 0; a < filename.Length; a++)
                    {
                        msh.Read(tmp, 0, 8);
                        eLen[a] = BitConverter.ToInt64(tmp, 0);
                    }
                    chk = "Parsing DFC header (segment 4)";
                    for (int a = 0; a < filename.Length; a++)
                    {
                        msh.Read(filename[a], 0, filename[a].Length);
                    }
                    chk = "Parsing DFC header (segment 5)";
                    for (int a = 0; a < filename.Length; a++)
                    {
                        files[a] = Encoding.UTF8.GetString(filename[a]).Replace('/', '\\');
                        int ofs = files[a].LastIndexOf('\\');
                        if (ofs > 0)
                        {
                            Directory.CreateDirectory(tempdir + files[a].Substring(0, ofs));
                        }
                    }
                    chk = "Parsing DFC header (segment 6)";
                    for (int a = 0; a < filename.Length; a++)
                    {
                        if (!files[a].StartsWith("nsf\\"))
                        {
                            bgmPtr = a;
                            break;
                        }
                    }
                    extracting = true;
                    chk = "Accessing XZ";
                    using (Stream xzstream = _me.GetManifestResourceStream("GamePatcher.res.xz.exe"))
                    {
                        chk = "Creating XZ target";
                        using (FileStream fso = new FileStream(tempdir + "xz.exe", FileMode.Create))
                        {
                            chk = "Transferring XZ stream";
                            xzstream.CopyTo(fso);
                        }
                    }
                    chk = "Preparing XZ proc";
                    Process proc = new Process();
                    proc.StartInfo.FileName = tempdir + "xz.exe";
                    proc.StartInfo.Arguments = "-dc -";
                    proc.StartInfo.RedirectStandardInput = true;
                    proc.StartInfo.RedirectStandardOutput = true;
                    proc.StartInfo.StandardOutputEncoding = Encoding.ASCII;
                    proc.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
                    proc.StartInfo.UseShellExecute = false;
                    proc.StartInfo.CreateNoWindow = true;
                    chk = "Starting XZ proc";
                    proc.Start();
                    new System.Threading.Thread(new System.Threading.ParameterizedThreadStart(delegate(object oo)
                    {
                        try
                        {
                            Stream s = (Stream)oo;
                            //Stream strm = new StreamTruncate(stream, L_CK + L_SZ);
                            //long remains = (s.Length - s.Position) - (L_CK + L_SZ);
                            byte[] cbuf = new byte[64 * 1024];
                            //while (remains > 0)
                            while (true)
                            {
                                //int i = stream.Read(cbuf, 0, (int)Math.Min(cbuf.Length, remains));
                                int i = stream.Read(cbuf, 0, cbuf.Length);
                                if (i <= 0) break;
                                s.Write(cbuf, 0, i);
                                progress = stream.Position * 1.0 / stream.Length;
                                //remains -= i;
                            }
                            //stream.CopyTo(s);
                            s.Flush();
                            s.Close();
                        }
                        catch (Exception ex)
                        {
                            MessageBox.Show("error while feeding xz:\r\n" + ex.Message);
                        }
                    })).Start(proc.StandardInput.BaseStream);

                    chk = "Extracting DFC payload";
                    var ebuf = new byte[64 * 1024];
                    for (int a = 0; a < filename.Length; a++)
                    {
                        chk = "Extracting DFC payload #" + a;
                        if (a == bgmPtr)
                        {
                            bgmReady = true;
                        }
                        using (FileStream fso = new FileStream(tempdir + files[a], FileMode.Create))
                        {
                            chk = "Flushing DFC payload #" + a;
                            long rem = eLen[a];
                            while (rem > 0)
                            {
                                int i = proc.StandardOutput.BaseStream.Read(ebuf, 0, (int)Math.Min(rem, ebuf.Length));
                                fso.Write(ebuf, 0, i);
                                rem -= i;
                            }
                        }
                    }
                    chk = "Finished";
                    extracting = false;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error when decompressing data:\r\n" + ex.Message + "\r\n\r\nLast checkpoint:\r\n" + chk);
            }
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            try
            {
                if (File.Exists("xz.exe"))
                    File.Delete("xz.exe");
            }
            catch { }
            try
            {
                this.Hide();
                Application.DoEvents();
                playNSF("end");
                System.Threading.Thread.Sleep(1500);
                killMusic();
            }
            catch { }
            System.Diagnostics.Process.GetCurrentProcess().Kill();
        }

        void contfocus()
        {
            _open.Focus();
            Timer t = new Timer();
            t.Interval = 100;
            t.Start();
            int i = 1;
            t.Tick += delegate(object oa, EventArgs ob)
            {
                if (--i < 0)
                    t.Stop();
                _open.Focus();
            };
        }
        string md5sum(string file)
        {
            return sum2text(md5sum(file, 0));
        }
        string sum2text(byte[] bytes)
        {
            StringBuilder sb = new StringBuilder();
            foreach (byte b in bytes)
            {
                sb.Append(b.ToString("x2"));
            }
            return sb.ToString();
        }
        byte[] md5sumNew(string file, int trim)
        {
            System.Security.Cryptography.MD5 md5 = new System.Security.Cryptography.MD5CryptoServiceProvider();
            using (FileStream fs = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                long hasRead = 0;
                long end = fs.Length - trim;
                byte[] buffer = new byte[8192];
                while (true)
                {
                    long i = fs.Read(buffer, 0, buffer.Length);
                    hasRead += i;
                    if (hasRead > end)
                    {
                        i -= hasRead - end;
                    }
                    md5.ComputeHash(buffer, 0, (int)i);
                    if (i <= 0 || hasRead >= end)
                    {
                        break;
                    }
                }
                return md5.Hash;
            }
        }
        byte[] md5buffer;
        byte[] md5sum(string file, int trim)
        {
            using (FileStream fs = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                Stream storm = null;
                if (trim != 0)
                {
                    //fs.SetLength(fs.Length - trim);
                    storm = new StreamTruncate(fs, trim);
                }
                else
                {
                    storm = fs;
                }
                md5buffer = new byte[0];
                new System.Threading.Thread(new System.Threading.ParameterizedThreadStart(md5worker)).Start(storm);

                while (md5buffer.Length == 0)
                    progress = storm.Position * 1.0 / storm.Length;

                //progress = -1;
                byte[] ret = new byte[md5buffer.Length];
                Array.Copy(md5buffer, ret, ret.Length);
                return ret;
            }
        }
        void md5worker(object o)
        {
            Stream storm = (Stream)o;
            System.Security.Cryptography.MD5 md5 = new System.Security.Cryptography.MD5CryptoServiceProvider();
            byte[] tmp = md5.ComputeHash(storm);
            md5buffer = tmp;
        }



        List<string> archivequeue;

        void recurse(string dir, List<string> lst)
        {
            foreach (string str in Directory.GetDirectories(dir))
            {
                recurse(str, lst);
            }
            lst.AddRange(Directory.GetFiles(dir));
        }

        void drecurse(string dir, List<string> lst)
        {
            foreach (string str in Directory.GetDirectories(dir))
            {
                drecurse(str, lst);
                lst.Add(str);
            }
        }

        string[] makeOrderLst(string isoPath)
        {
            var lines = new List<string>();
            using (FileStream isoStream = File.Open(isoPath, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                var cd = new DiscUtils.Iso9660.CDReader(isoStream, true);
                var di = new SortedDictionary<long, string>();
                recurse(cd, di, "");
                foreach (var node in di)
                    lines.Add(node.Value);
            }
            return lines.ToArray();
        }

        void recurse(DiscUtils.Iso9660.CDReader cd, SortedDictionary<long, string> dict, string root)
        {
            foreach (string dir in cd.GetDirectories(root))
                recurse(cd, dict, dir);

            foreach (string file in cd.GetFiles(root))
            {
                DiscUtils.StreamExtent[] range = cd.PathToExtents(file);

                if (range.Length > 1)
                    MessageBox.Show("your iso contains fragmented files,\r\nwhich is PROBABLY OK (cross your fingers)");

                if (dict.ContainsKey(range[0].Start))
                    MessageBox.Show("your iso is very interesting\r\n\r\n(interesting means broken)\r\n\r\nbut we would like to take a look at it,\r\nif you could send it over somehow");

                else
                    dict.Add(range[0].Start, file.TrimStart('\\'));
            }
        }

        bool rm_rf(string dir)
        {
            while (true)
            {
                for (int a = 0; a < 5; a++)
                {
                    try
                    {
                        if (Directory.Exists(dir))
                            Directory.Delete(dir, true);
                        return true;
                    }
                    catch
                    {
                        System.Threading.Thread.Sleep(100);
                    }
                }
                if (DialogResult.Cancel == MessageBox.Show(
                    "Can't delete the following folder, but will keep trying:\r\n\r\n" + dir,
                    "fucking windows", MessageBoxButtons.OKCancel, MessageBoxIcon.Warning))
                    System.Diagnostics.Process.GetCurrentProcess().Kill();
            }
        }

        void md5deep(string root, string saveAs)
        {
            var lst = new List<string>();
            recurse(root, lst);
            for (int a = 0; a < lst.Count; a++)
            {
                if (lst[a].Contains(@"SYSDIR\UPDATE\"))
                {
                    lst.RemoveAt(a--);
                    continue;
                }
                string tmp = md5sum(lst[a]);
                lst[a] = tmp + " " + lst[a].Substring(root.Length);
            }
            File.WriteAllLines(saveAs, lst.ToArray(), Encoding.UTF8);
        }

        void cdex(string isoPath, string outPath)
        {
            long tPos = 0;
            long tLen = new FileInfo(isoPath).Length;
            string[] files = makeOrderLst(isoPath);

            var buf = new byte[8192];
            var nul = new byte[8192];
            using (FileStream isoStream = File.Open(isoPath, FileMode.Open, FileAccess.Read, FileShare.Read))
            using (var cd = new DiscUtils.Iso9660.CDReader(isoStream, true))
            {
                foreach (var filename in files)
                {
                    string parent = filename.Substring(0, filename.LastIndexOf("\\") + 1);
                    string outFile = outPath + filename;
                    string outDir = outPath + parent;

                    if (filename.Contains(@"\UPDATE\"))
                        continue;

                    Directory.CreateDirectory(outDir);
                    using (Stream isoNode = cd.OpenFile(filename, FileMode.Open, FileAccess.Read))
                    using (FileStream fso = File.Open(outFile, FileMode.Create))
                    {
                        while (true)
                        {
                            progress = tPos * 1.0 / tLen;

                            int read = isoNode.Read(buf, 0, buf.Length);
                            if (read <= 0)
                                break;

                            fso.Write(buf, 0, read);
                            tPos += read;
                        }
                    }
                }
            }
            //progress = -1;
        }

        void st(string text)
        {
            this.Invoke((MethodInvoker)delegate
            {
                _installer.Text += DateTime.Now.ToLongTimeString() + "  " + text + "\r\n";
                _status.Text = text;
                if (_installer.Top + _installer.Height > creds.Top - 12)
                    creds.Visible = false;
            });
        }

        void runxd3(string exePath, string exeArgs, long len, bool creating)
        {
            Process proc = new Process();
            proc.StartInfo.FileName = exePath;
            proc.StartInfo.Arguments = exeArgs;
            proc.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
            proc.StartInfo.StandardErrorEncoding = Encoding.ASCII;
            proc.StartInfo.RedirectStandardError = true;
            proc.StartInfo.UseShellExecute = false;
            proc.StartInfo.CreateNoWindow = true;
            proc.Start();
            new System.Threading.Thread(new System.Threading.ParameterizedThreadStart(delegate(object oo)
            {
                Stream s = (Stream)oo;
                string pbuf = "";
                while (true)
                {
                    int c = s.ReadByte();
                    if (c < 0)
                        break;

                    if (c == '\n')
                    {
                        try
                        {
                            string line = pbuf;
                            pbuf = "";

                            int ofs = line.IndexOf(": total in ");
                            if (ofs < 0) continue;
                            line = line.Substring(ofs + 11);

                            if (!creating)
                            {
                                ofs = line.IndexOf(": out ");
                                if (ofs < 0) continue;
                                line = line.Substring(ofs + 6);
                            }

                            string[] items = line.Split(' ');
                            string num = items[0];
                            string def = items[1];
                            int mul = 1;
                            if (def == "KiB:") mul = 1024;
                            if (def == "MiB:") mul = 1024 * 1024;
                            if (def == "GiB:") mul = 1024 * 1024 * 1024;

                            double tmp = Convert.ToInt32(
                                line.Split(' ')[0].Split('.')[0].Split(',')[0]);

                            tmp = (tmp * mul) / len;
                            if (tmp >= 0 && tmp <= 1)
                                progress = tmp;
                        }
                        catch { }
                    }
                    else pbuf += (char)c;
                }
                //progress = -1;

            })).Start(proc.StandardError.BaseStream);
            proc.WaitForExit();
        }

        void runcso(string exePath, string exeArgs, bool creating, string outfile)
        {
            Process proc = new Process();
            proc.StartInfo.FileName = exePath;
            proc.StartInfo.Arguments = exeArgs;
            proc.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
            proc.StartInfo.UseShellExecute = false;
            proc.StartInfo.CreateNoWindow = true;
            proc.Start();
            while (!proc.HasExited)
            {
                try
                {
                    long sz = new FileInfo(outfile).Length;
                    progress = sz * (creating ? 1.45 : 1.0) / 785711104;
                }
                catch { }
                System.Threading.Thread.Sleep(100);
            }
        }

        void mkisofs(string exePath, string exeArgs)
        {
            StreamWriter logfile = null;
            //if (Program.HALT_CLEAN)
            //    logfile = new System.IO.StreamWriter(tempdir + "mk.log", false, Encoding.UTF8);

            Process proc = new Process();
            proc.StartInfo.FileName = exePath;
            proc.StartInfo.Arguments = exeArgs;
            proc.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
            proc.StartInfo.StandardErrorEncoding = Encoding.ASCII;
            proc.StartInfo.RedirectStandardError = true;
            proc.StartInfo.UseShellExecute = false;
            proc.StartInfo.CreateNoWindow = true;
            if (Program.HALT_CLEAN)
            {
                proc.StartInfo.StandardOutputEncoding = Encoding.ASCII;
                proc.StartInfo.RedirectStandardOutput = true;
            }
            proc.Start();
            if (Program.HALT_CLEAN)
            {
                MessageBox.Show("STDERR:\r\n" + proc.StandardError.ReadToEnd());
                MessageBox.Show("STDOUT:\r\n" + proc.StandardOutput.ReadToEnd());
            }
            else
                new System.Threading.Thread(new System.Threading.ParameterizedThreadStart(delegate(object oo)
                {
                    Stream s = (Stream)oo;
                    string pbuf = "";
                    while (true)
                    {
                        int c = s.ReadByte();
                        if (c < 0)
                            break;

                        if (c == '\n')
                        {
                            try
                            {
                                if (logfile != null)
                                    logfile.WriteLine(pbuf);

                                string line = pbuf;
                                pbuf = "";

                                int ofs = line.IndexOf("% done, estimate finish");
                                if (ofs < 0) continue;

                                int ofs1 = line.IndexOf(".");
                                int ofs2 = line.IndexOf(",");

                                if (ofs1 < 0) ofs = ofs2;
                                else if (ofs2 < 0) ofs = ofs1;
                                else ofs = Math.Min(ofs1, ofs2);

                                line = line.Substring(0, ofs).Trim();
                                progress = int.Parse(line) * 0.01;
                            }
                            catch { }
                        }
                        else pbuf += (char)c;
                    }
                    //progress = -1;

                })).Start(proc.StandardError.BaseStream);

            proc.WaitForExit();
        }

        void copyshit(DirectoryInfo source, DirectoryInfo target)
        {
            foreach (DirectoryInfo dir in source.GetDirectories())
                copyshit(dir, target.CreateSubdirectory(dir.Name));
            foreach (FileInfo file in source.GetFiles())
                if (file.Name != "xz.exe")
                    file.CopyTo(Path.Combine(target.FullName, file.Name));
        }

        long bytesCompressed = 0;
        long bytesToCompress = 1;
        void patchthread()
        {
            bool entireiso = DialogResult.Yes == MessageBox.Show(
                "Create xdelta3 patch of entire ISO?\r\n\r\n" +
                "Will not be embedded into patcher",
                "extra step?", MessageBoxButtons.YesNo);

            Process proc;
            progressn = 7;
            progressi = 0;
            bool full = true;

            if (full)
            {
                if (!Directory.Exists(Application.StartupPath + @"\snw_gp_archive"))
                {
                    st("unpacking resources");
                    exthread();
                    copyshit(
                        new DirectoryInfo(tempdir),
                        new DirectoryInfo(Application.StartupPath + @"\snw_gp_archive"));
                }
            }

            if (full)
            {
                rm_rf("tmp1");
                rm_rf("tmp2");

                if (!testdisk(1353887))
                {
                    exit();
                    return;
                }
                
                progress = 0;
                progressi = 0;
                st("unpack, original iso");
                cdex(@"orig.iso", @"tmp1\");

                progress = 0;
                progressi = 1;
                st("unpack, okay iso");
                cdex(@"okay.iso", @"tmp2\");

                st("decrypt eboot.bin");
                decryptEboot(@"tmp1\PSP_GAME\SYSDIR\EBOOT.BIN",
                    "Something went wrong while decrypting the eboot.bin in the orig.iso! " +
                    "This is gonna be messy if your translation project needs to modify " +
                    "the main game binary. RIP\r\n\r\nError message: ");
                decryptEboot(@"tmp2\PSP_GAME\SYSDIR\EBOOT.BIN", null);

                if (DialogResult.OK != MessageBox.Show(
                    "orig.iso  extracted to tmp1\r\nokay.iso extracted to tmp2\r\n\r\n" +
                    "this is your chance to modify the contents of tmp2,\r\n" +
                    "all changes will be included in the generated patcher.\r\n\r\n" +
                    "Please don't add new files,\r\nand don't remove existing files!\r\n\r\n" +
                    "Press OK when you've made your changes\r\nand you're ready to continue",
                    "this is it", MessageBoxButtons.OKCancel, MessageBoxIcon.Information))
                    System.Diagnostics.Process.GetCurrentProcess().Kill();

                progress = 0;
                progressi = 2;
                st("checksums, original iso");
                md5deep(@"tmp1\", @"snw_gp_archive\orig.md5");

                progress = 0;
                progressi = 3;
                st("checksums, okay iso");
                md5deep(@"tmp2\", @"snw_gp_archive\okay.md5");
            }

            if (full)
            {
                var mods = new List<string>();
                string[] sum1 = File.ReadAllLines(@"snw_gp_archive\orig.md5", Encoding.UTF8);
                string[] sum2 = File.ReadAllLines(@"snw_gp_archive\okay.md5", Encoding.UTF8);
                foreach (string str in sum2)
                    if (!sum1.Contains(str))
                        mods.Add(str);

                File.WriteAllLines(@"snw_gp_archive\mods.md5", mods.ToArray(), Encoding.UTF8);

                int n = 0;
                progress = 0;
                progressi = 4;
                foreach (string str in mods)
                {
                    string fn = str.Substring(33);
                    string xd = @"snw_gp_archive\" + (n++) + ".xd3";

                    st("make xd3 of " + fn);
                    if (File.Exists(xd))
                        File.Delete(xd);
                    runxd3(
                        @"snw_gp_archive\bin\xdelta3.exe",
                        string.Format(
                            "-v -e -s \"{0}\" \"{1}\" \"{2}\"",
                            @"tmp1\" + fn,
                            @"tmp2\" + fn, xd
                        ),
                        new FileInfo(@"tmp1\" + fn).Length, true
                    );
                }

                while (true)
                {
                    string xfn = @"snw_gp_archive\" + (n++) + ".xd3";
                    if (!File.Exists(xfn))
                        break;
                    File.Delete(xfn);
                }

                if (entireiso)
                {
                    progress = 0;
                    progressi = 5;
                    st("make xd3, entire iso");
                    if (File.Exists("okay.xd3"))
                        File.Delete("okay.xd3");
                    runxd3(
                        @"snw_gp_archive\bin\xdelta3.exe",
                        "-v -e -s orig.iso okay.iso okay.xd3",
                        new FileInfo("orig.iso").Length, true
                    );
                }
            }

            if (full)
            {
                progress = 0;
                progressi = 6;
                st("creating dfc");
                archivequeue = new List<string>();
                string src = Path.GetFullPath(@"snw_gp_archive\");
                recurse(src, archivequeue);
                for (int a = 1; a < archivequeue.Count; a++)
                {
                    if (archivequeue[a].Contains(@"\nsf\"))
                    {
                        var v = archivequeue[a];
                        archivequeue.RemoveAt(a);
                        archivequeue.Insert(0, v);
                    }
                }
                string[] files = archivequeue.ToArray();
                for (int a = 0; a < files.Length; a++)
                {
                    files[a] = files[a].Substring(src.Length).Replace('\\', '/');
                }

                int filenameslength = 0;
                long[] cLen = new long[files.Length];
                long[] eLen = new long[files.Length];
                byte[][] filename = new byte[files.Length][];
                for (int a = 0; a < files.Length; a++)
                {
                    eLen[a] = new FileInfo(src + files[a]).Length;
                    filename[a] = Encoding.UTF8.GetBytes(files[a]);
                    filenameslength += filename[a].Length;
                    bytesToCompress += eLen[a];
                }

                byte[] buffer = new byte[8192];
                byte[] header = new byte[
                                   4 + // header     length
                                   4 + // file       count
                    files.Length * 4 + // filename   length
                    files.Length * 8 + // compressed length
                    files.Length * 8 + // extracted  length
                    filenameslength
                ];
                for (int a = 0; a < header.Length; a++)
                {
                    header[a] = 0xFF;
                }

                var buf = new byte[64 * 1024];
                using (Stream stream = _me.GetManifestResourceStream("GamePatcher.res.xz.exe"))
                {
                    using (FileStream fso = new FileStream("xz.exe", FileMode.Create))
                    {
                        stream.CopyTo(fso);
                    }
                }
                proc = new Process();
                proc.StartInfo.FileName = @"xz.exe";
                proc.StartInfo.Arguments = "-zc -";
                proc.StartInfo.RedirectStandardInput = true;
                proc.StartInfo.RedirectStandardOutput = true;
                proc.StartInfo.StandardOutputEncoding = Encoding.ASCII;
                proc.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
                proc.StartInfo.UseShellExecute = false;
                proc.StartInfo.CreateNoWindow = true;
                proc.Start();
                new System.Threading.Thread(new System.Threading.ParameterizedThreadStart(delegate(object oo)
                {
                    using (FileStream fso = new FileStream(@"patch.dfc", FileMode.Create))
                    {
                        fso.Write(header, 0, header.Length);
                        Stream s = (Stream)oo;
                        s.CopyTo(fso);
                        s.Flush();
                        s.Close();
                    }
                })).Start(proc.StandardOutput.BaseStream);

                for (int a = 0; a < files.Length; a++)
                {
                    using (FileStream fsi = new FileStream(src + files[a], FileMode.Open, FileAccess.Read, FileShare.Read))
                    {
                        var ebuf = new byte[64 * 1024];
                        while (true)
                        {
                            int i = fsi.Read(ebuf, 0, ebuf.Length);
                            if (i <= 0) break;
                            bytesCompressed += i;
                            progress = bytesCompressed * 1.0 / bytesToCompress;
                            proc.StandardInput.BaseStream.Write(ebuf, 0, i);
                        }
                    }
                }
                proc.StandardInput.Flush();
                proc.StandardInput.Close();
                proc.WaitForExit();

                using (MemoryStream msh = new MemoryStream(header.Length))
                {
                    msh.Write(BitConverter.GetBytes((Int32)header.Length), 0, 4);
                    msh.Write(BitConverter.GetBytes((Int32)files.Length), 0, 4);

                    foreach (byte[] fn in filename)
                        msh.Write(BitConverter.GetBytes((Int32)fn.Length), 0, 4);

                    foreach (long cLn in cLen)
                        msh.Write(BitConverter.GetBytes((Int64)cLn), 0, 8);

                    foreach (long eLn in eLen)
                        msh.Write(BitConverter.GetBytes((Int64)eLn), 0, 8);

                    foreach (byte[] fn in filename)
                        msh.Write(fn, 0, fn.Length);

                    using (FileStream fso = new FileStream(@"patch.dfc", FileMode.Open, FileAccess.Write))
                    {
                        fso.Seek(0, SeekOrigin.Begin);
                        msh.Seek(0, SeekOrigin.Begin);
                        msh.WriteTo(fso);
                    }
                }
            }

            string outexe = "/dev/null";
            if (true)
            {
                outexe = "snw-psp-" + DateTime.UtcNow.ToString("yyyy-MMdd-HHmmss") + ".exe";
                st("write " + outexe);
                progress = -1;
                using (FileStream fso = new FileStream(outexe, FileMode.Create))
                {
                    using (FileStream fsi = new FileStream(Application.ExecutablePath,
                        FileMode.Open, FileAccess.Read, FileShare.Read))
                    {
                        Stream strm = fsi;
                        if (EXE_END > 0)
                            strm = new StreamTruncate(fsi, fsi.Length - EXE_END);
                        else EXE_END = fsi.Length;

                        //long remains = EXE_END > 0 ? EXE_END : fsi.Length;
                        byte[] buf = new byte[8192];
                        //while (remains > 0)
                        while (true)
                        {
                            //int read = fsi.Read(buf, 0, (int)Math.Min(buf.Length, remains));
                            int read = strm.Read(buf, 0, buf.Length);
                            if (read <= 0) break;
                            fso.Write(buf, 0, read);
                            //remains -= read;
                        }
                    }
                    using (FileStream fsi = new FileStream("patch.dfc",
                        FileMode.Open, FileAccess.Read, FileShare.Read))
                    {
                        fsi.CopyTo(fso);
                    }
                    byte[] len = BitConverter.GetBytes(EXE_END);
                    len = md5xor(len);
                    fso.Write(len, 0, len.Length);
                }
                st("checksum " + outexe);
                byte[] cksum = md5xor(md5sum(outexe, 0));
                using (FileStream fso = new FileStream(outexe, FileMode.Append))
                {
                    fso.Seek(0, SeekOrigin.End);
                    fso.Write(cksum, 0, cksum.Length);
                }
            }

            string crc = "deadbeef";
            using (FileStream fs = new FileStream(outexe, FileMode.Open, FileAccess.Read, FileShare.Read))
                crc = sum2text(new Crc32().ComputeHash(fs)).ToUpper();

            string pver = "";
            this.Invoke((MethodInvoker)delegate { pver = label7.Text; });
            string scene = "[OK]_Sound_of_the_Sky_Quintet_of_Maidens_[TLPatch_" + pver + "][" + crc + "].exe";
            while (File.Exists(scene))
                scene += ".exe";
            File.Move(outexe, scene);
            outexe = scene;

            st("done");
            progress = -1;
            MessageBox.Show("new patcher saved as:\r\n\r\n" + outexe);
            exit();
        }

        private void xor2(byte[] buffer, params byte[] crypt)
        {
            for (int a = 0; a < buffer.Length; a++)
            {
                buffer[a] ^= crypt[a % crypt.Length];
            }
        }
        void muset(object l)
        {
            foreach (var c in p_music.Controls)
            {
                if (typeof(Label) == c.GetType() &&
                    c != label20)
                {
                    ((Label)c).Font = label20.Font;
                    ((Label)c).ForeColor = Color.Gray;
                }
            }
            ((Label)l).ForeColor = SystemColors.ControlText;
            ((Label)l).Font = new System.Drawing.Font(label20.Font, FontStyle.Underline);
            if (!showmus)
            {
                _team.Height += _bgma.Top - label17.Top;
                showmus = _bgma.Visible = _bgmb.Visible = true;
            }
        }
        private void mu_nope_Click(object sender, EventArgs e)
        {
            killMusic();
            muset(sender);
            showmus = _bgma.Visible = _bgmb.Visible = false;
            _team.Height -= _bgma.Top - label17.Top;
        }
        private void mu_grays_Click(object sender, EventArgs e)
        {
            playNSF("grays");
            _bgma.Text = "Patcher BGM";
            _bgmb.Text = "tripflag - Rebasing Grays";
            muset(sender);
        }

        private void mu_nyaruko_Click(object sender, EventArgs e)
        {
            playNSF("nudzi_mi_sie");
            _bgma.Text = "Patcher BGM";
            _bgmb.Text = "Milos - Nudzi Mi Sie";
            muset(sender);
        }

        private void mu_disco_Click(object sender, EventArgs e)
        {
            playNSF("famicom_disco");
            _bgma.Text = "Patcher BGM";
            _bgmb.Text = "Im_a_Track_Man - Famikon Disuko";
            muset(sender);
        }

        void web()
        {
            try
            {
                System.Diagnostics.Process proc = new Process();
                proc.StartInfo.FileName = "https://ocv.me/snw";
                proc.Start();
                Application.DoEvents();
                System.Threading.Thread.Sleep(1000);
            }
            catch { MessageBox.Show("error"); }
            exit();
        }

        private void Form1_DragOver(object sender, DragEventArgs e)
        {
            e.Effect = DragDropEffects.All;
        }

        private void Form1_DragDrop(object sender, DragEventArgs e)
        {
            openevent((string[])e.Data.GetData(DataFormats.FileDrop));
        }

        private void Form1_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.O && e.Control)
                _open_Click(sender, e);
        }

        private void _open_Click(object sender, EventArgs e)
        {
            var ofd = new OpenFileDialog();
            ofd.Filter =
                "ISO or CSO|*.iso;*.cso|" +
                "Regular ISO (*.iso)|*.iso|" +
                "Compressed ISO (*.cso)|*.cso";

            ofd.Title = "Select the original ISO";
            if (DialogResult.OK == ofd.ShowDialog())
                openevent(ofd.FileNames);
        }

        void openevent(string[] files)
        {
            openqueue = files;
            opentimer.Stop();
            opentimer.Start();
            p_music.SendToBack();
            _pane1.SendToBack();
            creds.Visible = true;
        }

        void opentimer_Tick(object sender, EventArgs e)
        {
            opentimer.Stop();
            openISO(openqueue);
        }

        void openISO(string[] files)
        {
            if (files.Length < 1)
            {
                MessageBox.Show("You need to select an ISO or CSO file to patch");
                return;
            }
            if (files.Length > 1)
            {
                MessageBox.Show("Only select one ISO or CSO file; the VN to translate");
                return;
            }
            if (!File.Exists(files[0]))
            {
                MessageBox.Show("The file you selected does not exist...? " +
                    "Yeah, this is a bug.\r\n\r\nTried to load [" + files[0] + "]");
                return;
            }
            bool iso = files[0].ToLower().EndsWith(".iso");
            bool cso = files[0].ToLower().EndsWith(".cso");
            if (!iso && !cso)
            {
                MessageBox.Show(
                    "I only understand ISO and CSO files :(\r\n\r\n" +
                    "if your VN is compressed (zip/rar/7z files) please unpack it first.");
                return;
            }
            try
            {
                using (FileStream fsi = new FileStream(files[0], FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                    if (iso)
                    {
                        fsi.Seek(0x8001, SeekOrigin.Begin);
                        byte[] isobuf = new byte[5];
                        fsi.Read(isobuf, 0, isobuf.Length);
                        string isostr = Encoding.ASCII.GetString(isobuf);
                        if (isostr != "CD001")
                            throw new Exception();
                    }
                    if (cso)
                    {
                        byte[] isobuf = new byte[4];
                        fsi.Read(isobuf, 0, isobuf.Length);
                        string isostr = Encoding.ASCII.GetString(isobuf);
                        if (isostr != "CISO")
                            throw new Exception();
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "I only understand ISO and CSO files :(\r\n\r\n" +
                    "And even though your file extension claims otherwise, this is not a valid file.\r\n\r\n" +
                    "if your VN is compressed (zip/rar/7z files) please unpack it first.");
                return;
            }
            Program.SOURCE_ISO = files[0];
            MessageBox.Show("VN loaded.  In the next window,\r\nselect where to save the translated ISO.\r\n\r\n" +
                "Protip: Select the CSO file extension to create a 513 MB\r\n" +
                "compressed ISO which works on most emulators and real PSPs");

            SaveFileDialog sfd = new SaveFileDialog();
            sfd.Filter =
                "Regular ISO (*.iso)|*.iso|" +
                "Compressed ISO (*.cso)|*.cso";

            sfd.FileName = "patched.iso";
            sfd.Title = "Save translated ISO";
            if (DialogResult.OK != sfd.ShowDialog())
                return;

            string ofn = sfd.FileName;
            if (File.Exists(ofn))
                File.Delete(ofn);
            if (File.Exists(ofn))
            {
                MessageBox.Show("Could not overwrite the output ISO file! Aborting.");
                return;
            }

            new System.Threading.Thread(new
                System.Threading.ParameterizedThreadStart(patcher)
                ).Start(new string[] { files[0], ofn });
        }

        void cleanup()
        {
            cleanup(false);
        }
        void cleanup(bool all)
        {
            try
            {
                var lst = new List<string>();
                recurse(tempdir, lst);

                foreach (string item in lst)
                    if (!item.Contains(@"\nsf\") || all)
                        try
                        {
                            File.Delete(item);
                        }
                        catch { }

                lst.Clear();
                drecurse(tempdir, lst);

                for (int a = 0; a < 2; a++)
                    foreach (string item in lst)
                        if (!item.Contains(@"\nsf\") || all)
                            try
                            {
                                if (Directory.Exists(item))
                                    Directory.Delete(item);
                            }
                            catch { }
            }
            catch { }
        }

        void exit()
        {
            this.Invoke((MethodInvoker)delegate { this.Close(); });
        }

        void patcher(object oarg)
        {
            string[] argv = (string[])oarg;

            if (EXE_END < 0)
                tempdir = Application.StartupPath + @"\snw_gp_archive\";

            //Program.popception();

            string psp = tempdir + "i\\";
            string order = tempdir + "t\\order.lst";
            string muser = tempdir + "t\\user.md5";
            string org = argv[0];
            string res = argv[1];
            string is1 = org;
            string is2 = res;
            string ext1 = org.ToLower().Substring(org.Length - 3);
            string ext2 = res.ToLower().Substring(res.Length - 3);

            rm_rf(tempdir + "t");
            rm_rf(tempdir + "i");
            Directory.CreateDirectory(tempdir + "t");
            Directory.CreateDirectory(tempdir + "i");
            string[] origMD5 = File.ReadAllLines(tempdir + "orig.md5");
            string[] okayMD5 = File.ReadAllLines(tempdir + "okay.md5");
            string[] modsMD5 = File.ReadAllLines(tempdir + "mods.md5");
            progressi = 0;
            progressn = 5;
            progress = -1;

            int spaceNeeded = 1357528;
            /* if (tempdir.Substring(0, 2) != org.Substring(0, 2))
            {
                spaceNeeded -= 662016; // patched iso
                spaceNeeded += 628590; // afs dupe
            } */

            if (ext2 == "cso")
            {
                progressn++;
                spaceNeeded += 525796;
                is2 = tempdir + @"t\okay.iso";
            }
            if (ext1 == "cso")
            {
                progressn++;
                spaceNeeded += 767296;
                is1 = tempdir + @"t\orig.iso";
            }

            if (!testdisk(spaceNeeded))
            {
                exit();
                return;
            }

            if (ext1 == "cso")
            {
                st((progressi + 1) + "/" + progressn + ". Decompressing your " + ext1);
                runcso(
                    tempdir + @"\bin\ciso.exe", string.Format(
                    "0 \"{0}\" \"{1}\"", org, is1), false, is1);

                progress = 0;
                ++progressi;
            }



            st((progressi + 1) + "/" + progressn + ". Extracting VN files");
            cdex(is1, psp);
            string ebootBase = @"PSP_GAME\SYSDIR\EBOOT.BIN";
            string ebootOrig = psp + ebootBase;
            string ebootDecr = psp + ebootBase + "2";
            string ebootMD5 = md5sum(ebootOrig);
            if (!origMD5.Contains(ebootMD5 + " " + ebootBase))
            {
                try
                {
                    using (FileStream encfs = File.Open(ebootOrig, FileMode.Open, FileAccess.Read, FileShare.Read))
                    using (FileStream decfs = File.Open(ebootDecr, FileMode.Create))
                        new PSPFormatDecryptor(encfs).Decrypt(decfs);
                    // then check if the md5sum matches
                    // (assumes that the ISO images provided when creating the patch were both decrypted)
                    ebootMD5 = md5sum(ebootDecr);
                    if (origMD5.Contains(ebootMD5 + " " + ebootBase))
                    {
                        File.Delete(ebootOrig);
                        File.Move(ebootDecr, ebootOrig);
                    }
                    else File.Delete(ebootDecr);
                }
                catch (Exception ex)
                {
                    try
                    {
                        File.Delete(ebootDecr);
                    }
                    catch { }
                    MessageBox.Show(
                        "Something happened! The translated VN will work fine, " +
                        "but could you send us this message? Or actually, could we " +
                        "have the iso file you just used as well?\r\n\r\n" +
                        ex.Message + "\r\n\r\n" + ex.StackTrace);
                }
            }
            // if the checksum doesn't match at this point,
            // skip the file during patching below
            progress = 0;
            ++progressi;



            st((progressi + 1) + "/" + progressn + ". Verifying VN files");
            md5deep(psp, muser);
            string missing = "";
            string[] userMD5 = File.ReadAllLines(muser, Encoding.UTF8);
            foreach (string md5 in origMD5)
                if (!userMD5.Contains(md5))
                    missing += md5 + "\r\n";

            if (missing.Contains("data.afs"))
            {
                MessageBox.Show(
                    "Your ISO / CSO file is incompatible!\r\nPlease send it to us, so we can have a look.",
                    "Critical error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                exit();
                return;
            }
            if (!string.IsNullOrEmpty(missing))
            {
                if (DialogResult.Cancel == MessageBox.Show(
                    "Your ISO / CSO is not quite what we expected to see.\r\nHowever, nothing too important " +
                    "seems to be amiss...\r\nso it's PROBABLY fine (no guarantees)\r\n\r\n" + missing.Replace(" ", "_"),
                    "Warning", MessageBoxButtons.OKCancel, MessageBoxIcon.Warning))
                {
                    exit();
                    return;
                }
            }
            progress = 0;
            ++progressi;



            st((progressi + 1) + "/" + progressn + ". Patching stuff");
            int n = 0;
            foreach (string md5 in modsMD5)
            {
                string fn = md5.Substring(33);
                string xd = tempdir + (n++) + ".xd3";

                // check md5 of user's file before trying to patch it
                string thisMD5 = "fgsfds";
                foreach (string testMD5 in userMD5)
                    if (testMD5.Contains(fn))
                        thisMD5 = testMD5.Substring(0, 32);

                if (!origMD5.Contains(thisMD5 + " " + fn))
                {
                    MessageBox.Show("Could not patch the following file, as you seem to have a different version:\r\n\r\n" + fn + "\r\n\r\nThis means that some tiny parts of the VN will not be translated, but everything should work just fine otherwise.\r\n\r\nAlthough if you could send us the ISO you just used, that would be great!");
                    continue;
                }

                runxd3(
                    tempdir + @"\bin\xdelta3.exe",
                    string.Format(
                        "-v -d -s \"{0}\" \"{1}\" \"{2}\"",
                        psp + fn, xd, psp + "xd3out"
                    ),
                    new FileInfo(psp + fn).Length, false
                );
                File.Delete(psp + fn);
                File.Move(psp + "xd3out", psp + fn);
            }
            progress = 0;
            ++progressi;



            st((progressi + 1) + "/" + progressn + ". Verifying patch");
            missing = "";
            foreach (string entry in modsMD5)
            {
                string fn = entry.Substring(33);
                string md5 = entry.Substring(0, 32);
                string cur = md5sum(psp + fn);
                if (md5 != cur)
                    missing += fn + "_(" + cur + ")\r\n";
            }
            if (!string.IsNullOrEmpty(missing))
            {
                if (DialogResult.Cancel == MessageBox.Show(
                    "The following files didn't patch properly,\r\n" +
                    "but the translated iso MAY work anyways:\r\n" + missing,
                    "ah shit", MessageBoxButtons.OKCancel, MessageBoxIcon.Warning))
                {
                    exit();
                    return;
                }
            }
            progress = 0;
            ++progressi;



            st((progressi + 1) + "/" + progressn + ". Creating ISO spec");
            var proc = new System.Diagnostics.Process();
            proc.StartInfo.FileName = tempdir + @"\bin\isoinfo.exe";
            proc.StartInfo.Arguments = "-f -i \"" + is1 + "\"";
            proc.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
            proc.StartInfo.StandardOutputEncoding = Encoding.ASCII;
            proc.StartInfo.RedirectStandardOutput = true;
            proc.StartInfo.UseShellExecute = false;
            proc.StartInfo.CreateNoWindow = true;
            proc.Start();

            string[] isoinfo = proc.StandardOutput.ReadToEnd().Trim().Split('\n');
            proc.WaitForExit();
            for (int a = 0; a < isoinfo.Length; a++)
                isoinfo[a] = isoinfo[a].Trim() + " -" + (a + 1);
            File.WriteAllLines(order, isoinfo, Encoding.ASCII);

            st((progressi + 1) + "/" + progressn + ". Creating ISO image");
            string mkisofsCmd = string.Format(
                "-sort \"{0}\" -iso-level 4 -xa -A \"PSP GAME\" -V SNW_PSP " +
                "-sysid \"PSP GAME\" -volset \"SNW_PSP\" -p SNW -o \"{1}\" \"{2}\"",
                order, is2, psp.TrimEnd('\\'));
            if (Program.HALT_CLEAN)
                MessageBox.Show(mkisofsCmd);

            mkisofs(tempdir + @"\bin\mkisofs.exe", mkisofsCmd);
            progress = 0;
            ++progressi;

            if (ext2 == "cso")
            {
                st((progressi + 1) + "/" + progressn + ". Compressing to " + ext2);

                runcso(
                    tempdir + @"\bin\ciso.exe", string.Format(
                    "9 \"{0}\" \"{1}\"", is2, res), true, res);
            }

            if (Program.HALT_CLEAN)
                MessageBox.Show("about to clean");

            new System.Threading.Thread(new System.Threading.ThreadStart(cleanup)).Start();

            st("done");
            progress = -1;
            //p_music.BringToFront();
            MessageBox.Show("All done! Enjoy the yuri  :^)");
            exit();
        }

        private void _installer_Click(object sender, EventArgs e)
        {
            _installer.BackColor = Color.Black;
            _installer.ForeColor = Color.Green;
        }

        bool testdisk(int spaceNeeded)
        {
            string drivename =
                string.IsNullOrWhiteSpace(tempdir) ?
                Application.StartupPath : tempdir;

            drivename = drivename.Substring(0, 1) + ":\\";

            long spaceFree = 0;
            foreach (var drive in DriveInfo.GetDrives())
            {
                if (drive.IsReady && drive.Name == drivename)
                {
                    spaceFree = drive.TotalFreeSpace / 1024;
                }
            }
            if (spaceFree <= spaceNeeded)
            {
                if (DialogResult.OK != MessageBox.Show(string.Format(
                    "I need to borrow {1} megabyte of space on your {0} drive for this.\r\n" +
                    "Don't worry, you'll get it back once I'm finished!\r\n" +
                    "Except, it looks like you only have {2} megabyte free...\r\n\r\n" +
                    "This probably won't work!  Continue anyways?",
                    drivename, (spaceNeeded / 1024), (spaceFree / 1024)),
                    "Low disk space", MessageBoxButtons.OKCancel, MessageBoxIcon.Warning))
                    return false;
            }
            return true;
        }
    }
}
