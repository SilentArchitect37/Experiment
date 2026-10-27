import { test } from 'node:test';
import assert from 'node:assert/strict';
import { Gen3Save } from '../js/save.js';
import { decodeBoxMon, decryptSubstructs, encryptSubstructs, withHeldItem } from '../js/pokemon.js';
import { deposit, withdraw, firstEmptySlot, listBoxes } from '../js/bank.js';
import { summarize, campaign } from '../js/profile.js';
import { decodeText, encodeText } from '../js/text.js';
import { makeSave, makeMon, writeSlot, setFlag } from './helpers.mjs';

test('text encoding round-trips', () => {
  const s = 'Mr. MIME é ♂♀ 0123!?';
  assert.equal(decodeText(Uint8Array.from([...encodeText(s), 0xFF])), s);
});

test('Pokémon encryption round-trips for every substructure order', () => {
  for (let order = 0; order < 24; order++) {
    const raw = makeMon({ pid: 0x1000 * 24 + order, species: 100 + order });
    const mon = decodeBoxMon(raw);
    assert.equal(mon.species, 100 + order);
    assert.equal(mon.checksumOk, true);
    assert.deepEqual(mon.ivs, [31, 30, 29, 28, 27, 26]);
    assert.deepEqual(encryptSubstructs(raw, decryptSubstructs(raw)), raw);
  }
});

test('changing the held item keeps the Pokémon valid', () => {
  const raw = makeMon({ item: 0x177 });
  const mon = decodeBoxMon(withHeldItem(raw, 0));
  assert.equal(mon.heldItem, 0);
  assert.equal(mon.checksumOk, true);
  assert.equal(mon.species, 25);
});

test('parses a synthetic save and picks the newest slot', () => {
  const bytes = makeSave({ counter: 7, slot: 0, name: 'OLD' });
  writeSlot(bytes, 1, 8, sections => { sections[0].set([...encodeText('NEW'), 0xFF]); });
  const save = new Gen3Save(bytes, 'e');
  assert.equal(save.active.slot, 1);
  assert.equal(save.trainer.name, 'NEW');
});

test('rejects blank and corrupted saves', () => {
  assert.throws(() => new Gen3Save(new Uint8Array(0x20000).fill(0xFF), 'e'), /No valid save slot/);
  const bytes = makeSave();
  bytes[5 * 0x1000 + 10] ^= 1; // corrupt one data byte
  // The other slot is blank, so the save is now unreadable.
  assert.throws(() => new Gen3Save(bytes, 'e'), /No valid save slot/);
});

test('deposit and withdraw survive serialisation', () => {
  const save = new Gen3Save(makeSave(), 'frlg');
  const spot = deposit(save, makeMon());
  assert.deepEqual([spot.box, spot.slot], [0, 0]);
  const reread = new Gen3Save(save.toBytes(), 'frlg');
  assert.equal(listBoxes(reread)[0].slots[0].mon.nickname, 'PIKACHU');
  const raw = withdraw(reread, 0, 0);
  assert.equal(decodeBoxMon(raw).species, 25);
  assert.deepEqual(firstEmptySlot(reread), { box: 0, slot: 0 });
  // Untouched sectors must be byte-identical.
  const original = makeSave();
  assert.deepEqual(new Gen3Save(original, 'frlg').toBytes(), original);
});

test('items that do not exist in Ruby/Sapphire are stripped on deposit', () => {
  const save = new Gen3Save(makeSave(), 'rs');
  const result = deposit(save, makeMon({ item: 0x176 }));
  assert.equal(result.notes.length, 1);
  assert.equal(decodeBoxMon(save.getBoxMon(0, 0)).heldItem, 0);
  const ok = deposit(save, makeMon({ item: 0x0D }));
  assert.equal(ok.notes.length, 0);
});

test('box fills up and reports when full', () => {
  const save = new Gen3Save(makeSave(), 'e');
  for (let i = 0; i < 14 * 30; i++) deposit(save, makeMon({ pid: i + 1 }));
  assert.throws(() => deposit(save, makeMon()), /full/);
});

test('profile merges badges, Pokédex and campaign progress', () => {
  const fr = new Gen3Save(makeSave({ fill: s => {
    // FireRed: flags at SaveBlock1+0xEE0, badges 0x820.., game clear 0x82C.
    for (let b = 0; b < 8; b++) setFlag(s, 0xEE0, 0x820 + b);
    setFlag(s, 0xEE0, 0x82C);
    s[0][0x28] = 0b111; // owns #1-#3
  } }), 'frlg');
  const em = new Gen3Save(makeSave({ fill: s => {
    // Emerald: flags at SaveBlock1+0x1270; badge 1 = 0x867.
    setFlag(s, 0x1270, 0x867);
    s[0][0x28] = 0b110; // owns #2-#3
    s[0][0x28 + 31] = 0x80; // owns #256
  } }), 'e');
  const sum = summarize({ firered: fr, emerald: em });
  assert.equal(sum.badgeCount, 9);
  assert.equal(sum.ownedCount, 4);
  assert.equal(sum.champion.Kanto, true);
  const chapters = campaign(sum);
  assert.deepEqual(chapters.map(c => [c.done, c.unlocked]), [[true, true], [false, true], [false, false]]);
});
