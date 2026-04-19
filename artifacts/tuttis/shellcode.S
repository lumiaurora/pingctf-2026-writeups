.section .text
.globl _start
_start:
  lui a3, 0x10000
  addi a4, a3, 5
  lui a1, 0x80004
  addi a1, a1, -0x200

loop:
  lbu a0, 0(a1)
  beqz a0, done

wait_tx:
  lbu a5, 0(a4)
  andi a5, a5, 0x20
  beqz a5, wait_tx
  sb a0, 0(a3)
  addi a1, a1, 1
  j loop

done:
  li a0, 10

wait_nl:
  lbu a5, 0(a4)
  andi a5, a5, 0x20
  beqz a5, wait_nl
  sb a0, 0(a3)

hang:
  j hang
