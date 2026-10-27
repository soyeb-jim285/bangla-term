#!/bin/sh
# Open the bangla-term stack: patched kitty in glibc mode (Bengali gets the
# same per-codepoint widths as libc, so stock zsh/tmux/coreutils/less agree)
# with natural phrase shaping -> your zsh.
# Inside: `nvim` is the patched build (Neovim's own width tables otherwise disagree).
ROOT=$(cd "$(dirname "$0")" && pwd)
: "${KITTY_SRC:=$HOME/src/kitty}" "${BT_NVIM:=$HOME/src/neovim/build/bin/nvim}"
export BT_NVIM KITTY_BENGALI=glibc
export PATH="$ROOT/try/bin:$PATH"
export BAT_CONFIG_PATH="$ROOT/try/bat-config"
exec "$KITTY_SRC/kitty/launcher/kitty" --class bangla-term -d "$ROOT" \
    -o 'symbol_map U+0980-U+09FF Bangla Term Natural' \
    /usr/bin/zsh -o combiningchars "$@"
