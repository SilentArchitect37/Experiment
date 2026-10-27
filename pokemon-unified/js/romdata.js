// Pulls display data (names, Pokédex numbers, growth rates, sprites) straight out of the
// player's own cartridge dumps, so nothing copyrighted ships with this project.
// Tables are located by content signatures rather than fixed addresses, which keeps this
// working across Ruby/Sapphire, Emerald and FireRed/LeafGreen revisions.
import { decodeText, encodeText } from './text.js';

export const SPECIES_COUNT = 412; // internal species ids 0..411
const ROM_BASE = 0x08000000;
// ITEMS_COUNT per engine, keyed by the second letter of the game code (AXVE, BPEE, BPRE...).
const ITEM_COUNTS = { AXVE: 349, AXPE: 349, BPEE: 377, BPRE: 375, BPGE: 375 };

export function gameCode(rom) {
  return String.fromCharCode(...rom.subarray(0xAC, 0xB0));
}

export function romTitle(rom) {
  return String.fromCharCode(...rom.subarray(0xA0, 0xAC)).replace(/\0+$/, '');
}

function indexOfBytes(hay, needle, from = 0) {
  const first = needle[0];
  const last = hay.length - needle.length;
  outer: for (let i = hay.indexOf(first, from); i !== -1 && i <= last; i = hay.indexOf(first, i + 1)) {
    for (let j = 1; j < needle.length; j++) if (hay[i + j] !== needle[j]) continue outer;
    return i;
  }
  return -1;
}

function terminated(str) {
  const enc = encodeText(str);
  const out = new Uint8Array(enc.length + 1);
  out.set(enc);
  out[enc.length] = 0xFF;
  return out;
}

// Finds a table of fixed-size text entries given its first two entries' names.
function findTextTable(rom, stride, entry0, entry1) {
  const needle = terminated(entry1);
  const head = encodeText(entry0);
  for (let at = indexOfBytes(rom, needle); at !== -1; at = indexOfBytes(rom, needle, at + 1)) {
    const base = at - stride;
    if (base >= 0 && head.every((b, i) => rom[base + i] === b)) return base;
  }
  throw new Error(`Could not find the "${entry1}" table in this ROM.`);
}

function readTextTable(rom, base, stride, count, len = stride) {
  return Array.from({ length: count }, (_, i) => decodeText(rom, base + i * stride, len));
}

const u16 = (rom, off) => rom[off] | (rom[off + 1] << 8);
const u32 = (rom, off) => (rom[off] | (rom[off + 1] << 8) | (rom[off + 2] << 16) | (rom[off + 3] << 24)) >>> 0;
const isRomPtr = p => p >= ROM_BASE && p < ROM_BASE + 0x2000000;

function findSpeciesToNational(rom) {
  // gSpeciesToNationalPokedexNum[species - 1]: begins 1, 2, 3, ... and Treecko (277) maps to 252.
  const needle = new Uint8Array(40);
  for (let i = 0; i < 20; i++) { needle[i * 2] = i + 1; }
  for (let at = indexOfBytes(rom, needle); at !== -1; at = indexOfBytes(rom, needle, at + 2)) {
    if (at % 2 === 0 && u16(rom, at + 250 * 2) === 251 && u16(rom, at + 276 * 2) === 252) {
      return Array.from({ length: SPECIES_COUNT }, (_, s) => (s === 0 ? 0 : u16(rom, at + (s - 1) * 2)));
    }
  }
  throw new Error('Could not find the national Pokédex table.');
}

function findBaseStats(rom) {
  // Bulbasaur: 45/49/49/45/65/65, Grass/Poison; entry 0 is blank and entries are 28 bytes.
  const needle = Uint8Array.from([45, 49, 49, 45, 65, 65, 12, 3]);
  for (let at = indexOfBytes(rom, needle); at !== -1; at = indexOfBytes(rom, needle, at + 1)) {
    const base = at - 28;
    if (base >= 0 && rom.subarray(base, base + 8).every(b => b === 0)) return base;
  }
  throw new Error('Could not find the base stats table.');
}

function findExpTables(rom) {
  // gExperienceTables[6][101] of u32; the medium-fast row (index 0) is n^3.
  const needle = new Uint8Array(24);
  [0, 1, 8, 27, 64, 125].forEach((n, i) => { needle[i * 4] = n; });
  const at = indexOfBytes(rom, needle);
  if (at === -1 || at % 4) throw new Error('Could not find the experience tables.');
  return Array.from({ length: 6 }, (_, g) => Array.from({ length: 101 }, (_, l) => u32(rom, at + (g * 101 + l) * 4)));
}

// A pointer table whose entries are {ptr, size, tag} (sprites) or {ptr, tag, pad} (palettes)
// with tag == species index (+ tagOffset).
function findTaggedTable(rom, tagAt, tagOffset, sizeCheck, from = 0) {
  for (let at = from; at + 8 * 40 < rom.length; at += 4) {
    let ok = true;
    for (let i = 1; i <= 30 && ok; i++) {
      const e = at + i * 8;
      ok = isRomPtr(u32(rom, e)) && u16(rom, e + tagAt) === i + tagOffset && sizeCheck(rom, e);
    }
    if (ok) return at;
  }
  return -1;
}

// GBA BIOS LZ77 (type 0x10).
export function lz77(rom, offset) {
  if (rom[offset] !== 0x10) throw new Error('Not LZ77 data');
  const size = rom[offset + 1] | (rom[offset + 2] << 8) | (rom[offset + 3] << 16);
  const out = new Uint8Array(size);
  let src = offset + 4;
  let dst = 0;
  while (dst < size) {
    const flags = rom[src++];
    for (let bit = 7; bit >= 0 && dst < size; bit--) {
      if (flags & (1 << bit)) {
        const b1 = rom[src++];
        const b2 = rom[src++];
        const len = (b1 >> 4) + 3;
        const disp = (((b1 & 0xF) << 8) | b2) + 1;
        for (let k = 0; k < len && dst < size; k++, dst++) out[dst] = out[dst - disp];
      } else {
        out[dst++] = rom[src++];
      }
    }
  }
  return out;
}

export function extractRomData(rom) {
  const speciesBase = findTextTable(rom, 11, '??????????', 'BULBASAUR');
  const moveBase = findTextTable(rom, 13, '-', 'POUND');
  const abilityBase = findTextTable(rom, 13, '-------', 'STENCH');
  const itemBase = findTextTable(rom, 44, '????????', 'MASTER BALL');
  const statsBase = findBaseStats(rom);
  const code = gameCode(rom);
  const itemCount = ITEM_COUNTS[code] ?? 349;
  const baseStats = Array.from({ length: SPECIES_COUNT }, (_, s) => {
    const o = statsBase + s * 28;
    return {
      stats: Array.from(rom.subarray(o, o + 6)),
      types: [rom[o + 6], rom[o + 7]],
      genderRatio: rom[o + 16],
      growth: rom[o + 19],
      abilities: [rom[o + 22], rom[o + 23]],
    };
  });
  return {
    code,
    speciesNames: readTextTable(rom, speciesBase, 11, SPECIES_COUNT),
    moveNames: readTextTable(rom, moveBase, 13, 355),
    abilityNames: readTextTable(rom, abilityBase, 13, 78),
    itemNames: readTextTable(rom, itemBase, 44, itemCount, 14),
    nationalDex: findSpeciesToNational(rom),
    baseStats,
    expTables: findExpTables(rom),
  };
}

// Decodes every species' front sprite (first 64x64 frame) as RGBA, normal and shiny.
export function extractSprites(rom) {
  const picTable = findTaggedTable(rom, 6, 0, (r, e) => u16(r, e + 4) >= 0x800);
  const palTable = findTaggedTable(rom, 4, 0, (r, e) => u16(r, e + 6) === 0);
  const shinyTable = findTaggedTable(rom, 4, 500, (r, e) => u16(r, e + 6) === 0);
  if (picTable < 0 || palTable < 0 || shinyTable < 0) throw new Error('Could not find sprite tables.');
  const palette = (table, s) => {
    const raw = lz77(rom, u32(rom, table + s * 8) - ROM_BASE);
    return Array.from({ length: 16 }, (_, i) => {
      const c = raw[i * 2] | (raw[i * 2 + 1] << 8);
      const ex = v => (v << 3) | (v >> 2);
      return [ex(c & 31), ex((c >> 5) & 31), ex((c >> 10) & 31), i === 0 ? 0 : 255];
    });
  };
  const sprites = [];
  for (let s = 1; s < SPECIES_COUNT; s++) {
    try {
      const tiles = lz77(rom, u32(rom, picTable + s * 8) - ROM_BASE);
      const pals = [palette(palTable, s), palette(shinyTable, s)];
      const [normal, shiny] = pals.map(pal => {
        const rgba = new Uint8ClampedArray(64 * 64 * 4);
        for (let t = 0; t < 64; t++) {
          const tx = (t % 8) * 8;
          const ty = Math.floor(t / 8) * 8;
          for (let p = 0; p < 64; p++) {
            const byte = tiles[t * 32 + (p >> 1)];
            const idx = p & 1 ? byte >> 4 : byte & 15;
            const o = ((ty + (p >> 3)) * 64 + tx + (p & 7)) * 4;
            rgba.set(pal[idx], o);
          }
        }
        return rgba;
      });
      sprites[s] = { normal, shiny };
    } catch {
      sprites[s] = null;
    }
  }
  return sprites;
}

export function levelFromExp(data, species, exp) {
  const table = data.expTables[data.baseStats[species]?.growth ?? 0];
  if (!table) return 1;
  let lvl = 1;
  while (lvl < 100 && exp >= table[lvl + 1]) lvl++;
  return lvl;
}
