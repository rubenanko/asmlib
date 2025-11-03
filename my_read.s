global my_read
extern __errno_location 

section .text

my_read:
  xor eax, eax
  syscall
  test eax, eax
  js .error
  ret

.error:
  neg eax
  mov edx, eax
  call __errno_location
  mov [rax], edx
  push -1
  pop rax
  ret

