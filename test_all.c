#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>

int     my_strcmp(const char *s1, const char *s2);
char   *my_strcat(char *dest, const char *src);
char   *my_strchr(const char *s, int c);
int     my_toupper(int c);
ssize_t my_read(int fd, void *buf, size_t count);
void   *my_memset(void *s, int c, size_t n);
int     my_isalpha(int c);
int     my_puts(const char *s);

static int sgn(int x) { return (x > 0) - (x < 0); }

int main(void) {
    char buf[128];

    // --- my_strcmp ---
    assert(my_strcmp("abc", "abc") == 0);
    assert(my_strcmp("abc", "abd") < 0);
    assert(my_strcmp("abd", "abc") > 0);

    // --- my_memset ---
    my_memset(buf, 'A', 7);
    buf[7] = '\0';
    assert(strcmp(buf, "AAAAAAA") == 0);

    my_memset(buf, 0, sizeof buf);
    for (size_t i = 0; i < sizeof buf; ++i) assert(buf[i] == 0);

    // --- my_strcat ---
    strcpy(buf, "Hello");
    my_strcat(buf, " World");
    assert(strcmp(buf, "Hello World") == 0);

    strcpy(buf, "");
    my_strcat(buf, "abc");
    assert(strcmp(buf, "abc") == 0);

    // --- my_strrchr ---
    {
        const char *s = "abcabc";
        char *p = my_strchr(s, 'a');
        assert(p == (char*)s + 3);
    }
    assert(my_strchr("abc", 'z') == NULL);
    assert(*my_strchr("abc", '\0') == '\0');

    // --- my_toupper ---
    assert(my_toupper('a') == 'A');
    assert(my_toupper('z') == 'Z');
    assert(my_toupper('A') == 'A');
    assert(my_toupper('0') == '0');
    assert(my_toupper(-1) == -1);

    // --- my_isalpha ---
    assert(my_isalpha('A') != 0);
    assert(my_isalpha('Z') != 0);
    assert(my_isalpha('a') != 0);
    assert(my_isalpha('z') != 0);
    assert(my_isalpha('0') == 0);
    assert(my_isalpha('@') == 0); // 64
    assert(my_isalpha('[') == 0); // 91

    // --- my_puts ---
    int ret_puts = my_puts("my_puts test");
    assert(ret_puts >= 0);

    {
        char tmp[8];
        ssize_t r = my_read(-1, tmp, sizeof tmp);
        assert(r < 0);
    }
   

    return 0;
}

