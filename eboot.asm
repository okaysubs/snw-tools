.psp
.open "EBOOT.BIN",0x08804000
.headersize 0x8803F40

; Set sceImposeSetLanguageMode()'s first argument to 0x1 (English)
.org 0x8832670
   li    $a1, 1

; Set the language field in the struct parameter to sceUtilitySavedataInitStart() to 0x1 (English)
.org 0x8832334
   li    $at, 1
.org 0x8832350
   sw    $at, 4($s2)

; Change the embedded disc IDs region to "ES" (Europe)
.org 0x8889A60
   .ascii "ES"
.org 0x8889FD6
   .ascii "ES"
.org 0x888A166
   .ascii "ES"

; Fix pause menu alignment offset in two ways:
;   * Make offset calculation halfwidth-count based by reducing the width multiplier to 9.
.org 0x88157A8
   jal   0x888B1CC
   move  $t0, $zero
   sll   $a0, $v0, 3
   addu  $a0, $v0, $a0
   jal   0x888A2F8
    sra  $a0, $a0, 1

;   * Add a constant 10 pixels. This shows mis-aligned in the original too.
.org 0x888A2F8
   subu  $a0, $zero, $a0
   jr    $ra
    addi $a0, $a0, 10

;   * Make the character count halfwidth characters by counting using a simple strlen();
;     This works because halfwidth characters are always one byte, while fullwidth are two.
.org 0x888B1CC
   addi  $sp, -8
   sw    $ra, 4($sp)
   move  $t1, $a2
   li    $v0, 0
l: lb    $t2, ($t1)
   beqz  $t2, e
    addi $t1, 1
   j     l
    addi $v0, 1
e: jal   0x8838794
    sw   $v0, ($sp)
   lw    $v0, ($sp)
   lw    $ra, 4($sp)
   jr    $ra
    addi $sp, 8

;     (Clear the relocation entry for the replaced branch at 0x88157A8.)
.org 0x88A339C
   .word 0

.close

