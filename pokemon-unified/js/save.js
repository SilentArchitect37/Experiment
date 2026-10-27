// Gen III 128 KiB flash save: two slots of 14 sectors, each 4 KiB with a footer.
// Layout and checksum follow pokeemerald/pokefirered/pokeruby src/save.c.
import { BOX_MON_SIZE, PARTY_MON_SIZE } from './pokemon.js';
import { decodeText } from './text.js';
import { ENGINE_LAYOUT } from './games.js';

export const SAVE_SIZE = 0x20000;
const SECTOR_SIZE = 0x1000;
const SECTOR_DATA_SIZE = 0xF80;
const SECTORS_PER_SLOT = 14;
const SIGNATURE = 0x08012025;
const STORAGE_FIRST_SECTOR = 5;
const STORAGE_SIZE = 0x83D0;
export const BOX_COUNT = 14;
export const BOX_CAPACITY = 30;
const BOX_NAMES_OFFSET = 0x8344;

const view = bytes => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);

export function sectorChecksum(bytes, offset, size) {
  const v = view(bytes);
  let sum = 0;
  for (let i = 0; i < size; i += 4) sum = (sum + v.getUint32(offset + i, true)) >>> 0;
  return ((sum >>> 16) + sum) & 0xFFFF;
}

const dataSizeForSector = id => (id === 13 ? STORAGE_SIZE - 8 * SECTOR_DATA_SIZE : SECTOR_DATA_SIZE);

function readSlot(bytes, slot) {
  const v = view(bytes);
  const sectors = new Array(SECTORS_PER_SLOT);
  let counter = null;
  for (let i = 0; i < SECTORS_PER_SLOT; i++) {
    const base = (slot * SECTORS_PER_SLOT + i) * SECTOR_SIZE;
    if (v.getUint32(base + 0xFF8, true) !== SIGNATURE) return null;
    const id = v.getUint16(base + 0xFF4, true);
    if (id >= SECTORS_PER_SLOT || sectors[id] !== undefined) return null;
    // The game zero-fills each sector before copying data in, so summing the whole
    // data area gives the same result as summing only the block's real size.
    if (sectorChecksum(bytes, base, SECTOR_DATA_SIZE) !== v.getUint16(base + 0xFF6, true)) return null;
    const c = v.getUint32(base + 0xFFC, true);
    if (counter !== null && c !== counter) return null;
    counter = c;
    sectors[id] = base;
  }
  return { slot, counter, sectors };
}

function gather(bytes, sectors, first, count) {
  const out = new Uint8Array(count * SECTOR_DATA_SIZE);
  for (let i = 0; i < count; i++) {
    const base = sectors[first + i];
    out.set(bytes.subarray(base, base + SECTOR_DATA_SIZE), i * SECTOR_DATA_SIZE);
  }
  return out;
}

export class Gen3Save {
  constructor(input, engine) {
    let bytes = input instanceof Uint8Array ? input : new Uint8Array(input);
    // Some emulators append a footer (e.g. 16 bytes of RTC data); keep only the flash image.
    if (bytes.length < SAVE_SIZE) throw new Error(`Save is ${bytes.length} bytes; a Gen III save is 128 KiB.`);
    this.bytes = Uint8Array.from(bytes.subarray(0, SAVE_SIZE));
    this.trailer = Uint8Array.from(bytes.subarray(SAVE_SIZE));
    this.engine = engine;
    this.layout = ENGINE_LAYOUT[engine];
    if (!this.layout) throw new Error(`Unknown engine ${engine}`);
    const slots = [readSlot(this.bytes, 0), readSlot(this.bytes, 1)].filter(Boolean);
    if (!slots.length) throw new Error('No valid save slot found (empty or corrupted save).');
    // The game treats the counter as wrapping; the newer slot is the one with the larger counter.
    slots.sort((a, b) => ((b.counter - a.counter) | 0));
    this.active = slots[0];
    this._load();
  }

  _load() {
    const { sectors } = this.active;
    this.block2 = gather(this.bytes, sectors, 0, 1);
    this.block1 = gather(this.bytes, sectors, 1, 4);
    this.storage = gather(this.bytes, sectors, STORAGE_FIRST_SECTOR, 9).subarray(0, STORAGE_SIZE);
  }

  get trainer() {
    const b = this.block2;
    const v = view(b);
    const id = v.getUint32(0x0A, true);
    return {
      name: decodeText(b, 0, 7),
      gender: b[8] ? 'female' : 'male',
      tid: id & 0xFFFF,
      sid: id >>> 16,
      playTime: { hours: v.getUint16(0x0E, true), minutes: b[0x10], seconds: b[0x11] },
    };
  }

  flag(n) {
    return !!(this.block1[this.layout.flagsOffset + (n >> 3)] & (1 << (n & 7)));
  }

  get badges() {
    return Array.from({ length: 8 }, (_, i) => this.flag(this.layout.badge1Flag + i));
  }

  get champion() {
    return this.flag(this.layout.gameClearFlag);
  }

  // National Pokédex flags; bit n-1 is national number n.
  dexFlags(kind) {
    const start = kind === 'owned' ? 0x28 : 0x5C;
    return this.block2.subarray(start, start + 52);
  }

  get party() {
    const count = Math.min(6, this.block1[this.layout.partyCountOffset]);
    const mons = [];
    for (let i = 0; i < count; i++) {
      const off = this.layout.partyOffset + i * PARTY_MON_SIZE;
      mons.push({ raw: this.block1.slice(off, off + BOX_MON_SIZE), level: this.block1[off + 84] });
    }
    return mons;
  }

  get currentBox() {
    return this.storage[0];
  }

  boxName(box) {
    return decodeText(this.storage, BOX_NAMES_OFFSET + box * 9, 9);
  }

  boxMonOffset(box, slot) {
    return 4 + (box * BOX_CAPACITY + slot) * BOX_MON_SIZE;
  }

  getBoxMon(box, slot) {
    const off = this.boxMonOffset(box, slot);
    return this.storage.slice(off, off + BOX_MON_SIZE);
  }

  setBoxMon(box, slot, raw) {
    if (raw && raw.length !== BOX_MON_SIZE) throw new Error('A box Pokémon is 80 bytes.');
    this.storage.set(raw ?? new Uint8Array(BOX_MON_SIZE), this.boxMonOffset(box, slot));
  }

  // Serialises the edited PC storage back into the active slot and returns a new save image.
  toBytes() {
    const out = Uint8Array.from(this.bytes);
    const v = view(out);
    const { sectors } = this.active;
    for (let i = 0; i < 9; i++) {
      const id = STORAGE_FIRST_SECTOR + i;
      const base = sectors[id];
      const size = dataSizeForSector(id);
      out.fill(0, base, base + SECTOR_DATA_SIZE);
      out.set(this.storage.subarray(i * SECTOR_DATA_SIZE, i * SECTOR_DATA_SIZE + size), base);
      v.setUint16(base + 0xFF6, sectorChecksum(out, base, SECTOR_DATA_SIZE), true);
    }
    if (!this.trailer.length) return out;
    const full = new Uint8Array(out.length + this.trailer.length);
    full.set(out);
    full.set(this.trailer, out.length);
    return full;
  }
}
