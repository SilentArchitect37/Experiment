// Gen III (English) character encoding.
const TABLE = new Map();
const put = (code, ch) => TABLE.set(code, ch);
put(0x00, ' ');
put(0x1B, 'é');
put(0x2D, '&');
put(0x34, 'Lv');
put(0x35, '=');
put(0x53, 'PK');
put(0x54, 'MN');
put(0x5A, 'Í');
put(0x5B, '%');
put(0x5C, '(');
put(0x5D, ')');
'0123456789'.split('').forEach((c, i) => put(0xA1 + i, c));
put(0xAB, '!'); put(0xAC, '?'); put(0xAD, '.'); put(0xAE, '-'); put(0xAF, '·');
put(0xB0, '…'); put(0xB1, '“'); put(0xB2, '”'); put(0xB3, '‘'); put(0xB4, '’');
put(0xB5, '♂'); put(0xB6, '♀'); put(0xB7, '$'); put(0xB8, ','); put(0xB9, '×');
put(0xBA, '/');
'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach((c, i) => put(0xBB + i, c));
'abcdefghijklmnopqrstuvwxyz'.split('').forEach((c, i) => put(0xD5 + i, c));
put(0xF0, ':');

const REVERSE = new Map();
for (const [code, ch] of TABLE) if (!REVERSE.has(ch)) REVERSE.set(ch, code);

export function decodeText(bytes, offset = 0, maxLen = bytes.length - offset) {
  let out = '';
  for (let i = 0; i < maxLen; i++) {
    const b = bytes[offset + i];
    if (b === 0xFF) break;
    out += TABLE.get(b) ?? '';
  }
  return out;
}

export function encodeText(str) {
  const out = [];
  for (const ch of str) {
    const code = REVERSE.get(ch);
    if (code === undefined) throw new Error(`Cannot encode character "${ch}"`);
    out.push(code);
  }
  return Uint8Array.from(out);
}
