// Moving Pokémon between cartridges. Pure functions over Gen3Save, so they are unit-testable.
import { BOX_COUNT, BOX_CAPACITY } from './save.js';
import { decodeBoxMon, isEmptySlot, withHeldItem } from './pokemon.js';
import { ENGINE_LAYOUT } from './games.js';

export function listBoxes(save) {
  return Array.from({ length: BOX_COUNT }, (_, box) => ({
    name: save.boxName(box),
    slots: Array.from({ length: BOX_CAPACITY }, (_, slot) => {
      const raw = save.getBoxMon(box, slot);
      return isEmptySlot(raw) ? null : { raw, mon: decodeBoxMon(raw) };
    }),
  }));
}

export function firstEmptySlot(save, preferBox = save.currentBox) {
  for (let i = 0; i < BOX_COUNT; i++) {
    const box = (preferBox + i) % BOX_COUNT;
    for (let slot = 0; slot < BOX_CAPACITY; slot++) {
      if (isEmptySlot(save.getBoxMon(box, slot))) return { box, slot };
    }
  }
  return null;
}

// Removes a Pokémon from a PC slot and returns its raw 80 bytes.
export function withdraw(save, box, slot) {
  const raw = save.getBoxMon(box, slot);
  if (isEmptySlot(raw)) throw new Error('That PC slot is empty.');
  const mon = decodeBoxMon(raw);
  if (mon.isBadEgg) throw new Error('This is a Bad Egg (corrupted data); it cannot be moved.');
  save.setBoxMon(box, slot, null);
  return raw;
}

// Adapts a Pokémon for a target engine. Returns the bytes to store and any notes for the player.
export function adaptForEngine(raw, engine) {
  const mon = decodeBoxMon(raw);
  const notes = [];
  if (mon.heldItem > ENGINE_LAYOUT[engine].lastItemId) {
    notes.push('Its held item does not exist in this game, so the item was removed.');
    return { raw: withHeldItem(raw, 0), notes, removedItem: mon.heldItem };
  }
  return { raw, notes, removedItem: 0 };
}

export function deposit(save, raw, target = null) {
  const spot = target ?? firstEmptySlot(save);
  if (!spot) throw new Error('Every PC box in this game is full.');
  if (!isEmptySlot(save.getBoxMon(spot.box, spot.slot))) throw new Error('That PC slot is occupied.');
  const adapted = adaptForEngine(raw, save.engine);
  save.setBoxMon(spot.box, spot.slot, adapted.raw);
  return { ...spot, ...adapted };
}
