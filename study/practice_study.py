# 简单的装饰器
import functools
import time

from study.decorator_study import log_decorator, timer_decorator


@log_decorator
@timer_decorator
def add(a: int, b: int) -> int:
    return a + b


def log_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f'开始调用函数 {func.__name__}')
        result = func(*args, **kwargs)
        print(f'函数 {func.__name__} 调用结束')
        print(f'函数调用结果: {result}')

    return wrapper

def time_decorator(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f'函数 {func.__name__} 执行时间: {end_time - start_time:.6f} 秒')
        return result

    return wrapper

if __name__ == '__main__':
    add(1, b=2)
