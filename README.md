# *Sound of the Sky: Quintet of Maidens* translation tools

*Just looking for the patch? Head over to https://ocv.me/snw to get it.*

## Overview

[Sora no Woto: Otome no Gojuusou](https://vndb.org/v5304) is a PSP visual novel that uses
a bunch of Dreamcast-era [CRI](https://en.wikipedia.org/wiki/CRI_Middleware) middleware.

More interesting however were the (seemingly) custom image, script and font formats.
A blog post is on its way describing our process of figuring out the semantics of these formats.

For now, please enjoy the source code of the tools we created to translate the VN.

## Structure

* `patcher`: The source code for the patcher front-end.
* `snw_gp_archive`: The bootstrap directory where the front-end, combined with the actual patches, creates the patcher contents from.
* `tools`: The source code for the unpacking, translation and repacking tools.
* `subs`: The subtitles and AVISynth scripts used to re-encode the OP and intro videos.
* `prxpatch`: An abandoned prototype for a patcher PSP module.

## Included tools

All below tools can be found in the `tools` directory.

### Unpacking/repacking

* `adjustoffsets.py`: Adjust the file structure to deal with the new patched files. *(deprecated by built-in patcher functionality)*
* `alter.py`: Updates extracted files with replacement files from another folder.
* `config.py`: Optional configuration to speed unpacking/repacking up by skipping unnecessary files.
* `embedded.py`: Repack the embedded MARC archive within the main executable.
* `extract.py`: Recursively extract the visual novel and its various nested archives and formats.
* `repack.py`: Recursively repack extracted contents into data files.
* `scripts2replacementdata.py`: Organize script files. *(deprecated by organizing it yourself)*

### File formats

* `adx.py`: [ADX](https://en.wikipedia.org/wiki/ADX_(file_format)) audio file unpacker/repacker (unfinished).
* `afs.py`: [AFS](http://wiki.xentax.com/index.php/GRAF:AFS_AFS) archive file unpacker/repacker.
* `ev.py`: EV script file dialogue unpacker/repacker.
* `font.py`: Font file unpacker/repacker.
* `gim.py`: GIM image file unpack/repacker using [GimConv](http://www.psdevwiki.com/ps3/GimConv).
* `marc.py`: MARC archive file unpacker/repacker.
* `mtex.py`: MTEX image file unpacker.
* `mtexsplice.py`: MTEX image file repacker.

### Quality checking

* `consistency.py`: Checks for possible inconsistencies within the translation.

### Misc

* `changealpha.py`: Tweak alpha channel of an image.
* `evtres.py`: Perform character analysis on scripts for font purposes.
* `encvis.py` and `evis.py`: Parse and visualize the script structure in EV files.
* `evisscan.py`: Scan EV file script structure for certain commands.

## Other things

The `prxpatch` directory contains a PSP kernel module (.prx file) to impose upon the game and force the
system OSD to display things in English instead of Japanese.
It was based off [Codestation's prxpatch](https://github.com/codestation/prxpatch),
essentially only stripping the more elaborate patching done there and adjusting it for Sora no Woto.

Sadly, it doesn't work, but it shouldn't take much effort to get working.
We ultimately deemed it not worth the effort, especially considering it has to be installed to a memory stick,
which would be yet another stage for the patcher. In addition, the relatively simple changes it was stripped
down to would be better served by just a patch to the main game binary.

## Making a patch

0. Compile the patcher in the `patcher` directory. Make sure the patch contents can be bootstrapped by placing the `snw_gp_archive` directory in the same directory as the patcher executable.
1. Rip your copy of the VN from the UMD to an ISO file.
2. Use the patcher to extract the ISO as follows: copy the VN ISO to the same directory as the patcher executable as `orig.iso`, then copy it again to `okay.iso`.
   Then run the patcher and answer 'Yes' to the question of whether you want to make a patch. The game files you want to edit are in the `tmp2` folder.
   Leave the patcher open.
3. Use `extract.py` to recursively unpack the `data.afs` file located in `PSP_GAME/USRDIR` and to create a metadata file:

    ```sh
    python3 extract.py /path/to/data.afs data.meta yes
    ```

4. Edit any of the files that are extracted. Images and fonts should be extracted to PNG files, dialogue and strings to plain text files.
   You can *optionally* copy only the files you deem relevant to another directory (e.g. a shared Dropbox folder) and use `alter.py` to copy over files from there
   to the original folder, as long as the folder structure is kept intact:

    ```sh
    python3 alter.py /path/to/data.afs /path/to/working/folder
    ```

5. *(Optional)* Use `consistency.py` to do some basic consistency checking on the script:

    ```sh
    python3 consistency.py /path/to/data.afs
    ```

5. Use `repack.py` with the generated metadata file to recursively repack the files into `data.afs`:

    ```sh
    python3 repack.py data.meta
    ```

6. *(Optional)* Use `embedded.py` to extract the embedded archive in `EBOOT.BIN` located in `PSP_GAME/SYSDIR` and make changes to its contents.
   This archive contains trivial things like the loading graphic shown at the very start:

    ```sh
    python3 embedded.py extract /path/to/EBOOT.BIN archive.marc
    python3 extract.py archive.marc embedded.meta
    # Make changes...
    python3 repack.py embedded.meta
    python3 embedded.py repack /path/to/EBOOT.BIN archive.marc
    ```

7. *(Optional)* Patch `EBOOT.BIN` to use English in the PSP OSD's system dialogs. We used a hex editor here:

   * Change the bytes starting at offset `0x2E3F4` to `01 00 01 34` (`li $at, 1`);
   * Change the bytes starting at offset `0x2E412` to `04 00 41 AE` (`sw $at, 4($s2)`);
   * Change the bytes starting at offset `0x2E730` to `01 00 04 34` (`li $a1, 1`).
   * Change the embedded disc ID at offsets `0x85B18`, `0x86094` and `0x86224`. We just changed the region part (`JM`, offset +2) to European (`ES`).

8. *(Optional)* Hand-tweak `UMD_DATA.BIN` and `PARAM.SFO` (in the `PSP_GAME` folder) to edit the VN title and disc ID. We, again, just used a hex editor here.
9. *(Optional)* Use, among others, [ffmpeg](https://ffmpeg.org/) to extract the video and audio streams from the movie files in `PSP_GAME/USRDIR/mv`, edit/translate/sub them, and remux them.
10. Go back to the patcher, and tell it to proceed. It will generate a patcher from the new content in the `tmp2` folder compared to the original content in the `tmp1` folder and output it as `[OK]_Sound_of_the_Sky_Quintet_of_Maidens_[TLPatch_<version>][<crc>].exe` in the same folder as itself.     

## License

The tools and patcher, whose files reside in the `tools` and `patcher` directories,
are licensed under the MIT license:

```
Copyright (C) 2013-2016
    Shiz <hi@shiz.me>,
    CensoredUsername <cens.username@gmail.com>,
    ed <s@ocv.me>

Permission is hereby granted, free of charge, to any
person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without
limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice
shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
```

Exceptions to this are the following files/directories:

* `patcher/DiscUtils`: https://discutils.codeplex.com/SourceControl/latest#LICENSE.txt
* `patcher/res/xz.exe`: http://git.tukaani.org/?p=xz.git;a=blob;f=COPYING;h=43c90d0598c55ab9f4edeb1781cdf5c549ca567e;hb=HEAD
* `patcher/*/doot.ico`: (unknown license)
* `snw_gp_archive/bin/*iso*`: https://sourceforge.net/projects/cdrtools/
* `snw_gp_archive/bin/ciso.exe`: https://sourceforge.net/p/ciso/code/2/tree/trunk/license
* `snw_gp_archive/bin/xdelta3.exe`: https://github.com/jmacd/xdelta/blob/f89cbc46d874b958678bef1a6bfa33912ddbcbd0/xdelta3/LICENSE
* `snw_gp_archive/nsf/chiptune.exe`: https://github.com/bbbradsmith/nsfplay/blob/64c12149674c8cd7868a07545338429e7bab1ec2/nsfplay/nsfplay.h
* `snw_gp_archive/nsf/plugins`: https://github.com/bbbradsmith/nsfplay/blob/8589b385cc7cfb3e665adda5c86e50a054fe0f61/readme.txt
* `snw_gp_archive/nsf/nudzi_mi_sie.nsf`: http://famitracker.com/forum/posts.php?id=6130 (unknown license)
* `snw_gp_archive/nsf/famicom_disco.nsf`: https://www.youtube.com/watch?v=EeJF161wRoM (unknown license)

Any original works, depending on your jurisdiction, included in released
translation patches are licensed under the [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) license:

```
Creative Commons Attribution-ShareAlike 4.0 International Public
License

By exercising the Licensed Rights (defined below), You accept and agree
to be bound by the terms and conditions of this Creative Commons
Attribution-ShareAlike 4.0 International Public License ("Public
License"). To the extent this Public License may be interpreted as a
contract, You are granted the Licensed Rights in consideration of Your
acceptance of these terms and conditions, and the Licensor grants You
such rights in consideration of benefits the Licensor receives from
making the Licensed Material available under these terms and
conditions.


Section 1 -- Definitions.

  a. Adapted Material means material subject to Copyright and Similar
     Rights that is derived from or based upon the Licensed Material
     and in which the Licensed Material is translated, altered,
     arranged, transformed, or otherwise modified in a manner requiring
     permission under the Copyright and Similar Rights held by the
     Licensor. For purposes of this Public License, where the Licensed
     Material is a musical work, performance, or sound recording,
     Adapted Material is always produced where the Licensed Material is
     synched in timed relation with a moving image.

  b. Adapter's License means the license You apply to Your Copyright
     and Similar Rights in Your contributions to Adapted Material in
     accordance with the terms and conditions of this Public License.

  c. BY-SA Compatible License means a license listed at
     creativecommons.org/compatiblelicenses, approved by Creative
     Commons as essentially the equivalent of this Public License.

  d. Copyright and Similar Rights means copyright and/or similar rights
     closely related to copyright including, without limitation,
     performance, broadcast, sound recording, and Sui Generis Database
     Rights, without regard to how the rights are labeled or
     categorized. For purposes of this Public License, the rights
     specified in Section 2(b)(1)-(2) are not Copyright and Similar
     Rights.

  e. Effective Technological Measures means those measures that, in the
     absence of proper authority, may not be circumvented under laws
     fulfilling obligations under Article 11 of the WIPO Copyright
     Treaty adopted on December 20, 1996, and/or similar international
     agreements.

  f. Exceptions and Limitations means fair use, fair dealing, and/or
     any other exception or limitation to Copyright and Similar Rights
     that applies to Your use of the Licensed Material.

  g. License Elements means the license attributes listed in the name
     of a Creative Commons Public License. The License Elements of this
     Public License are Attribution and ShareAlike.

  h. Licensed Material means the artistic or literary work, database,
     or other material to which the Licensor applied this Public
     License.

  i. Licensed Rights means the rights granted to You subject to the
     terms and conditions of this Public License, which are limited to
     all Copyright and Similar Rights that apply to Your use of the
     Licensed Material and that the Licensor has authority to license.

  j. Licensor means the individual(s) or entity(ies) granting rights
     under this Public License.

  k. Share means to provide material to the public by any means or
     process that requires permission under the Licensed Rights, such
     as reproduction, public display, public performance, distribution,
     dissemination, communication, or importation, and to make material
     available to the public including in ways that members of the
     public may access the material from a place and at a time
     individually chosen by them.

  l. Sui Generis Database Rights means rights other than copyright
     resulting from Directive 96/9/EC of the European Parliament and of
     the Council of 11 March 1996 on the legal protection of databases,
     as amended and/or succeeded, as well as other essentially
     equivalent rights anywhere in the world.

  m. You means the individual or entity exercising the Licensed Rights
     under this Public License. Your has a corresponding meaning.


Section 2 -- Scope.

  a. License grant.

       1. Subject to the terms and conditions of this Public License,
          the Licensor hereby grants You a worldwide, royalty-free,
          non-sublicensable, non-exclusive, irrevocable license to
          exercise the Licensed Rights in the Licensed Material to:

            a. reproduce and Share the Licensed Material, in whole or
               in part; and

            b. produce, reproduce, and Share Adapted Material.

       2. Exceptions and Limitations. For the avoidance of doubt, where
          Exceptions and Limitations apply to Your use, this Public
          License does not apply, and You do not need to comply with
          its terms and conditions.

       3. Term. The term of this Public License is specified in Section
          6(a).

       4. Media and formats; technical modifications allowed. The
          Licensor authorizes You to exercise the Licensed Rights in
          all media and formats whether now known or hereafter created,
          and to make technical modifications necessary to do so. The
          Licensor waives and/or agrees not to assert any right or
          authority to forbid You from making technical modifications
          necessary to exercise the Licensed Rights, including
          technical modifications necessary to circumvent Effective
          Technological Measures. For purposes of this Public License,
          simply making modifications authorized by this Section 2(a)
          (4) never produces Adapted Material.

       5. Downstream recipients.

            a. Offer from the Licensor -- Licensed Material. Every
               recipient of the Licensed Material automatically
               receives an offer from the Licensor to exercise the
               Licensed Rights under the terms and conditions of this
               Public License.

            b. Additional offer from the Licensor -- Adapted Material.
               Every recipient of Adapted Material from You
               automatically receives an offer from the Licensor to
               exercise the Licensed Rights in the Adapted Material
               under the conditions of the Adapter's License You apply.

            c. No downstream restrictions. You may not offer or impose
               any additional or different terms or conditions on, or
               apply any Effective Technological Measures to, the
               Licensed Material if doing so restricts exercise of the
               Licensed Rights by any recipient of the Licensed
               Material.

       6. No endorsement. Nothing in this Public License constitutes or
          may be construed as permission to assert or imply that You
          are, or that Your use of the Licensed Material is, connected
          with, or sponsored, endorsed, or granted official status by,
          the Licensor or others designated to receive attribution as
          provided in Section 3(a)(1)(A)(i).

  b. Other rights.

       1. Moral rights, such as the right of integrity, are not
          licensed under this Public License, nor are publicity,
          privacy, and/or other similar personality rights; however, to
          the extent possible, the Licensor waives and/or agrees not to
          assert any such rights held by the Licensor to the limited
          extent necessary to allow You to exercise the Licensed
          Rights, but not otherwise.

       2. Patent and trademark rights are not licensed under this
          Public License.

       3. To the extent possible, the Licensor waives any right to
          collect royalties from You for the exercise of the Licensed
          Rights, whether directly or through a collecting society
          under any voluntary or waivable statutory or compulsory
          licensing scheme. In all other cases the Licensor expressly
          reserves any right to collect such royalties.


Section 3 -- License Conditions.

Your exercise of the Licensed Rights is expressly made subject to the
following conditions.

  a. Attribution.

       1. If You Share the Licensed Material (including in modified
          form), You must:

            a. retain the following if it is supplied by the Licensor
               with the Licensed Material:

                 i. identification of the creator(s) of the Licensed
                    Material and any others designated to receive
                    attribution, in any reasonable manner requested by
                    the Licensor (including by pseudonym if
                    designated);

                ii. a copyright notice;

               iii. a notice that refers to this Public License;

                iv. a notice that refers to the disclaimer of
                    warranties;

                 v. a URI or hyperlink to the Licensed Material to the
                    extent reasonably practicable;

            b. indicate if You modified the Licensed Material and
               retain an indication of any previous modifications; and

            c. indicate the Licensed Material is licensed under this
               Public License, and include the text of, or the URI or
               hyperlink to, this Public License.

       2. You may satisfy the conditions in Section 3(a)(1) in any
          reasonable manner based on the medium, means, and context in
          which You Share the Licensed Material. For example, it may be
          reasonable to satisfy the conditions by providing a URI or
          hyperlink to a resource that includes the required
          information.

       3. If requested by the Licensor, You must remove any of the
          information required by Section 3(a)(1)(A) to the extent
          reasonably practicable.

  b. ShareAlike.

     In addition to the conditions in Section 3(a), if You Share
     Adapted Material You produce, the following conditions also apply.

       1. The Adapter's License You apply must be a Creative Commons
          license with the same License Elements, this version or
          later, or a BY-SA Compatible License.

       2. You must include the text of, or the URI or hyperlink to, the
          Adapter's License You apply. You may satisfy this condition
          in any reasonable manner based on the medium, means, and
          context in which You Share Adapted Material.

       3. You may not offer or impose any additional or different terms
          or conditions on, or apply any Effective Technological
          Measures to, Adapted Material that restrict exercise of the
          rights granted under the Adapter's License You apply.


Section 4 -- Sui Generis Database Rights.

Where the Licensed Rights include Sui Generis Database Rights that
apply to Your use of the Licensed Material:

  a. for the avoidance of doubt, Section 2(a)(1) grants You the right
     to extract, reuse, reproduce, and Share all or a substantial
     portion of the contents of the database;

  b. if You include all or a substantial portion of the database
     contents in a database in which You have Sui Generis Database
     Rights, then the database in which You have Sui Generis Database
     Rights (but not its individual contents) is Adapted Material,

     including for purposes of Section 3(b); and
  c. You must comply with the conditions in Section 3(a) if You Share
     all or a substantial portion of the contents of the database.

For the avoidance of doubt, this Section 4 supplements and does not
replace Your obligations under this Public License where the Licensed
Rights include other Copyright and Similar Rights.


Section 5 -- Disclaimer of Warranties and Limitation of Liability.

  a. UNLESS OTHERWISE SEPARATELY UNDERTAKEN BY THE LICENSOR, TO THE
     EXTENT POSSIBLE, THE LICENSOR OFFERS THE LICENSED MATERIAL AS-IS
     AND AS-AVAILABLE, AND MAKES NO REPRESENTATIONS OR WARRANTIES OF
     ANY KIND CONCERNING THE LICENSED MATERIAL, WHETHER EXPRESS,
     IMPLIED, STATUTORY, OR OTHER. THIS INCLUDES, WITHOUT LIMITATION,
     WARRANTIES OF TITLE, MERCHANTABILITY, FITNESS FOR A PARTICULAR
     PURPOSE, NON-INFRINGEMENT, ABSENCE OF LATENT OR OTHER DEFECTS,
     ACCURACY, OR THE PRESENCE OR ABSENCE OF ERRORS, WHETHER OR NOT
     KNOWN OR DISCOVERABLE. WHERE DISCLAIMERS OF WARRANTIES ARE NOT
     ALLOWED IN FULL OR IN PART, THIS DISCLAIMER MAY NOT APPLY TO YOU.

  b. TO THE EXTENT POSSIBLE, IN NO EVENT WILL THE LICENSOR BE LIABLE
     TO YOU ON ANY LEGAL THEORY (INCLUDING, WITHOUT LIMITATION,
     NEGLIGENCE) OR OTHERWISE FOR ANY DIRECT, SPECIAL, INDIRECT,
     INCIDENTAL, CONSEQUENTIAL, PUNITIVE, EXEMPLARY, OR OTHER LOSSES,
     COSTS, EXPENSES, OR DAMAGES ARISING OUT OF THIS PUBLIC LICENSE OR
     USE OF THE LICENSED MATERIAL, EVEN IF THE LICENSOR HAS BEEN
     ADVISED OF THE POSSIBILITY OF SUCH LOSSES, COSTS, EXPENSES, OR
     DAMAGES. WHERE A LIMITATION OF LIABILITY IS NOT ALLOWED IN FULL OR
     IN PART, THIS LIMITATION MAY NOT APPLY TO YOU.

  c. The disclaimer of warranties and limitation of liability provided
     above shall be interpreted in a manner that, to the extent
     possible, most closely approximates an absolute disclaimer and
     waiver of all liability.


Section 6 -- Term and Termination.

  a. This Public License applies for the term of the Copyright and
     Similar Rights licensed here. However, if You fail to comply with
     this Public License, then Your rights under this Public License
     terminate automatically.

  b. Where Your right to use the Licensed Material has terminated under
     Section 6(a), it reinstates:

       1. automatically as of the date the violation is cured, provided
          it is cured within 30 days of Your discovery of the
          violation; or

       2. upon express reinstatement by the Licensor.

     For the avoidance of doubt, this Section 6(b) does not affect any
     right the Licensor may have to seek remedies for Your violations
     of this Public License.

  c. For the avoidance of doubt, the Licensor may also offer the
     Licensed Material under separate terms or conditions or stop
     distributing the Licensed Material at any time; however, doing so
     will not terminate this Public License.

  d. Sections 1, 5, 6, 7, and 8 survive termination of this Public
     License.


Section 7 -- Other Terms and Conditions.

  a. The Licensor shall not be bound by any additional or different
     terms or conditions communicated by You unless expressly agreed.

  b. Any arrangements, understandings, or agreements regarding the
     Licensed Material not stated herein are separate from and
     independent of the terms and conditions of this Public License.


Section 8 -- Interpretation.

  a. For the avoidance of doubt, this Public License does not, and
     shall not be interpreted to, reduce, limit, restrict, or impose
     conditions on any use of the Licensed Material that could lawfully
     be made without permission under this Public License.

  b. To the extent possible, if any provision of this Public License is
     deemed unenforceable, it shall be automatically reformed to the
     minimum extent necessary to make it enforceable. If the provision
     cannot be reformed, it shall be severed from this Public License
     without affecting the enforceability of the remaining terms and
     conditions.

  c. No term or condition of this Public License will be waived and no
     failure to comply consented to unless expressly agreed to by the
     Licensor.

  d. Nothing in this Public License constitutes or may be interpreted
     as a limitation upon, or waiver of, any privileges and immunities
     that apply to the Licensor or You, including from the legal
     processes of any jurisdiction or authority.
```

The kernel module in the `prxpatch` directory is a derivative of [Codestation's prxpatch](https://github.com/codestation/prxpatch)
and is this licensed under the GNU General Public License version 3 or later;
see the `COPYING` file in that directory for details.
