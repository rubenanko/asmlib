global my_isalpha

section .text

my_isalpha:
  xor rax, rax
  cmp edi,'z' 
  jg _fail
  
  cmp edi, 'a'
  jge _success

  cmp edi, 'Z'
  jg _fail
  
  cmp edi, 'A'
  jge _success
  
_fail:
  push 0
  pop rax
  ret

_success:
  push 1
  pop rax
  ret


