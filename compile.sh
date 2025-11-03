#!/usr/bin/env sh
set -e
nasm -felf64 my_strcmp.s   -o my_strcmp.o
nasm -felf64 my_strcat.s   -o my_strcat.o
nasm -felf64 my_strrchr.s  -o my_strrchr.o
nasm -felf64 my_toupper.s  -o my_toupper.o
nasm -felf64 my_read.s     -o my_read.o
nasm -felf64 my_memset.s   -o my_memset.o
nasm -felf64 my_isalpha.s  -o my_isalpha.o
nasm -felf64 my_puts.s     -o my_puts.o

gcc -Wall -Wextra -O2 test_all.c my_*.o -o test_all
./test_all

