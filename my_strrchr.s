global my_strrchr
section .text

my_strrchr:
  xor rax, rax

_loop:
  push qword [rdi]
  pop rdx
  cmp dl, sil
  jne _cont
  push rdi
  pop rax

_cont:
  test dl, dl
  jz _return
  inc rdi
  jmp _loop

_return:
  ret
