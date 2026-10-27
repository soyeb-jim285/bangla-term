#!/bin/sh
# Check kitty and Neovim widths against libc wcswidth over docs/bengali-test.txt.
#   KITTY_SRC=~/src/kitty NVIM_BIN=~/src/neovim/build/bin/nvim ./check.sh
cd "$(dirname "$0")"; export LANG=C.UTF-8
pass=0; fail=0; skip=0
run() { name=$1; shift; if out=$("$@" 2>&1); then pass=$((pass+1)); echo "PASS $name"; else fail=$((fail+1)); echo "FAIL $name"; echo "$out" | sed 's/^/    /'; fi; }
skip() { skip=$((skip+1)); echo "SKIP $1 ($2)"; }

[ -x "${KITTY_SRC:-}/kitty/launcher/kitty" ] &&
  run kitty-glibc env KITTY_BENGALI=glibc "$KITTY_SRC/kitty/launcher/kitty" +runpy "exec(open('kitty/glibc-test.py').read())" ||
  skip kitty-glibc "set KITTY_SRC to a patched, built kitty"
[ -x "${NVIM_BIN:-}" ] && run nvim-glibc nvim/glibc-test.sh "$NVIM_BIN" || skip nvim-glibc "set NVIM_BIN to patched nvim"
echo "$pass passed, $fail failed, $skip skipped"; [ $fail -eq 0 ]
