global my_puts

section .text

my_puts:
  push rdi
  pop rsi
  push rdi
  pop rdx

.strlen:
.strlen_loop:
  cmp byte [rdx], 0
  je .end_strlen
  inc rdx
  jmp .strlen_loop
.end_strlen:

.write_str:
  push 1
  push 1
  pop rax
  pop rdi
  sub rdx, rsi 
  syscall
  test rax, rax
  js .error

.write_nl:
  sub rsp, 8
  mov qword [rsp], 10
  push 1
  push 1
  pop rax
  pop rdi
  push rsp
  pop rsi
  push 1 
  pop rdx
  syscall
  add rsp, 8
  test rax, rax
  js .error
  push 1
  pop rax
  ret

.error:
  push -1
  pop rax
  ret
