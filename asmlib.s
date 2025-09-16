global putn
global exit_zero


section .text

; rbx -> string to write to stdout
; rcx -> length of the string
putn:
	mov rax,1
	mov rdi,1
	mov rsi,rbx
	mov rdx,rcx
	syscall

; exit with code zero
exit_zero:
	mov rax,60
	xor rdi,rdi
	syscall
