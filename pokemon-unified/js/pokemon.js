// Gen III BoxPokemon (80 bytes): header + 48 bytes of encrypted, shuffled substructures.
import { decodeText } from './text.js';

export const BOX_MON_SIZE = 80;
export const PARTY_MON_SIZE = 100;

// Substructure order for PID % 24 (G = growth, A = attacks, E = EVs/condition, M = misc).
const ORDERS = [
  'GAEM', 'GAME', 'GEAM', 'GEMA', 'GMAE', 'GMEA', 'AGEM', 'AGME', 'AEGM', 'AEMG', 'AMGE', 'AMEG',
  'EGAM', 'EGMA', 'EAGM', 'EAMG', 'EMGA', 'EMAG', 'MGAE', 'MGEA', 'MAGE', 'MAEG', 'MEGA', 'MEAG',
];

export const NATURES = [
  'Hardy', 'Lonely', 'Brave', 'Adamant', 'Naughty', 'Bold', 'Docile', 'Relaxed', 'Impish', 'Lax',
  'Timid', 'Hasty', 'Serious', 'Jolly', 'Naive', 'Modest', 'Mild', 'Quiet', 'Bashful', 'Rash',
  'Calm', 'Gentle', 'Sassy', 'Careful', 'Quirky',
];

export const ORIGIN_GAMES = { 1: 'Sapphire', 2: 'Ruby', 3: 'Emerald', 4: 'FireRed', 5: 'LeafGreen', 15: 'Colosseum/XD' };

const view = bytes => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);

export function isEmptySlot(raw) {
  const v = view(raw);
  return v.getUint32(0, true) === 0 && v.getUint32(4, true) === 0 && raw[19] === 0;
}

// Returns the 48 decrypted bytes rearranged into canonical G, A, E, M order.
export function decryptSubstructs(raw) {
  const v = view(raw);
  const pid = v.getUint32(0, true);
  const key = (pid ^ v.getUint32(4, true)) >>> 0;
  const plain = new Uint8Array(48);
  const pv = view(plain);
  for (let i = 0; i < 48; i += 4) pv.setUint32(i, (v.getUint32(32 + i, true) ^ key) >>> 0, true);
  const order = ORDERS[pid % 24];
  const out = new Uint8Array(48);
  for (const [canonical, letter] of ['G', 'A', 'E', 'M'].entries()) {
    const pos = order.indexOf(letter);
    out.set(plain.subarray(pos * 12, pos * 12 + 12), canonical * 12);
  }
  return out;
}

export function substructChecksum(canonical) {
  const v = view(canonical);
  let sum = 0;
  for (let i = 0; i < 48; i += 2) sum = (sum + v.getUint16(i, true)) & 0xFFFF;
  return sum;
}

// Re-shuffles and encrypts canonical substructures into a copy of raw, refreshing the checksum.
export function encryptSubstructs(raw, canonical) {
  const out = Uint8Array.from(raw.subarray(0, BOX_MON_SIZE));
  const v = view(out);
  const pid = v.getUint32(0, true);
  const key = (pid ^ v.getUint32(4, true)) >>> 0;
  const order = ORDERS[pid % 24];
  const shuffled = new Uint8Array(48);
  for (const [canonical_i, letter] of ['G', 'A', 'E', 'M'].entries()) {
    shuffled.set(canonical.subarray(canonical_i * 12, canonical_i * 12 + 12), order.indexOf(letter) * 12);
  }
  const sv = view(shuffled);
  for (let i = 0; i < 48; i += 4) v.setUint32(32 + i, (sv.getUint32(i, true) ^ key) >>> 0, true);
  v.setUint16(28, substructChecksum(canonical), true);
  return out;
}

export function decodeBoxMon(raw) {
  if (isEmptySlot(raw)) return null;
  const v = view(raw);
  const pid = v.getUint32(0, true);
  const otId = v.getUint32(4, true);
  const flags = raw[19];
  const s = decryptSubstructs(raw);
  const sv = view(s);
  const checksumOk = substructChecksum(s) === v.getUint16(28, true);
  const ivWord = sv.getUint32(36 + 4, true);
  const origins = sv.getUint16(36 + 2, true);
  const shinyValue = ((otId >>> 16) ^ (otId & 0xFFFF) ^ (pid >>> 16) ^ (pid & 0xFFFF)) & 0xFFFF;
  return {
    pid, otId,
    tid: otId & 0xFFFF, sid: otId >>> 16,
    nickname: decodeText(raw, 8, 10),
    language: raw[18],
    isBadEgg: !!(flags & 1) || !checksumOk,
    hasSpecies: !!(flags & 2),
    isEggFlag: !!(flags & 4),
    otName: decodeText(raw, 20, 7),
    species: sv.getUint16(0, true),
    heldItem: sv.getUint16(2, true),
    experience: sv.getUint32(4, true),
    friendship: s[9],
    moves: [0, 1, 2, 3].map(i => sv.getUint16(12 + i * 2, true)),
    evs: Array.from(s.subarray(24, 30)),
    metLocation: s[37],
    metLevel: origins & 0x7F,
    originGame: (origins >> 7) & 0xF,
    ball: (origins >> 11) & 0xF,
    otGender: origins >> 15,
    ivs: [0, 5, 10, 15, 20, 25].map(shift => (ivWord >>> shift) & 31),
    isEgg: !!((ivWord >>> 30) & 1),
    abilitySlot: (ivWord >>> 31) & 1,
    nature: NATURES[pid % 25],
    shiny: shinyValue < 8,
    checksumOk,
  };
}

// Returns a copy of raw with the held item replaced.
export function withHeldItem(raw, itemId) {
  const s = decryptSubstructs(raw);
  view(s).setUint16(2, itemId, true);
  return encryptSubstructs(raw, s);
}
