global my_strcmp

section .text

my_strcmp:

_loop_compare:
  mov al, [rdi]
  mov dl, [rsi]
  cmp al, dl
  je _equal
 
 _diff:
  movzx eax, al
  movzx edx, dl
  sub eax, edx
  ret


_equal:
  test al, al 
  jz _return
  inc rdi
  inc rsi
  jmp _loop_compare

_return:
  xor eax, eax
  ret
