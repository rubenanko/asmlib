#!/usr/bin/python3 -u

import os
import sys
from pathlib import Path
import subprocess
import pickle
from pprint import pprint

funcs = {
        # "bzero": (7, 14), NO
        "isalpha": (10, 18), # XXX 15 OK
        "puts": (39, 63), # XXX OK
        "read": (22, 28), # XXX OK
        "strcat": (17, 25), # XXX 40 OK
        "strcmp": (16, 26), # XXX 24 OK
        "toupper": (12, 20), # XXX 13 NO DEMO

        "memset": (9, 17), # XXX 19 OK
        # "isalpha": (11, 22), # XXX 15 OK
        # "puts": (39, 78), # XXX OK
        # "read": (23, 33.0), # XXX OK

        # "strlen": (14, 20), # 14 NO
        # "atoi": (47, 90), # badly defined (handle newlines? handle '+' chr ?, ...) NO
        # "abs": (8, 16), # 8 NO
        # "strchr": (19, 35), # XXX 21 NO
        "strrchr": (20, 34), # XXX 29 OK

        }

nasm_template = """
global my_%s
section .text
my_%s:
    ret
"""

correction_c_template = r"""
#define _gnu_source
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <strings.h>
#include <assert.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <time.h>
#include <immintrin.h>


// prototypes
size_t abi_check(void *func, size_t num_args, ...);

int num_tests = 0;
int num_errors = 0;

#define TEST_FUNC(name, func) \
    else if (!strcmp(argv[1], name)) { \
        func(); \
    }

#define expect(expr, msg, ...) \
    do \
    { \
        num_tests++; \
        if (!(expr)) \
        { \
            fprintf(stderr, "\033[0;31m%s failed  (test %d, line %d): \033[1;33m%s\033[0m (\033[0;31m" msg "\033[0m)\n", __func__, num_tests, __LINE__, #expr, __VA_ARGS__); \
            num_errors++; \
        } \
        else \
        { \
            fprintf(stderr, "\033[0;32m%s success (test %d, line %d): \033[1;32m%s\033[0m (\033[0;32m" msg "\033[0m)\n", __func__, num_tests, __LINE__, #expr, __VA_ARGS__); \
        } \
    } while(0)

int rdrand32() {
    unsigned int _rand32;
    // Utilisation de l'instruction RDRAND
    int success = _rdrand32_step(&_rand32);
    if (!success) {
        fprintf(stderr, "RDRAND instruction failed, CALL THE TEACHER\n");
        exit(1);
    }
    return (int)_rand32;
}


#ifdef MY_toupper
int my_toupper(int c);
#define ABICHECK_my_toupper(c) (int)abi_check(my_toupper, 1, (int)c)
void test_toupper () {
    unsigned int c = 0x00;
    while (c < 256) {
        expect(
                toupper(c) == ABICHECK_my_toupper(c),
                "c=%02hhx", c
                );
        c++;
    }
}
#endif

#ifdef MY_isalpha
int my_isalpha(int c);
#define ABICHECK_my_isalpha(c) (int)abi_check(my_isalpha, 1, (int)c)
void test_isalpha () {
    unsigned int c = 0x00;
    while (c < 256) {
        expect(
                !!isalpha(c) == !!ABICHECK_my_isalpha(c),
                "c=%02hhx", c
                );
        c++;
    }
}
#endif

#ifdef MY_puts
int c_diff(const char *path1, const char *path2) {
    FILE *f1, *f2;
    int ch1, ch2;

    f1 = fopen(path1, "r");
    if (f1 == NULL) {
        perror("Erreur lors de l'ouverture du premier fichier");
        exit(1);
    }

    f2 = fopen(path2, "r");
    if (f2 == NULL) {
        perror("Erreur lors de l'ouverture du deuxième fichier");
        fclose(f1);
        exit(1);
    }

    while (1) {
        ch1 = fgetc(f1);
        ch2 = fgetc(f2);

        if (ch1 != ch2) {
            fclose(f1);
            fclose(f2);
            return 1; // Les fichiers sont différents
        }

        if (ch1 == EOF && ch2 == EOF) {
            break; // Les deux fichiers ont été lus jusqu'à la fin
        }
    }

    fclose(f1);
    fclose(f2);
    return 0; // Les fichiers sont identiques
}
int my_puts(const char *s);
#define ABICHECK_my_puts(s) (int)abi_check(my_puts, 1, (char*)s)
void test_puts () {
    int ret1, ret2;
    char *puts_string;

    puts_string = "hello world\n\0\x01";
    freopen("/tmp/asmtest1", "w", stdout);
    ret1 = puts(puts_string);
    fflush(stdout);
    freopen("/tmp/asmtest2", "w", stdout);
    ret2 = ABICHECK_my_puts(puts_string);
    fflush(stdout);
    freopen("/dev/tty", "w", stdout);
    assert(ret1 >= 0);
    expect(ret2 >= 0,
            "hello world", 0); // check return
    expect(c_diff("/tmp/asmtest1", "/tmp/asmtest2") == 0,
            "hello world", 0); // check written
                               //

    puts_string = "";
    freopen("/tmp/asmtest1", "w", stdout);
    ret1 = puts(puts_string);
    fflush(stdout);
    freopen("/tmp/asmtest2", "w", stdout);
    ret2 = ABICHECK_my_puts(puts_string);
    fflush(stdout);
    freopen("/dev/tty", "w", stdout);
    assert(ret1 >= 0);
    expect(ret2 >= 0,
            "EMPTY", 0); // check return
    expect(c_diff("/tmp/asmtest1", "/tmp/asmtest2") == 0,
            "EMPTY", 0); // check written

    char bigbuf[150000] = {0};
    memset(bigbuf, 0xff, 0x1ffff);
    puts_string = bigbuf;
    freopen("/tmp/asmtest1", "w", stdout);
    ret1 = puts(puts_string);
    fflush(stdout);
    freopen("/tmp/asmtest2", "w", stdout);
    ret2 = ABICHECK_my_puts(puts_string);
    fflush(stdout);
    freopen("/dev/tty", "w", stdout);
    assert(ret1 >= 0);
    expect(ret2 >= 0,
            "0xff * 85535", 0); // check return
    expect(c_diff("/tmp/asmtest1", "/tmp/asmtest2") == 0,
            "0xff * 85535", 0); // check written

    puts_string = "hello world\n\n\0\xff";
    fclose(stdout);
    ret1 = puts(puts_string);
    ret2 = ABICHECK_my_puts(puts_string);
    freopen("/dev/tty", "w", stdout);
    assert(ret1 == EOF);
    expect(ret2 == EOF,
            "write helloworld to closed fd (ebadf), ret=%p", ret2); // check return
                                                                    //
    puts_string = "";
    fclose(stdout);
    ret1 = puts(puts_string);
    ret2 = ABICHECK_my_puts(puts_string);
    freopen("/dev/tty", "w", stdout);
    assert(ret1 == EOF);
    expect(ret2 == EOF,
            "write EMPTY str to closed fd (ebadf), ret=%p", ret2); // check return
}
#endif

#ifdef MY_read
ssize_t my_read(int fd, void *buf, size_t count);
#define ABICHECK_my_read(fd, buf, count) (ssize_t)abi_check(my_read, 3, (int)fd, (void*)buf, (size_t)count)
void test_read () {
    int fd;
    char buf1[150000] = {0};
    char buf2[150000] = {0};
    ssize_t ret1, ret2;

    fd = open("/etc/passwd", O_RDONLY, 0666);
    memset(buf1, '\0', 150000);
    memset(buf2, '\0', 150000);
    assert(!lseek(fd, 0, SEEK_SET));
    ret1 = read(fd, buf1, 0x1ffff);
    assert(!lseek(fd, 0, SEEK_SET));
    ret2 = ABICHECK_my_read(fd, buf2, 0x1ffff);
    assert(ret1 > 4);
    expect(
            ret1 == ret2,
            "read /etc/passwd, ret=%d", ret2 // check return
          );
    expect(
            !memcmp(buf1, buf2, 150000),
            "read /etc/passwd", 0); // check buf
    close(fd);


    fd = open("/dev/zero", O_RDONLY, 0666);
    memset(buf1, 'a', 150000);
    memset(buf2, 'a', 150000);
    ret1 = read(fd, buf1, 0x1ffff);
    ret2 = ABICHECK_my_read(fd, buf2, 0x1ffff);
    assert(ret1 == 0x1ffff);
    expect(
            ret1 == ret2,
            "read /dev/zero, ret=%d", ret2 // check return
          );
    expect(
            !memcmp(buf1, buf2, 150000),
            "read /dev/zero", 0); // check buf
    close(fd);


    fd = open("/dev/null", O_RDONLY, 0666);
    memset(buf1, '0', 150000);
    memset(buf2, '0', 150000);
    ret1 = read(fd, buf1, 0x1ffff);
    ret2 = ABICHECK_my_read(fd, buf2, 0x1ffff);
    assert(ret1 == 0);
    expect(
            ret1 == ret2,
            "read /dev/null, ret=%d", ret2 // check return
          );
    expect(
            !memcmp(buf1, buf2, 150000),
            "read /dev/null", 0
            ); // check buf
    close(fd);
                                  //
    fd = open("/dev", O_RDONLY, 0666);
    errno = 0;
    ret1 = read(fd, buf1, 0x1ffff);
    assert(errno == EISDIR);
    errno = 0;
    ret2 = ABICHECK_my_read(fd, buf2, 0x1ffff);
    assert(ret1 == -1);
    expect(
            ret1 == ret2,
            "read /dev directory, ret=%d", ret2 // check return
          );
    expect(
            errno == EISDIR,
            "read /dev directory, errno=%d", errno // check errno
          );
    expect(
            !memcmp(buf1, buf2, 150000),
            "read /dev directory", 0
            ); // check buf
    close(fd);

    fd = open("/etc/passwd", O_RDONLY, 0666);
    errno = 0;
    ret1 = read(fd, (char*)0xffffff, 0x1ffff);
    assert(errno == EFAULT);
    errno = 0;
    ret2 = ABICHECK_my_read(fd, (char*)0xffffff, 0x1ffff);
    assert(ret1 == -1);
    expect(
            ret1 == ret2,
            "read info invalid buf, ret=%d", ret2 // check return
          );
    expect(
            errno == EFAULT,
            "read into invalid buf, errno=%d", errno // check errno
          );
    close(fd);
}
#endif

#ifdef MY_bzero
void my_bzero(void *s, size_t n);
#define ABICHECK_my_bzero(s, n) (void)abi_check(my_bzero, 2, (void*)s, (size_t)n)
void test_bzero () {
    char buf1[150000];
    char buf2[150000];

    memset(buf1, 'a', 150000);
    memset(buf2, 'a', 150000);

    bzero(buf1, 256);
    ABICHECK_my_bzero(buf2, 256);
    expect(
            !memcmp(buf1, buf2, 150000),
            "small buf", 0
            );

    bzero(buf1+1000, 0x1ffff);
    ABICHECK_my_bzero(buf2+1000, 0x1ffff);
    expect(
            !memcmp(buf1, buf2, 150000),
            "big buf", 0
            );
};
#endif

#ifdef MY_strcat
char *my_strcat(char *restrict dst, const char *restrict src);
#define ABICHECK_my_strcat(dst, src) (char*)abi_check(my_strcat, 2, (char*)dst, (char*)src)
void test_strcat () {
    char buf1[300000];
    char buf2[300000];
    char suffix[0x1ffff+1];
    char *ret2;

    memset(buf1, '\0', 300000);
    memset(buf2, '\0', 300000);
    memset(suffix+1, 0xfd, 0x1ffff-1);
    strcat(buf1, "hello world");
    ret2 = ABICHECK_my_strcat(buf2, "hello world");
    expect(
            ret2 == buf2,
            "check return", 0);
    expect(
            !memcmp(buf1, buf2, 300000),
            "check mem", 0
            );


    strcat(buf1, "hello world");
    ret2 = ABICHECK_my_strcat(buf2, "hello world");
    expect(
            ret2 == buf2,
            "check return", 0);
    expect(
            !memcmp(buf1, buf2, 300000),
            "check mem", 0
            );

    buf1[5] = '\0';
    buf2[5] = '\0';
    strcat(buf1, "hello world");
    ret2 = ABICHECK_my_strcat(buf2, "hello world");
    expect(
            ret2 == buf2,
            "check return", 0);
    expect(
            !memcmp(buf1, buf2, 300000),
            "check mem", 0
            );

    strcat(buf1, suffix);
    ret2 = ABICHECK_my_strcat(buf2, suffix);
    expect(
            ret2 == buf2,
            "check return", 0);
    expect(
            !memcmp(buf1, buf2, 300000),
            "check mem", 0
            );

    strcat(buf1, suffix);
    ret2 = ABICHECK_my_strcat(buf2, suffix);
    expect(
            ret2 == buf2,
            "check return", 0);
    expect(
            !memcmp(buf1, buf2, 300000),
            "check mem", 0
            );

    buf1[5] = '\0';
    buf2[5] = '\0';
    strcat(buf1, "hello world");
    ret2 = ABICHECK_my_strcat(buf2, "hello world");
    expect(
            ret2 == buf2,
            "check return", 0);
    expect(
            !memcmp(buf1, buf2, 300000),
            "check mem", 0
            );
}
#endif

#ifdef MY_strlen
size_t my_strlen(const char *s);
#define ABICHECK_my_strlen(s) (size_t)abi_check(my_strlen, 1, (char*)s)
void test_strlen () {
    char buf1[300000];

    expect(
            strlen("a") == ABICHECK_my_strlen("a"),
            "check_mem", 0);
    expect(
            strlen(buf1) == ABICHECK_my_strlen(buf1),
            "check_mem", 0);

    int i = 30;
    while (i) {
        int val = (rand() % 0x1ffff) + 1;
        memset(buf1, val, val);
        buf1[val] = '\0';
        expect(
                strlen(buf1) == ABICHECK_my_strlen(buf1),
                "check_mem", 0);
        i--;
    }


}
#endif

#ifdef MY_strchr
char *my_strchr(const char *s, int c);
#define ABICHECK_my_strchr(s, c) (char*)abi_check(my_strchr, 2, (char*)s, (int)c)
void test_strchr () {
    char buf1[300000];

    char *str = "bonjour";
    expect(
            ABICHECK_my_strchr(str, 'o') == str+1,
            "bonjour ? o", 0);
    expect(
            ABICHECK_my_strchr(str, 'u') == NULL,
            "bonjour ? u", 0);
    expect(
            ABICHECK_my_strchr(str, 'b') == str,
            "bonjour ? b", 0);
    expect(
            ABICHECK_my_strchr(str, 'r') == str+6,
            "bonjour ? r", 0);

    int i = 256;
    while (i) {
        int val = (rand() % 0x1ffff) + 1;
        memset(buf1, val, val);
        buf1[val] = '\0';
        buf1[rand() % val] = val-1;
        expect(
                strchr(buf1, val-1) == ABICHECK_my_strchr(buf1, val-1),
                "check_mem %p (%02hhx)", strchr(buf1, val-1), val-1);
        i--;
    }


}
#endif

#ifdef MY_strrchr
char *my_strrchr(const char *s, int c);
#define ABICHECK_my_strrchr(s, c) (char*)abi_check(my_strrchr, 2, (char*)s, (int)c)
void test_strrchr () {
    char buf1[300000];

    char *str = "bonjour\0xbonjour";
    expect(
            ABICHECK_my_strrchr(str, 'o') == str+4,
            "bonjour ? o", 0);
    expect(
            ABICHECK_my_strrchr(str, 'U') == NULL,
            "bonjour ? u", 0);
    expect(
            ABICHECK_my_strrchr(str, 'b') == str,
            "bonjour ? b", 0);
    expect(
            ABICHECK_my_strrchr(str, 'r') == str+6,
            "bonjour ? r", 0);
    expect(
            ABICHECK_my_strrchr(str, '\0') == str+7,
            "bonjour ? 0x0", 0);
    expect(
            ABICHECK_my_strrchr(str, 'x') == NULL,
            "bonjour ? x", 0);

    int i = 256;
    while (i) {
        int val = (rand() % 0x1ffff) + 1;
        memset(buf1, val, val);
        buf1[val] = '\0';
        buf1[rand() % val] = val-1;
        expect(
                strrchr(buf1, val-1) == ABICHECK_my_strrchr(buf1, val-1),
                "check_mem %p (%02hhx)", strrchr(buf1, val-1), val-1);
        i--;
    }
}
#endif

#ifdef MY_atoi
int my_atoi(const char *nptr);
#define ABICHECK_my_atoi(nptr) (int)abi_check(my_atoi, 1, (char*)nptr)
void test_atoi () {
    int c = 200;
    while (c--) {
        int rand32 = rdrand32();
        char rand32_str[20];
        snprintf(rand32_str, 20, "%d", rand32);
        expect(
                atoi(rand32_str) == ABICHECK_my_atoi(rand32_str),
                "rd=%d", rand32);
    }
    c = 0;
    while (c < 256) {
        char str[20];
        snprintf(str, 20, "%d%c", 0, c);
        expect(atoi(str) == ABICHECK_my_atoi(str),
                "test 0 (%02hhx)", c);

        snprintf(str, 20, "%d%c", -1, c);
        expect(atoi(str) == ABICHECK_my_atoi(str),
                "test -1 (%02hhx)", c);

        snprintf(str, 20, "%d%c", 0x7fffffff, c);
        expect(atoi(str) == ABICHECK_my_atoi(str),
                "test INT_MAX (%02hhx)", c);

        snprintf(str, 20, "%d%c", 0x80000000, c);
        expect(atoi(str) == ABICHECK_my_atoi(str),
                "test INT_MIN (%02hhx)", c);
        c++;
    }
    /* expect(1==2, "%d", atoi("9999999999999999999999999999999999999999999")); */
}
#endif

#ifdef MY_abs
int my_abs(int j);
#define ABICHECK_my_abs(j) (int)abi_check(my_abs, 1, (int)j)
void test_abs () {
    int c = 200;
    while (c--) {
        int rand32 = rdrand32();
        expect(
                abs(rand32) == ABICHECK_my_abs(rand32),
                "rd=%d", rand32);
    }
    expect(abs(0) == ABICHECK_my_abs(0),
            "test 0", 0);
    expect(abs(-1) == ABICHECK_my_abs(-1),
            "test -1", 0);
    expect(abs(0x7fffffff) == ABICHECK_my_abs(0x7fffffff),
            "test INT_MAX", 0);
    expect(abs(0x80000000) == ABICHECK_my_abs(0x80000000),
            "test INT_MIN", 0);
}
#endif

#ifdef MY_strcmp
int wr(int val) {
    if (val < 0) return -1;
    if (val > 0) return 1;
    return 0;
}
int my_strcmp(const char *s1, const char *s2);
#define ABICHECK_my_strcmp(s1, s2) (int)abi_check(my_strcmp, 2, (char*)s1, (char*)s2)
void test_strcmp () {
    int ret1, ret2;

    char buf1[0x1ffff+1] = {0};
    char buf2[0x1ffff+1] = {0};

    expect(
            wr(strcmp(buf1-100, buf1-100)) == wr(ABICHECK_my_strcmp(buf1-100, buf1-100)),
            "cmp same ptr", 0
            );

    strcat(buf1, "hello world");
    strcat(buf2, "hello world");
    expect(
            wr(strcmp(buf1, buf2)) == wr(ABICHECK_my_strcmp(buf1, buf2)),
            "cmp same data", 0
            );

    memset(buf1, '\0', 0x1ffff);
    memset(buf2, '\0', 0x1ffff);
    expect(
            wr(strcmp(buf1, buf2)) == wr(ABICHECK_my_strcmp(buf1, buf2)),
            "cmp same data", 0
            );

    strcat(buf1, "aaaa");
    strcat(buf2, "zzzz");
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp smaller data (ret1=%d, ret2=%d)", ret1, ret2
            );
    strcat(buf1, "zzzz");
    strcat(buf2, "aaaa");
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp smaller data (ret1=%d, ret2=%d)", ret1, ret2
            );

    strcpy(buf1, "zzzz");
    strcpy(buf2, "aaaa");
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp bigger data (ret1=%d, ret2=%d)", ret1, ret2
            );

    strcpy(buf1, "\x02");
    strcpy(buf2, "\x01");
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp bigger data (ret1=%d, ret2=%d)", ret1, ret2
            );

    strcpy(buf1, "\xfe");
    strcpy(buf2, "\xff");
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp smaller data (ret1=%d, ret2=%d)", ret1, ret2
            );

    memset(buf1, '\x80', 0x1ffff);
    memset(buf2, '\x80', 0x1ffff);
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp equal data (ret1=%d, ret2=%d)", ret1, ret2
            );

    buf1[0x1ffff] = '\x81';
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp bigger data (ret1=%d, ret2=%d)", ret1, ret2
            );

    buf2[0x1ffff] = '\x86';
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp smaller data (ret1=%d, ret2=%d)", ret1, ret2
            );

    buf2[1] = 0x00;
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp bigger data (ret1=%d, ret2=%d)", ret1, ret2
            );

    buf1[1] = 0x00;
    ret1 = strcmp(buf1, buf2);
    ret2 = ABICHECK_my_strcmp(buf1, buf2);
    expect(
            wr(ret1) == wr(ret2),
            "cmp equal data (ret1=%d, ret2=%d)", ret1, ret2
            );
}
#endif

#ifdef MY_memset
void *my_memset(void *s, int c, size_t n);
#define ABICHECK_my_memset(s, c, n) (void*)abi_check(my_memset, 3, (void*)s, (int)c, (size_t)n)
void test_memset() {
    unsigned int c = 0x00;
    while (c < 256) {
        char buf1[150000];
        char buf2[150000];
        memset(buf1, 'a', 150000);
        memset(buf2, 'a', 150000);

        expect(
                buf1 == memset(buf1, c, 256) &&
                buf2 == ABICHECK_my_memset(buf2, c, 256),
                "small buf retval (%02hhx)", c);
        expect(
                !memcmp(buf1, buf2, 150000),
                "small buf (%02hhx)", c);


        expect(
                buf1+1000 == memset(buf1+1000, c, 0x1ffff) &&
                buf2+1000 == ABICHECK_my_memset(buf2+1000, c, 0x1ffff),
                "big buf retval (%02hhx)", c);
        expect(
                !memcmp(buf1, buf2, 150000),
                "big buf (%02hhx)", c);
        c++;
    }
}
#endif

int main(int argc, char **argv) {
    srand(time(NULL));
    if (argc == 2) {
        printf("testing %s\n", argv[1]);
        if (0) {
            ;
        }
        #ifdef MY_toupper
        TEST_FUNC("toupper", test_toupper)
        #endif
        #ifdef MY_bzero
        TEST_FUNC("bzero", test_bzero)
        #endif
        #ifdef MY_isalpha
        TEST_FUNC("isalpha", test_isalpha)
        #endif
        #ifdef MY_puts
        TEST_FUNC("puts", test_puts)
        #endif
        #ifdef MY_read
        TEST_FUNC("read", test_read)
        #endif
        #ifdef MY_strcat
        TEST_FUNC("strcat", test_strcat)
        #endif
        #ifdef MY_strcmp
        TEST_FUNC("strcmp", test_strcmp)
        #endif
        #ifdef MY_atoi
        TEST_FUNC("atoi", test_atoi)
        #endif
        #ifdef MY_memset
        TEST_FUNC("memset", test_memset)
        #endif
        #ifdef MY_strlen
        TEST_FUNC("strlen", test_strlen)
        #endif
        #ifdef MY_abs
        TEST_FUNC("abs", test_abs)
        #endif
        #ifdef MY_strchr
        TEST_FUNC("strchr", test_strchr)
        #endif
        #ifdef MY_strrchr
        TEST_FUNC("strrchr", test_strrchr)
        #endif
        else {
            printf("usage: %s [function]\n", argv[0]);
            printf("example: %s strcmp\n", argv[0]);
            exit(1);
        }

        if (!num_errors) {
            fprintf(stderr, "\033[32mall %d tests succeeded\033[0m\n", num_tests);
            return 0;
        }
        else {
            fprintf(stderr, "\033[31m%d of %d tests failed !\033[0m\n", num_errors, num_tests);
            return 1;
        }
    }
}
"""

abi_template = """
; size_t abi_check(void *func, size_t num_args, size_t arg1, size_t arg2, size_t arg3);
global abi_check

%macro  multipush 1-*
  %rep  %0
  %rotate -1
    push %1
  %endrep
%endmacro

%macro  multipop 1-*
  %rep %0
    pop %1
  %rotate 1
  %endrep
%endmacro

%define  override_val 0xaaaaaaaaaaaaaaaa

%macro  reg_override 1-*
  %rep %0
    mov %1, override_val
  %rotate 1
  %endrep
%endmacro

%macro  randomize 1-*
  %rep %0
    rdrand %1
  %rotate 1
  %endrep
%endmacro

%define STACK_RBX QWORD [rsp+(8*5)]
%define STACK_RCX QWORD [rsp+(8*6)]
%define STACK_RDX QWORD [rsp+(8*7)]
%define STACK_RSI QWORD [rsp+(8*8)]
%define STACK_RDI QWORD [rsp+(8*9)]
%define STACK_RSP QWORD [rsp+(8*10)]
%define STACK_RBP QWORD [rsp+(8*11)]
%define STACK_R8  QWORD [rsp+(8*12)]
%define STACK_R9  QWORD [rsp+(8*13)]
%define STACK_R10 QWORD [rsp+(8*14)]
%define STACK_R11 QWORD [rsp+(8*15)]
%define STACK_R12 QWORD [rsp+(8*16)]
%define STACK_R13 QWORD [rsp+(8*17)]
%define STACK_R14 QWORD [rsp+(8*18)]
%define STACK_R15 QWORD [rsp+(8*19)]

%define STACK_FUNCPTR   STACK_RDI
%define STACK_NUM_ARGS  STACK_RSI
%define STACK_ARG1      STACK_RDX
%define STACK_ARG2      STACK_RCX
%define STACK_ARG3      STACK_R8

%define STACK_RAND      STACK_RCX

section .text

abi_check:

.backup_registers:
    multipush rbx, rcx, rdx, rsi, rdi, rsp, rbp, r8, r9, r10, r11, r12, r13, r14, r15


.override_registers:
    randomize rax, rbx, rcx, rdx, rsi, rdi, r8, r9, r10, r11, r12, r13, r14, r15


.randomize_non_volatile:
    multipush rbx, r12, r13, r14, r15

.set_args:
    ; set arg1
    cmp STACK_NUM_ARGS, 1
    jb .call_function
    mov rdi, STACK_ARG1
    ; set arg2
    cmp STACK_NUM_ARGS, 2
    jb .call_function
    mov rsi, STACK_ARG2
    ; set arg3
    cmp STACK_NUM_ARGS, 3
    jb .call_function
    mov rdx, STACK_ARG3


.call_function:
    call STACK_FUNCPTR


.check_nonvolatile_registers:
    mov rdi, STACK_RSP
    sub rdi, 0x58
    cmp rsp, rdi
    jne .return_error

    cmp rbp, STACK_RBP
    jne .return_error

    pop rdi
    cmp rbx, rdi
    jne .return_error

    pop rdi
    cmp r12, rdi
    jne .return_error

    pop rdi
    cmp r13, rdi
    jne .return_error

    pop rdi
    cmp r14, rdi
    jne .return_error

    pop rdi
    cmp r15, rdi
    jne .return_error


.check_direction_flag_is_clear:
    pushf
    pop rdi
    bt rdi, 10
    jc .return_error


.return_func_result:
    multipop rbx, rcx, rdx, rsi, rdi, rsp, rbp, r8, r9, r10, r11, r12, r13, r14, r15
    ret


.return_error:
    multipop rbx, rcx, rdx, rsi, rdi, rsp, rbp, r8, r9, r10, r11, r12, r13, r14, r15
    rdrand rax
    ret
"""

RM=True
WORKING_EXO_POINTS = 8
COMPACT_EXO_POINTS = 12


if True or not Path("test_functions").is_file():
    os.system("rm -f my_*.o abi_check.o ./test_functions")

    abi = Path("abi_check.s")
    if not abi.is_file():
        abi.write_text(abi_template)
    os.system(f"nasm -f elf64 abi_check.s -o abi_check.o")
    if RM:
        os.system(f"rm abi_check.s")

    for func in funcs:
        path = Path("my_"+func+".s")
        if not path.exists():
            path.write_text(nasm_template.replace("%s", func))
        os.system(f"nasm -f elf64 my_{func}.s -o my_{func}.o")
    objs = " ".join(f"my_{f}.o" for f in funcs)
    macros = " ".join(f"-D MY_{f}" for f in funcs)

    correction_c = Path("correction.c")
    if not correction_c.is_file():
        correction_c.write_text(correction_c_template)
    os.system(f"gcc -march=native -fno-builtin -no-pie -g {objs} abi_check.o correction.c {macros} -o test_functions")
    if RM:
        os.system(f"rm correction.c")
        os.system(f"rm abi_check.o")

    assert Path("test_functions").is_file()

NOTES = {}

all_functions_work = True
for func in funcs:
    note = 0
    # external functions are forbidden (exept for __errno_location)
    if os.system(f"objdump -x my_{func}.o | grep -v __errno_location | grep -q UND") != 0:
        if os.system(f"./test_functions {func}") == 0:
            note = WORKING_EXO_POINTS;
    NOTES[func] = note
    if not note:
        all_functions_work = False
if RM:
    os.system(f"rm test_functions")

report = open("REPORT.txt", 'w')
size_data = {}
XP_DELTA = 2
for func, note in NOTES.items():
    ideal_sz = funcs[func][0]
    worst_sz = funcs[func][1]
    ret, out = subprocess.getstatusoutput(f"size -A -d my_{func}.o | grep ^Total | grep -o '[0-9]\\+$'")
    assert ret == 0
    student_sz = int(out.split()[0])
    
    function_works = "OK" if note else "FAIL !"

    print(file=report)
    print(f"SIZE OF YOUR {func}:   {student_sz} ({function_works})", file=report)
    print(f"IDEAL SIZE FOR {func}: {ideal_sz}", file=report)
    # if not all_functions_work or student_sz > worst_sz:
    if not note or student_sz > worst_sz:
        print(f"extra points for {func}: 0", file=report)
    else:
        points_per_byte = COMPACT_EXO_POINTS / (worst_sz - ideal_sz)
        extra_points = (worst_sz - student_sz)
        extra_points *= points_per_byte
        # extra points divided by 2 if not all functions work
        if not all_functions_work:
            extra_points /= 4
            print(f"extra points for {func}: {extra_points:.2f} (75% decrease because not all functions work)", file=report)
        else:
            print(f"extra points for {func}: {extra_points:.2f}", file=report)
        NOTES[func] += extra_points

    if NOTES[func] > 0:
        size_data[func] = (ideal_sz, student_sz)


print("\n\n============== CALCULATING YOUR NOTE ================", file=report)
total = 0
for func, note in NOTES.items():
    print(f"got {note:.2f}/20 for {func}", file=report)
    total += note
glob_note = round(total / len(NOTES), 2)
print(f"GLOBAL NOTE: {glob_note}/20", file=report)
report.close()

open("NOTE.txt", 'w').write(str(glob_note))

with open('DATA.pickle', 'wb') as f:
    pickle.dump(
            {
                "note": glob_note,
                "size_data": size_data
            }, f)

if RM:
    os.system("cat REPORT.txt")
    os.system(f"rm REPORT.txt")
    os.system(f"rm NOTE.txt")
    os.system(f"rm DATA.pickle")
