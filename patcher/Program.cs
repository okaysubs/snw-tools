using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;
using System.IO;
using System.Security.Cryptography;

/* GamePatcher SNW Edition v1.0
 * MIT-Licensed, 2016-05-06, ed <irc.rizon.net>
 * https://github.com/okaysubs/snw-tools
 */

namespace GamePatcher
{
    static class Program
    {
        public static string TARGET_EXE;
        public static string SOURCE_ISO;
        public static bool HALT_CLEAN;
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        [System.Runtime.ExceptionServices.HandleProcessCorruptedStateExceptions]
        static void Main(string[] args)
        {
            bool eh = true;
            TARGET_EXE = "";
            SOURCE_ISO = "";
            HALT_CLEAN = false;

            foreach (string arg in args)
            {
                if (arg == "exceptions")
                    eh = false;

                else if (arg == "haltclean")
                    HALT_CLEAN = true;

                else if (arg.ToLower().EndsWith(".exe"))
                    TARGET_EXE = arg;

                else if (arg.ToLower().EndsWith(".iso"))
                    SOURCE_ISO = arg;

                else if (DialogResult.No == MessageBox.Show(
                        "You dropped a file onto the .exe that\r\n" +
                        "I don't know what do to with. Continue?\r\n\r\n" +
                        args[0], "What", MessageBoxButtons.YesNo, MessageBoxIcon.Warning))
                    System.Diagnostics.Process.GetCurrentProcess().Kill();
            }

            if (eh)
            {
                AppDomain.CurrentDomain.UnhandledException += (ueSender, ueArgs) =>
                        new UI_Exception(ueArgs.ExceptionObject as Exception, 1).ShowDialog();

                Application.ThreadException += (ueSender, ueArgs) =>
                    new UI_Exception(ueArgs.Exception, 2).ShowDialog();

                Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
            }

            if (!string.IsNullOrEmpty(TARGET_EXE))
            {
                if (DialogResult.No == MessageBox.Show(
                    "Will read patch data from the .exe file that you\r\n" +
                    "dropped onto this patcher. Continue?\r\n\r\n" + TARGET_EXE,
                    "Unpacker input", MessageBoxButtons.YesNo, MessageBoxIcon.Question))
                    System.Diagnostics.Process.GetCurrentProcess().Kill();
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Form1());
        }

        public static void popception(int lv = 1)
        {
            bool cu = false;
            try
            {
                if (lv == 6)
                {
                    throw new Exception("hit lv");
                }
                popception(lv + 1);
            }
            finally
            {
                cu = true;
            }
        }
    }

    public class StreamTruncate : Stream
    {
        long len;
        Stream stream;
        public StreamTruncate(Stream stream, long trim)
        {
            len = stream.Length - trim;
            this.stream = stream;
        }
        public override int Read(byte[] buffer, int offset, int count)
        {
            long i = stream.Read(buffer, offset, count);
            if (stream.Position >= len)
            {
                i -= stream.Position - len;
            }
            return (int)Math.Max(0, i);
        }
        public override bool CanRead { get { return stream.CanRead; } }
        public override bool CanSeek { get { return stream.CanSeek; } }
        public override bool CanWrite { get { return stream.CanWrite; } }
        public override void Flush()
        {
            stream.Flush();
        }
        public override long Length { get { return len; } }
        public override long Position
        {
            get
            {
                return stream.Position;
            }
            set
            {
                stream.Position = value;
            }
        }
        public override long Seek(long offset, System.IO.SeekOrigin origin)
        {
            return stream.Seek(offset, origin);
        }
        public override void SetLength(long value)
        {
            throw new NotImplementedException();
        }
        public override void Write(byte[] buffer, int offset, int count)
        {
            throw new NotImplementedException();
        }
    }

    class PSPFormatDecryptor
    {
        public static readonly uint PSP_MAGIC = 0x5053507E; // "~PSP"
        public static readonly uint PSP_HEADER_SIZE = 336;

        protected class DecryptionHeader
        {
            public byte[] KeyData { get; set; }
            public byte[] UserKey { get; set; }
            public byte[] Hash { get; set; }
            public byte[] CMACKey { get; set; }
            public uint Tag { get; set; }
            public uint Size { get; set; }
            public uint Offset { get; set; }
        }

        private Stream input;
        private LittleEndianReader reader;


        public PSPFormatDecryptor(Stream input)
        {
            this.input = input;
            this.reader = new LittleEndianReader(this.input);
        }

        public void Decrypt(Stream output)
        {
            DecryptionHeader header;
            KeyInfo mainKey;
            byte[] scrambleKey, derivedKey;

            // Parse header and retrieve key.
            this.input.Seek(0, SeekOrigin.Begin);
            header = this.ParseHeader();

            try
            {
                mainKey = KeyStorage.KEYS[header.Tag];
            }
            catch (KeyNotFoundException)
            {
                throw new InvalidOperationException(String.Format("Missing key for tag {0:x} in key storage.", header.Tag));
            }
            this.input.Seek(header.Offset, SeekOrigin.Begin);

            try
            {
                scrambleKey = KeyStorage.SCRAMBLE_KEYS[mainKey.ScrambleType];
            }
            catch (KeyNotFoundException)
            {
                throw new InvalidOperationException(String.Format("Missing descramble key for code 0x{0:x} in key storage.", mainKey.ScrambleType));
            }

            // Get derived key.
            int keyLength = mainKey.Key.Length;
            derivedKey = new byte[9 * keyLength];
            for (int i = 0; i < 9; i++)
            {
                Array.Copy(mainKey.Key, 0, derivedKey, i * keyLength, keyLength);
                derivedKey[i * keyLength] = (byte)i;
            }
            this.DecryptRound(derivedKey, 0, (uint)(9 * keyLength), derivedKey, 0, scrambleKey);

            // Recreate part of header to decrypt it.
            byte[] origHeader = new byte[0x60];
            int offset = 0;
            offset = this.AppendBuffer(header.KeyData, origHeader, offset);
            offset = this.AppendBuffer(header.Hash, origHeader, offset);
            offset = this.AppendBuffer(header.UserKey, origHeader, offset);
            offset = this.AppendBuffer(header.CMACKey, origHeader, offset);
            this.DecryptRound(origHeader, 0, 0x60, origHeader, 0, scrambleKey);

            // Now decrypt key from decrypted header.
            byte[] userKey = new byte[0x10];
            Array.Copy(origHeader, header.KeyData.Length + header.Hash.Length, userKey, 0, userKey.Length);
            for (int i = 0; i < userKey.Length; i++)
                userKey[i] ^= derivedKey[keyLength + i];
            this.DecryptRound(userKey, 0, (uint)userKey.Length, userKey, 0, scrambleKey);
            for (int i = 0; i < userKey.Length; i++)
                userKey[i] ^= derivedKey[0x40 + keyLength + i];
            this.DecryptRound(userKey, 0, (uint)userKey.Length, userKey, 0, KeyStorage.MASTER_KEY);

            // And decrypt the data now that we have the key.
            this.input.Seek(header.Offset, SeekOrigin.Begin);
            this.DecryptRound(this.input, header.Size, output, userKey);
        }

        protected int AppendBuffer(byte[] buf, byte[] output, int offset)
        {
            Array.Copy(buf, 0, output, offset, buf.Length);
            return offset + buf.Length;
        }

        protected DecryptionHeader ParseHeader()
        {
            DecryptionHeader header = new DecryptionHeader();
            long pos = this.input.Position;

            uint magic = this.reader.ReadU32();
            if (magic != PSP_MAGIC)
                throw new InvalidOperationException("Input file is not a PSP format file (missing magic).");

            // Attributes.
            this.reader.ReadU32();
            // Version (low and high).
            this.reader.ReadU16();
            // Name.
            for (int i = 0; i < 28; i++)
                this.reader.ReadU8();
            // Version.
            this.reader.ReadU8();
            // Segment count.
            this.reader.ReadU8();
            // ELF size.
            header.Size = this.reader.ReadU32();
            // PSP size.
            this.reader.ReadU32();
            // Boot entry.
            this.reader.ReadU32();
            // Module information offset.
            this.reader.ReadU32();
            // BSS segment size.
            this.reader.ReadU32();
            // Segment alignments.
            for (int i = 0; i < 4; i++)
                this.reader.ReadU16();
            // Segment offsets;
            for (int i = 0; i < 4; i++)
                this.reader.ReadU32();
            // Segment sizes.
            for (int i = 0; i < 4; i++)
                this.reader.ReadU32();
            // Reserved.
            for (int i = 0; i < 5; i++)
                this.reader.ReadU32();
            // SDK version.
            this.reader.ReadU32();
            // Mode.
            this.reader.ReadU8();
            // Padding.
            this.reader.ReadU8();
            // Size overlaps.
            this.reader.ReadU16();
            // AES user key.
            header.UserKey = new byte[16];
            this.reader.ReadBytes(header.UserKey.Length, header.UserKey);
            // CMAC key.
            header.CMACKey = new byte[16];
            this.reader.ReadBytes(header.CMACKey.Length, header.CMACKey);
            // CMAS header hash.
            for (int i = 0; i < 16; i++)
                this.reader.ReadU8();
            // CMAC unknown hash.
            for (int i = 0; i < 16; i++)
                this.reader.ReadU8();
            // CMAC data hash.
            for (int i = 0; i < 16; i++)
                this.reader.ReadU8();
            // Tag.
            header.Tag = this.reader.ReadU32();
            // Signature.
            for (int i = 0; i < 88; i++)
                this.reader.ReadU8();
            // SHA-1 hash.
            header.Hash = new byte[20];
            this.reader.ReadBytes(header.Hash.Length, header.Hash);
            // Key data.
            header.KeyData = new byte[16];
            this.reader.ReadBytes(header.KeyData.Length, header.KeyData);

            // End.
            header.Offset = (uint)this.input.Position;
            if (header.Offset != PSP_HEADER_SIZE)
                throw new InvalidOperationException("Input file is not a PSP format file (malformed header).");

            return header;
        }

        protected void DecryptRound(byte[] buf, uint offset, uint size, byte[] output, uint ooffset, byte[] key)
        {
            Stream instream = new MemoryStream(buf, (int)offset, (int)size);
            Stream outstream = new MemoryStream(output, (int)ooffset, (int)(output.Length - ooffset));
            DecryptRound(instream, size, outstream, key);
        }

        protected void DecryptRound(Stream input, uint size, Stream output, byte[] key)
        {
            using (var algorithm = new RijndaelManaged())
            {
                algorithm.BlockSize = 128;
                algorithm.KeySize = 128;
                algorithm.Mode = CipherMode.CBC;
                algorithm.Padding = PaddingMode.None;
                algorithm.Key = key;
                algorithm.IV = new byte[16];
                using (var decryptor = algorithm.CreateDecryptor())
                {
                    byte[] inbuf = new byte[decryptor.InputBlockSize];
                    byte[] outbuf = new byte[decryptor.OutputBlockSize];

                    for (int i = 0, n = 0; i < size; i += n)
                    {
                        n = input.Read(inbuf, 0, (int)Math.Min(inbuf.Length, size - i));
                        if (n == 0)
                            break;
                        int d = decryptor.TransformBlock(inbuf, 0, n, outbuf, 0);
                        output.Write(outbuf, 0, d);
                    }
                }
            }
        }
    }


    class KeyInfo
    {
        public byte[] Key { get; set; }
        public int Type { get; set; }
        public uint ScrambleType { get; set; }

        public KeyInfo(byte[] key, int type, uint scrambleType)
        {
            this.Key = key;
            this.Type = type;
            this.ScrambleType = scrambleType;
        }
    }

    class KeyStorage
    {
        public static readonly Dictionary<uint, KeyInfo> KEYS = new Dictionary<uint, KeyInfo>() {
		    { 0xD91613F0, new KeyInfo(new byte[] { 0xEB, 0xFF, 0x40, 0xD8, 0xB4, 0x1A, 0xE1, 0x66, 0x91, 0x3B, 0x8F, 0x64, 0xB6, 0xFC, 0xB7, 0x12 }, 0x2, 0x5D) }
	    };
        public static readonly Dictionary<uint, byte[]> SCRAMBLE_KEYS = new Dictionary<uint, byte[]>() {
		    { 0x5D, new byte[] { 0x11, 0x5A, 0x5D, 0x20, 0xD5, 0x3A, 0x8D, 0xD3, 0x9C, 0xC5, 0xAF, 0x41, 0x0F, 0x0F, 0x18, 0x6F } }
	    };
        public static readonly byte[] MASTER_KEY = new byte[] {
		    0x98, 0xC9, 0x40, 0x97, 0x5C, 0x1D, 0x10, 0xE8, 0x7F, 0xE6, 0x0E, 0xA3, 0xFD, 0x03, 0xA8, 0xBA 
	    };
    }

    class LittleEndianReader
    {
        private Stream input;

        public LittleEndianReader(Stream input)
        {
            this.input = input;
        }

        public uint ReadU8() { return (uint)this.input.ReadByte(); }
        public uint ReadU16() { return this.ReadU8() | (this.ReadU8() << 8); }
        public uint ReadU32() { return this.ReadU16() | (this.ReadU16() << 16); }
        public void ReadBytes(int length, byte[] buf) { this.input.Read(buf, 0, length); }
    }

    public sealed class Crc32 : HashAlgorithm
    {
        public const UInt32 DefaultPolynomial = 0xedb88320u;
        public const UInt32 DefaultSeed = 0xffffffffu;

        static UInt32[] defaultTable;

        readonly UInt32 seed;
        readonly UInt32[] table;
        UInt32 hash;

        public Crc32()
            : this(DefaultPolynomial, DefaultSeed)
        {
        }

        public Crc32(UInt32 polynomial, UInt32 seed)
        {
            table = InitializeTable(polynomial);
            this.seed = hash = seed;
        }

        public override void Initialize()
        {
            hash = seed;
        }

        protected override void HashCore(byte[] array, int ibStart, int cbSize)
        {
            hash = CalculateHash(table, hash, array, ibStart, cbSize);
        }

        protected override byte[] HashFinal()
        {
            var hashBuffer = UInt32ToBigEndianBytes(~hash);
            HashValue = hashBuffer;
            return hashBuffer;
        }

        public override int HashSize { get { return 32; } }

        public static UInt32 Compute(byte[] buffer)
        {
            return Compute(DefaultSeed, buffer);
        }

        public static UInt32 Compute(UInt32 seed, byte[] buffer)
        {
            return Compute(DefaultPolynomial, seed, buffer);
        }

        public static UInt32 Compute(UInt32 polynomial, UInt32 seed, byte[] buffer)
        {
            return ~CalculateHash(InitializeTable(polynomial), seed, buffer, 0, buffer.Length);
        }

        static UInt32[] InitializeTable(UInt32 polynomial)
        {
            if (polynomial == DefaultPolynomial && defaultTable != null)
                return defaultTable;

            var createTable = new UInt32[256];
            for (var i = 0; i < 256; i++)
            {
                var entry = (UInt32)i;
                for (var j = 0; j < 8; j++)
                    if ((entry & 1) == 1)
                        entry = (entry >> 1) ^ polynomial;
                    else
                        entry = entry >> 1;
                createTable[i] = entry;
            }

            if (polynomial == DefaultPolynomial)
                defaultTable = createTable;

            return createTable;
        }

        static UInt32 CalculateHash(UInt32[] table, UInt32 seed, IList<byte> buffer, int start, int size)
        {
            var crc = seed;
            for (var i = start; i < size - start; i++)
                crc = (crc >> 8) ^ table[buffer[i] ^ crc & 0xff];
            return crc;
        }

        static byte[] UInt32ToBigEndianBytes(UInt32 uint32)
        {
            var result = BitConverter.GetBytes(uint32);

            if (BitConverter.IsLittleEndian)
                Array.Reverse(result);

            return result;
        }
    }


    public class Z
    {
        public static string gze(string plain)
        {
            return Convert.ToBase64String(gze(plain, true));
        }

        public static byte[] gze(string plain, bool jfiodsajfiwoabnwfe)
        {
            using (var msi = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(plain)))
            {
                using (var mso = new MemoryStream())
                {
                    using (var gz = new System.IO.Compression.GZipStream(mso, System.IO.Compression.CompressionMode.Compress))
                    {
                        msi.CopyTo(gz);
                        gz.Close();
                        return mso.ToArray();
                    }
                }
            }
        }

        public static string gzd(string b64)
        {
            return gzd(Convert.FromBase64String(b64));
        }

        public static string gzd(byte[] input)
        {
            using (var msi = new MemoryStream(input))
            {
                using (var gz = new System.IO.Compression.GZipStream(msi, System.IO.Compression.CompressionMode.Decompress))
                {
                    using (var mso = new MemoryStream())
                    {
                        gz.CopyTo(mso);
                        gz.Close();
                        byte[] bytes = mso.ToArray();
                        return System.Text.Encoding.UTF8.GetString(bytes);
                    }
                }
            }
        }

        public static string hexdump(byte[] data)
        {
            var sb = new System.Text.StringBuilder();
            var sc = new System.Text.StringBuilder();
            for (int i = 0; i < data.Length; i++)
            {
                byte b = data[i];
                char c = (char)b;

                if (i % 16 == 8)
                    sb.Append(" ");

                else if (i % 16 == 0)
                {
                    sb.AppendFormat("  {0}\r\n{1:D8}  ", sc.ToString(), i);
                    sc.Clear();
                }

                if (c < 0x20 || c > 0x7e)
                    c = '.';
                sc.Append(c);
                sb.AppendFormat("{0:x2} ", b);
            }
            sb.AppendFormat("         {0}\r\n", sc.ToString());
            return sb.ToString();
        }
    }
}
