global my_memset

section .text

my_memset:
  push rdx ; n
  pop rcx ; repetitions
  push rdi ; s saved
  push rdi ; location
  push rsi ; value
  pop rax ; to al
  pop rdi ; where
  rep stosb
  pop rax
  ret





