#include <limits.h>
#include <stddef.h>
#include <stdio.h>

/* 学员只需实现这个函数，main 和测试输入由本文件提供。 */
int clamp_speed(int target_speed);

static int check_one(int input, int expected)
{
    int actual = clamp_speed(input);
    if (actual != expected)
    {
        printf("FAIL: input=%d, expected=%d, actual=%d\n", input, expected, actual);
        return 1;
    }
    return 0;
}

int main(void)
{
    const int inputs[] = {
        INT_MIN, INT_MIN + 1, -10000, -1001, -1000, -999, -1, 0,
        1, 999, 1000, 1001, 10000, INT_MAX - 1, INT_MAX
    };
    const int expected[] = {
        -1000, -1000, -1000, -1000, -1000, -999, -1, 0,
        1, 999, 1000, 1000, 1000, 1000, 1000
    };
    size_t count = 0;

    for (size_t i = 0; i < sizeof(inputs) / sizeof(inputs[0]); ++i)
    {
        if (check_one(inputs[i], expected[i]) != 0)
        {
            return 1;
        }
        ++count;
    }

    for (int input = -2000; input <= 2000; ++input)
    {
        int answer = input;
        if (answer < -1000)
        {
            answer = -1000;
        }
        else if (answer > 1000)
        {
            answer = 1000;
        }
        if (check_one(input, answer) != 0)
        {
            return 1;
        }
        ++count;
    }

    printf("PASS: %zu cases\n", count);
    return 0;
}
