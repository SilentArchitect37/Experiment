// Builds synthetic but structurally valid Gen III saves and Pokémon for tests.
import { sectorChecksum, SAVE_SIZE } from '../js/save.js';
import { encryptSubstructs } from '../js/pokemon.js';
import { encodeText } from '../js/text.js';

export function makeSave({ counter = 1, slot = 0, name = 'TEST', tid = 12345, sid = 54321, fill } = {}) {
  const bytes = new Uint8Array(SAVE_SIZE).fill(0xFF);
  writeSlot(bytes, slot, counter, sections => {
    sections[0].set(encodeText(name), 0);
    sections[0][encodeText(name).length] = 0xFF;
    new DataView(sections[0].buffer).setUint32(0x0A, ((sid << 16) | tid) >>> 0, true);
    fill?.(sections);
  });
  return bytes;
}

export function writeSlot(bytes, slot, counter, fill) {
  const sections = Array.from({ length: 14 }, () => new Uint8Array(0xF80));
  fill(sections);
  const v = new DataView(bytes.buffer);
  for (let id = 0; id < 14; id++) {
    const physical = (id + counter) % 14; // the game rotates sectors each save
    const base = (slot * 14 + physical) * 0x1000;
    bytes.fill(0, base, base + 0x1000);
    bytes.set(sections[id], base);
    v.setUint16(base + 0xFF4, id, true);
    v.setUint16(base + 0xFF6, sectorChecksum(bytes, base, 0xF80), true);
    v.setUint32(base + 0xFF8, 0x08012025, true);
    v.setUint32(base + 0xFFC, counter, true);
  }
}

export function makeMon({ pid = 0x12345678, otId = 0xBEEF1234, species = 25, item = 0, exp = 1000, nickname = 'PIKACHU' } = {}) {
  const raw = new Uint8Array(80);
  const v = new DataView(raw.buffer);
  v.setUint32(0, pid, true);
  v.setUint32(4, otId, true);
  raw.fill(0xFF, 8, 18);
  raw.set(encodeText(nickname), 8);
  raw[18] = 2;
  raw[19] = 2;
  raw.fill(0xFF, 20, 27);
  raw.set(encodeText('ASH'), 20);
  const s = new Uint8Array(48);
  const sv = new DataView(s.buffer);
  sv.setUint16(0, species, true);
  sv.setUint16(2, item, true);
  sv.setUint32(4, exp, true);
  sv.setUint16(12, 84, true); // Thundershock
  sv.setUint32(40, (31 | (30 << 5) | (29 << 10) | (28 << 15) | (27 << 20) | (26 << 25)) >>> 0, true);
  return encryptSubstructs(raw, s);
}

// Sets an event flag inside SaveBlock1, which spans sections 1-4.
export function setFlag(sections, flagsOffset, flag) {
  const at = flagsOffset + (flag >> 3);
  sections[1 + Math.floor(at / 0xF80)][at % 0xF80] |= 1 << (flag & 7);
}
