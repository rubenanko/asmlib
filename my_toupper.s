global my_toupper

section .text

my_toupper:
  mov eax, edi
  cmp al, 'a'
  jb .back 
  cmp al, 'z'
  ja .back 
  sub al, 32
.back:
  ret

