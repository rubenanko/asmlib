global my_strcat 

section .text

my_strcat:
  push rdi

_toend:
  cmp byte [rdi], 0
  jz _copy
  inc rdi
  jmp _toend

_copy:
  lodsb
  stosb
  test al, al 
  jne _copy
  pop rax
  ret
