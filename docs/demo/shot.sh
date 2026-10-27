#!/bin/sh
# shot.sh KITTY_BIN TAG [env...] : run demo in a fixed-size kitty, screenshot to TAG.png
K=$1; T=$2; shift 2
S=$PWD/$T.sock; rm -f $S
env "$@" setsid $K --class bt-$T -o allow_remote_control=yes --listen-on unix:$S -o font_size=14 \
  -o 'symbol_map U+0980-U+09FF Noto Sans Bengali' -o remember_window_size=no -o initial_window_width=760 -o initial_window_height=300 \
  -d "$(dirname "$(realpath "$0")")" /usr/bin/zsh -o combiningchars >/dev/null 2>&1 &
sleep 3
R() { ~/src/kitty/kitty/launcher/kitty @ --to unix:$S "$@"; }
R send-text 'clear; command cat demo.txt; echo\r'; sleep 1
R send-text 'echo বিজ্ঞান ও প্রযুক্তি বিশ্ববিদ্যালয়'; sleep .5
R send-key left left left left left left left left left left left left left; sleep 1
g=$(hyprctl clients -j | python3 -c "import json,sys;c=[c for c in json.load(sys.stdin) if c['class']=='bt-$T'][0];print('%d,%d %dx%d'%(*c['at'],*c['size']))")
grim -g "$g" $T.png
for p in $(hyprctl clients -j | python3 -c "import json,sys;[print(c['pid']) for c in json.load(sys.stdin) if c['class']=='bt-$T']"); do kill $p; done
