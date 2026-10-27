# Run inside patched kitty: KITTY_BENGALI=glibc kitty +runpy "exec(open('kitty/glibc-test.py').read())"
# glibc mode: kitty's width of every Bengali run in the corpus equals libc wcswidth.
import ctypes, re
from kitty.fast_data_types import wcswidth
libc = ctypes.CDLL('libc.so.6'); libc.setlocale(6, b'C.UTF-8')
libc.wcswidth.argtypes = [ctypes.c_wchar_p, ctypes.c_size_t]
runs = set(re.findall('[ঀ-৿][ঀ-৿ ]*', open('docs/bengali-test.txt', encoding='utf-8').read()))
bad = [r for r in runs if wcswidth(r) != libc.wcswidth(r, len(r))]
print(f'kitty glibc ok ({len(runs)} runs)' if not bad else f'kitty glibc FAILED: {bad[:5]}')
if bad: raise SystemExit(1)
