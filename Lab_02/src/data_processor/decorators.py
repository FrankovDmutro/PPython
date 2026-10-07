import functools
import time

def measure_time(func):
    """Декоратор для заміру тривалості виконання операцій аналітики."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start_time
        print(f"[Таймінг] Функцію '{func.__name__}' виконано за {duration:.8f} с")
        return result
    return wrapper