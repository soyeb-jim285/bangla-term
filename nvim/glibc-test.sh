#!/bin/sh
# Patched nvim in glibc mode: strdisplaywidth of every corpus line equals libc wcswidth.
NVIM=${1:-nvim}
KITTY_BENGALI=glibc "$NVIM" --headless --clean -c 'lua for _, l in ipairs(vim.fn.readfile("docs/bengali-test.txt")) do io.stdout:write(vim.fn.strdisplaywidth(l), "\n") end' -c q 2>/dev/null |
python3 -c '
import ctypes, sys
libc = ctypes.CDLL("libc.so.6"); libc.setlocale(6, b"C.UTF-8"); libc.wcswidth.argtypes = [ctypes.c_wchar_p, ctypes.c_size_t]
lines = open("docs/bengali-test.txt", encoding="utf-8").read().split("\n")[:-1]
got = [int(x) for x in sys.stdin.read().split()]
bad = [l for l, g in zip(lines, got) if libc.wcswidth(l, len(l)) != g]
assert len(got) == len(lines) and not bad, (len(got), len(lines), bad[:3])
print("nvim glibc ok")'
