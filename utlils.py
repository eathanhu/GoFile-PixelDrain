import math


def human_readable_size(n: int) -> str:
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def progress_bar(now: int, total: int, length: int = 20) -> str:
    if total <= 0:
        return '[?]'
    frac = now/total
    done = int(frac*length)
    bar = '█'*done + '░'*(length-done)
    return f"[{bar}] {frac*100:5.1f}%"
