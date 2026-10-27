// Optional checks against real cartridges and real in-game saves. Nothing here is committed;
// point the env vars at your own files:
//   GEN3_ROM_DIR   folder with the .gba files
//   GEN3_FR_SAVE   a FireRed save made right after choosing Bulbasaur
//   GEN3_EM_SAVE   any Emerald save
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { extractRomData, extractSprites, gameCode, levelFromExp } from '../js/romdata.js';
import { Gen3Save } from '../js/save.js';
import { decodeBoxMon } from '../js/pokemon.js';
import { deposit, withdraw, listBoxes } from '../js/bank.js';

const { GEN3_ROM_DIR, GEN3_FR_SAVE, GEN3_EM_SAVE } = process.env;
const roms = GEN3_ROM_DIR ? readdirSync(GEN3_ROM_DIR).filter(f => f.endsWith('.gba')) : [];

test('extracts names, Pokédex numbers and sprites from every ROM', { skip: !roms.length && 'GEN3_ROM_DIR not set' }, () => {
  for (const f of roms) {
    const rom = new Uint8Array(readFileSync(join(GEN3_ROM_DIR, f)));
    const d = extractRomData(rom);
    assert.equal(d.speciesNames[1], 'BULBASAUR', f);
    assert.equal(d.speciesNames[277], 'TREECKO', f);
    assert.equal(d.nationalDex[277], 252, f);
    assert.equal(d.nationalDex[410], 386, f);
    assert.equal(d.moveNames[354], 'PSYCHO BOOST', f);
    assert.equal(d.itemNames[1], 'MASTER BALL', f);
    assert.equal(levelFromExp(d, 1, 135), 5, f);
    const sprites = extractSprites(rom);
    assert.equal(sprites.filter(Boolean).length, 411, f);
    assert.ok(['AXVE', 'AXPE', 'BPEE', 'BPRE', 'BPGE'].includes(gameCode(rom)));
  }
});

test('reads a real FireRed save with its starter', { skip: !GEN3_FR_SAVE && 'GEN3_FR_SAVE not set' }, () => {
  const bytes = new Uint8Array(readFileSync(GEN3_FR_SAVE));
  const save = new Gen3Save(bytes, 'frlg');
  assert.deepEqual(save.toBytes(), bytes, 'unchanged save must serialise byte-for-byte');
  const [starter] = save.party;
  const mon = decodeBoxMon(starter.raw);
  assert.equal(mon.species, 1);
  assert.equal(mon.checksumOk, true);
  assert.equal(mon.originGame, 4); // FireRed
  assert.equal(starter.level, 5);
});

test('moves a real Pokémon from FireRed into Emerald and back', { skip: !(GEN3_FR_SAVE && GEN3_EM_SAVE) && 'saves not set' }, () => {
  const fr = new Gen3Save(readFileSync(GEN3_FR_SAVE), 'frlg');
  const em = new Gen3Save(readFileSync(GEN3_EM_SAVE), 'e');
  deposit(fr, fr.party[0].raw); // simulate depositing the starter at a PC
  const raw = withdraw(fr, 0, 0);
  const spot = deposit(em, raw);
  const em2 = new Gen3Save(em.toBytes(), 'e');
  const moved = listBoxes(em2)[spot.box].slots[spot.slot].mon;
  assert.equal(moved.species, 1);
  assert.equal(moved.otName, decodeBoxMon(fr.party[0].raw).otName);
  assert.equal(listBoxes(new Gen3Save(fr.toBytes(), 'frlg'))[0].slots[0], null);
  assert.equal(em2.trainer.name, em.trainer.name);
});
