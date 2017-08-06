.psp
.open "EBOOT-temp.BIN","EBOOT.BIN",0x08804000
.headersize 0x08803f40


; adjust text speed
; fade ticks is always 0x1E or 0. >> 3 gives 3, &0x2 gives 2, >> 4 gives 1. 
.org 0x088389A4
    sll     $s1, $a3, 1 ; fade in twice as fast
    sra     $s0, $a2, 4 ; and divide fade ticks by 4.
    andi    $s2, $t0, 0x00 ; ignore newchar overrides.

; make sure the function behaves okay with a delay of 1
.org 0x08838A50
    li      $a1, 0

; varwidth code
.org 0x08838428
    ; this is normally a branch which checks if alpha == 0.0 and then does not push the character to the drawlist
    ; as we need the intermediate characters for the width calculation, we don't do this.
    beqz    $a0,  continue ; note: this is the target of a reloc so we don't get away that easy.
     nop
continue:
    ; rotation.x = disp->rot.x
    lw      $a0,  0($s3)
    sw      $a0,  0x60-0x5C($sp)
    ; rotation.y = disp->rot.y
    lw      $a1,  4($s3)
    sw      $a1,  0x60-0x58($sp)
    ; rotation.z = disp->rot.z + curchar.rotation
    lwc1    $f12, 8($s3)
    lwc1    $f13, 0xC($s0)
    add.s   $f12, $f13
    swc1    $f12, 0x60-0x54($sp)
    ; scale.x = curchar.scale
    ; scale.y = curchar.scale
    lw      $a2,  8($s0)
    sw      $a2,  0x60-0x50($sp)
    sw      $a2,  0x60-0x4C($sp)
    ; accumulator update
    lb      $a0,  0x4($s0) ; curchar.column
    li      $a1,  1        ; 1
    beqz    $a0,  reset
     subu   $a0,  $t8 ; as this would just leave some random trash in the other case we leave it here.
    j accum_update
     nop
    nop
reset:
    mtc1    $zero, $f0
rejoin:
    lbu     $t8,  0x4($s0) ;curchar.column
    lhu     $t9,  0x0($s0) ;curchar.code
    ; position.x = (float)disp->xpos + accumulator
    lh      $a1,  0x28($s1) ; disp->xpos
    mtc1    $a1,  $f12
    cvt.s.w $f12, $f12
    add.s   $f12, $f0
    swc1    $f12, 0x60-0x44($sp)
    ; position.y = (float)disp->ypos - (float)curchar.line * render->yspacing // y = ystart - line * spacing
    lb      $a0,  0x5($s0) ; curchar.line
    mtc1    $a0,  $f12
    cvt.s.w $f12, $f12
    lwc1    $f13, 0x14($s4) ; render.yspacing
    mul.s   $f12, $f13
    lh      $a1,  0x2A($s1) ; disp->ypos
    mtc1    $a1,  $f13
    cvt.s.w $f13, $f13
    sub.s   $f12, $f13, $f12
    swc1    $f12, 0x60-0x40($sp)

.org 0x0888CEE0
.area 0x100b
accum_update:
    beq     $a0,  $a1, halfwidth ; branch if a0 == 1
     mtc1   $a0,  $f12 ; only used by fullwidth
fullwidth:
    cvt.s.w $f12, $f12
    lwc1    $f13, 0x10($s4) ; render.xspacing
    mul.s   $f12, $f13
    j rejoin
     add.s  $f0, $f12

halfwidth:
    ; obtain the key
    lh      $a0,  0x0($s0)   ; current char
    slti    $a1,  $a0, 0x100
    beqz    $a1,  table     ; bail out if current char is fullwidth
    ; binary search setup, key
     sll    $a0,  8
    or      $a0,  $t9
    ; top/bottom of the table
    lui     $t0,  (KERNING_TABLE >> 16) + 1                      ; top of pointer to the kerning table
    addi    $t0,  (KERNING_TABLE & 0xFFFF) - 0x10000             ; bottom of pointer to the binary search table
    addi    $t1,  $t0, (KERNING_TABLE_END - KERNING_TABLE - 0x4) ; top of binary search table
kernloop: ; binary search loop. optimized for speed.
    add    $a1, $t0, $t1     ; pos = (top - bot) >> 1 & ~0x3
    srl     $a1, 3
    sll     $a1, 2
    lhu     $a2, 0x0($a1)    ; posval = *pos
    beq     $a0, $a2, result ; if posval == target
     slt    $a2, $a0, $a2
    bnez    $a2, smaller     ; if target < posval 
     slt    $a2, $t1, $t0
    beqz    $a2, kernloop    ; if top >= bottom
     addi   $t0, $a1, 4
smaller:
    beqz    $a2, kernloop    ; if top >= bottom
     addi   $t1, $a1, -4
table: ; we didn't get a hit, do a lookup in the table
    lui     $a1,  (WIDTH_TABLE >> 16) + 1
    addu    $a1,  $t9
    addiu   $a1,  (WIDTH_TABLE & 0xFFFF) - 0x10000 - 0x20 - 0x2 ; bottom 16 bits of address - overflow correction - offset of visible ascii characters - correction for other path
result: ; we've got an address, load it
    lbu     $a0, 0x2($a1)
    lui     $a1,  0x3F00 ; 0.5
    ; do the math to update the accumulator
    mtc1    $a0,  $f12
    mtc1    $a1,  $f13
    cvt.s.w $f12, $f12
    mul.s   $f12, $f13
    j rejoin
     add.s  $f0,  $f12 ; accumulator update
.endarea

.org 0x0888cfe0
WIDTH_TABLE:
.area 0x60b
; newcodepage4.png
;         [ ]  !   "   #   $   %   &   '   (   )   *   +   ,   -   .   /
    .byte  8,  9, 14, 18, 14, 22, 19,  8, 12, 12, 15, 17,  8, 15,  8, 15
;          0   1   2   3   4   5   6   7   8   9   :   ;   <   =   >   ?
    .byte 17, 12, 16, 16, 17, 15, 16, 17, 15, 16,  8,  8, 17, 17, 17, 14
;          @   A   B   C   D   E   F   G   H   I   J   K   L   M   N   O
    .byte 19, 20, 19, 19, 20, 17, 17, 19, 19,  8, 11, 21, 16, 24, 20, 21
;          P   Q   R   S   T   U   V   W   X   Y   Z   [   \   ]   ^   _
    .byte 19, 22, 19, 15, 17, 19, 20, 28, 18, 18, 17, 13, 15, 13, 15, 19
;          `   a   b   c   d   e   f   g   h   i   j   k   l   m   n   o
    .byte 13, 18, 18, 17, 17, 17, 13, 17, 18,  8,  8, 17, 11, 26, 17, 18
;          p   q   r   s   t   u   v   w   x   y   z   {   |   }   ~   
    .byte 18, 18, 13, 13, 12, 17, 17, 27, 17, 17, 15, 12,  7, 12, 16, 17
.endarea

KERNING_TABLE:
.area 0x1000b
    ; sorted list of combinations for the binary search tree
    ; note: low values first, high values last.
    ; note2: there should at least be one item in this list
    ; mapping: 0xcurprev pixels
    ; example entry: capital A followed by a capital V
    .halfword 0x222c, 4 ; ,"
    .halfword 0x222e, 4 ; ."
    .halfword 0x2241, 18 ; A"
    .halfword 0x2242, 17 ; B"
    .halfword 0x224c, 12 ; L"
    .halfword 0x272c, 4 ; ,'
    .halfword 0x272e, 4 ; .'
    .halfword 0x2741, 18 ; A'
    .halfword 0x2742, 17 ; B'
    .halfword 0x274c, 12 ; L'
    .halfword 0x2c22, 10 ; ",
    .halfword 0x2c27, 4 ; ',
    .halfword 0x2c46, 13 ; F,
    .halfword 0x2c54, 14 ; T,
    .halfword 0x2c59, 14 ; Y,
    .halfword 0x2c66, 11 ; f,
    .halfword 0x2c72, 9 ; r,
    .halfword 0x2e22, 10 ; ".
    .halfword 0x2e27, 4 ; '.
    .halfword 0x2e46, 13 ; F.
    .halfword 0x2e54, 14 ; T.
    .halfword 0x2e59, 14 ; Y.
    .halfword 0x2e66, 11 ; f.
    .halfword 0x2e72, 9 ; r.
    .halfword 0x4122, 12 ; "A
    .halfword 0x4127, 6 ; 'A
    .halfword 0x4146, 15 ; FA
    .halfword 0x4154, 14 ; TA
    .halfword 0x4159, 14 ; YA
    .halfword 0x4a22, 10 ; "J
    .halfword 0x4a27, 4 ; 'J
    .halfword 0x5441, 16 ; AT
    .halfword 0x594c, 12 ; LY
    .halfword 0x6154, 14 ; Ta
    .halfword 0x6159, 16 ; Ya
    .halfword 0x6166, 11 ; fa
    .halfword 0x6354, 14 ; Tc
    .halfword 0x6359, 16 ; Yc
    .halfword 0x6366, 11 ; fc
    .halfword 0x6454, 14 ; Td
    .halfword 0x6459, 16 ; Yd
    .halfword 0x6466, 11 ; fd
    .halfword 0x6554, 14 ; Te
    .halfword 0x6559, 16 ; Ye
    .halfword 0x6566, 11 ; fe
    .halfword 0x6754, 14 ; Tg
    .halfword 0x6759, 16 ; Yg
    .halfword 0x6f54, 14 ; To
    .halfword 0x6f66, 11 ; fo
    .halfword 0x7154, 14 ; Tq
    .halfword 0x7266, 11 ; fr
    .halfword 0x7554, 16 ; Tu
    .halfword 0x7654, 16 ; Tv
    .halfword 0x7954, 16 ; Ty
.endarea
KERNING_TABLE_END:

.close


