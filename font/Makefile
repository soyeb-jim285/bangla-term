# Requires a Python with fonttools: make PYTHON=/path/to/venv/bin/python
PYTHON ?= python3
NOTO ?= /usr/share/fonts/noto
OUT := ../build

# Noto Sans Bengali scaled uniformly 1.15x so the matra sits near Latin cap
# height; at that size the median phrase still fits its glibc cells
# (tools/fill_ratio.py).
$(OUT)/BanglaTermNatural-Regular.ttf: condense.py
	mkdir -p $(OUT) && $(PYTHON) -I condense.py $(NOTO)/NotoSansBengali-Regular.ttf $@ 1.15 "Bangla Term Natural" 1.15

install: $(OUT)/BanglaTermNatural-Regular.ttf
	cp $< ~/.local/share/fonts/ && fc-cache -f ~/.local/share/fonts

.PHONY: install
