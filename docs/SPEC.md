# Bengali in the terminal: width rule and rendering

Status: prototype. Scope: Bengali (U+0980–U+09FF); the same approach applies
to the other Brahmic scripts.

## Problem

A terminal is a grid, and two parties compute text width: the application
(zsh, tmux, nvim) decides where the cursor goes, and the terminal decides
where glyphs are drawn. Today they disagree for Bengali:

| text      | kitty 0.49 (cells) | libc `wcswidth` | shaped width (cells, Noto Sans) |
|-----------|--------------------|-----------------|----------------------------------|
| কি        | 1                  | 2               | 1.79                             |
| ক্ষ       | 1                  | 2               | 1.43                             |
| বিজ্ঞান   | 3                  | 6               | 4.45                             |

kitty takes a cluster's width from its first codepoint, so it gives far fewer
cells than the shell expects and far fewer than the glyphs need. Glyphs are
squeezed or overlap, and the cursor lands inside letters.

## Width rule

**The terminal uses the widths programs already count with: glibc
`wcwidth()`, per codepoint.** 0 for U+0981, 09BC, 09C1–09C4, 09CD, 09E2–09E3,
09FE; 1 for every other assigned Bengali character. Equivalently: a cluster's
width is the sum of `wcwidth` over its codepoints.

zsh, bash, tmux (default), coreutils, less and Python already count this way,
so they need no change.

## Rendering

kitty (`KITTY_BENGALI=glibc`) gives each spacing character its own cell, but
shapes a whole Bengali phrase (words plus the single spaces between them, up
to 96 cells) as one HarfBuzz run. That gives natural conjuncts, reph and
vowel signs. The shaped phrase is then fitted into its cells: extra room goes
to the spaces (at most 2.5 cells per space), and the phrase is squeezed only
if it overflows. It starts and ends exactly on its grid cells, so pipes and
columns around it stay aligned.

Details that mattered for quality:

- No dotted circle: HarfBuzz is told not to insert U+25CC before a mark
  that starts a run.
- Bengali fonts are rendered unhinted. At small sizes TrueType hinting moves
  ra-phala and vowel signs away from where HarfBuzz placed them.
- Glyphs taller than the cell ascent (ঠ, reph, about 0.03 em) are clipped
  rather than shifted down, so the headline stays straight.

## Font

`font/condense.py` builds **Bangla Term Natural**: Noto Sans Bengali scaled
1.15x, with hinting stripped. Bengali reads small next to Latin at the same
point size; 1.15 puts the headline near Latin cap height. Its median phrase
fills about 0.93 of its glibc cells.

```
symbol_map U+0980-U+09FF Bangla Term Natural
```

Fill ratio (shaped width / allotted cells) with stock Noto Sans Bengali,
41 phrases from `docs/bengali-test.txt`, 0.6 em cell (`tools/fill_ratio.py`):

| width rule | median | p90 |
|---|---|---|
| kitty today (first codepoint) | 1.19 | 1.43 |
| Mc vowel signs = 0 (Bun/JS) | 1.09 | 1.36 |
| sum of wcwidth | 0.81 | 0.90 |

## Programs

Programs with their own width tables need a small patch to match glibc:

| program | stock model | fix |
|---------|-------------|-----|
| Neovim | cluster = first codepoint | `nvim/neovim-0.12.6-bengali-glibc.patch` (active when `KITTY_BENGALI=glibc`) |
| fzf / Go uniseg | glibc except U+09BE, 09D7 = 0 | `fzf/uniseg-0.4.7-bengali.patch` |
| bat / Rust unicode-width | glibc except U+09BE, 09D7 = 0 | let the terminal wrap: `--wrap=never` |
| tmux | glibc, unless `codepoint-widths` overrides it | do not override Bengali widths |
| opencode (OpenTUI) | grapheme widths | built-in `OPENTUI_FORCE_WCWIDTH=1` (set by `try/bin/opencode`) |
| Claude Code | Bun widths, plus a native cell segmenter in its own Bun build | `claude/osc66-proxy.js` wraps each grapheme in kitty's `OSC 66 ; w=<Bun width>` so kitty uses the cells Claude reserved (squeezed, but intact); under tmux, which drops OSC 66, it puts a ZWJ before each vowel sign Bun counts as 0, which tmux and patched kitty join into the previous cell |

## Verification

`make check` compares kitty's and Neovim's widths with libc `wcswidth` on
every line of `docs/bengali-test.txt`. Screenshots: `docs/screenshots/`.

## Known limitations

- Switched on by an env var and hardcoded to Bengali. Upstream, the rule
  should be script-general and negotiated (kitty#8533).
- `cat` output wraps at the row edge mid-word, like any wide text.
- Programs with non-glibc width tables (above) drift.
