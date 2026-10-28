// Run a Bun TUI (Claude Code) in a pty and tell kitty how wide its Bengali is.
//   bun osc66-proxy.js claude [args...]
// Under tmux it marks Bun-zero-width vowel signs with ZWJ instead (see zwj).
// Claude Code lays text out with Bun.stringWidth, which counts Bengali vowel
// signs as 0 (বিজ্ঞান = 4 cells, libc says 6). Instead of changing the app,
// wrap every Bengali grapheme it prints in kitty's text-sizing escape
// OSC 66 ; w=<Bun width> ; <grapheme> so the terminal gives it exactly the
// cells the app reserved. Needs kitty >= 0.40; looks best in glibc mode.
const BN = /[ঀ-৿]/;
const RUN = /[ঀ-৿‌‍]+/g;
const seg = new Intl.Segmenter(undefined, { granularity: 'grapheme' });

// Bun counts these 0 cells, glibc (tmux, kitty) 1. tmux cannot pass OSC 66, so
// under tmux put a ZWJ before each: tmux then joins it into the previous cell,
// and patched kitty (glibc mode) does the same. Bun widths are glibc widths
// with exactly these zeroed (checked on docs/bengali-test.txt).
const BUN_ZERO = /[\u0980\u0982\u09BE-\u09C0\u09C7\u09C8\u09CB\u09CC\u09D7]/g;
const zwj = (text) => text.replace(BUN_ZERO, '\u200D$&');

const osc66 = (text) =>
  text.replace(RUN, (run) => {
    let out = '';
    for (const { segment: g } of seg.segment(run)) {
      const w = Bun.stringWidth(g);
      // ponytail: OSC 66 takes w=1..7; a 0-width lone mark passes through as is.
      out += w > 0 && w <= 7 && BN.test(g) ? `\x1b]66;w=${w};${g}\x07` : g;
    }
    return out;
  });
const wrap = process.env.TMUX && process.argv[2] !== '--test' ? zwj : osc66;

// Split output into escape sequences (passed through untouched) and text.
// Returns [transformed, leftover]: an unfinished escape or a trailing Bengali
// run (its grapheme may continue in the next chunk) is held back.
const ESC = /\x1b(?:\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]|[\]PX^_][\s\S]*?(?:\x07|\x1b\\)|(?![[\]PX^_])[\x20-\x2f]*[\x30-\x7e])/g;
function transform(s) {
  let out = '', last = 0, m;
  ESC.lastIndex = 0;
  while ((m = ESC.exec(s))) {
    out += wrap(s.slice(last, m.index)) + m[0];
    last = ESC.lastIndex;
  }
  let rest = s.slice(last);
  const esc = rest.indexOf('\x1b');
  let hold = '';
  if (esc >= 0) [rest, hold] = [rest.slice(0, esc), rest.slice(esc)];
  else {
    const tail = rest.match(/[ঀ-৿‌‍]+$/);
    if (tail) [rest, hold] = [rest.slice(0, tail.index), tail[0]];
  }
  return [out + wrap(rest), hold];
}

if (process.argv[2] === '--test') {
  const eq = (a, b) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`); };
  eq(transform('a \x1b[31mকি\x1b[0m'), ['a \x1b[31m\x1b]66;w=1;কি\x07\x1b[0m', '']);
  eq(transform('জ্ঞা x'), ['\x1b]66;w=2;জ্ঞা\x07 x', '']);
  eq(transform('\x1b]0;বাংলা\x07ok'), ['\x1b]0;বাংলা\x07ok', '']); // OSC payload untouched
  eq(transform('ab\x1b[3'), ['ab', '\x1b[3']); // unfinished escape held back
  eq(transform('x ক'), ['x ', 'ক']); // trailing grapheme may continue
  eq(zwj('কিং বা'), 'ক\u200Dি\u200Dং ব\u200Dা');
  console.log('osc66-proxy ok');
  process.exit(0);
}

const decoder = new TextDecoder();
let pending = '', timer;
const flush = () => {
  timer = undefined;
  if (pending) process.stdout.write(wrap(pending)), (pending = '');
};

const proc = Bun.spawn(process.argv.slice(2), {
  env: process.env,
  terminal: {
    cols: process.stdout.columns || 80,
    rows: process.stdout.rows || 24,
    data(_, bytes) {
      clearTimeout(timer);
      const [out, hold] = transform(pending + decoder.decode(bytes, { stream: true }));
      if (out) process.stdout.write(out);
      pending = hold;
      if (pending) timer = setTimeout(flush, 5);
    },
  },
});

process.stdin.setRawMode?.(true);
process.stdin.on('data', (d) => proc.terminal.write(d));
process.stdout.on('resize', () => proc.terminal.resize(process.stdout.columns, process.stdout.rows));
await proc.exited;
process.stdin.setRawMode?.(false);
process.exit(proc.exitCode ?? 0);
