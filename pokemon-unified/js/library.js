// Loading cartridges and saves into the browser's storage and keeping hub state in sync.
import * as db from './db.js';
import { GAMES, GAME_BY_ID } from './games.js';
import { gameCode, extractRomData, extractSprites } from './romdata.js';
import { Gen3Save } from './save.js';
import { isZip, unzip } from './zip.js';

const RUNNING_STALE_MS = 10000;
const BACKUPS_PER_GAME = 10;
const DATA_SOURCE_ORDER = ['emerald', 'firered', 'leafgreen', 'ruby', 'sapphire'];

// Accepts .gba/.zip ROMs and .sav files; returns a list of human-readable results.
export async function importFiles(fileList) {
  const results = [];
  for (const file of fileList) {
    try {
      let bytes = new Uint8Array(await file.arrayBuffer());
      let name = file.name;
      if (isZip(bytes)) {
        const entry = (await unzip(bytes)).find(f => /\.(gba|sav)$/i.test(f.name));
        if (!entry) throw new Error('No .gba or .sav file inside this ZIP.');
        bytes = await entry.read();
        name = entry.name;
      }
      if (/\.sav$/i.test(name) || bytes.length === 0x20000 || bytes.length === 0x20010) {
        results.push({ ok: false, message: `${file.name}: to import a save, use the "Import save" button on that game's card.` });
        continue;
      }
      const code = gameCode(bytes);
      const game = GAMES[code];
      if (!game) throw new Error(`Not a supported cartridge (game code "${code}"). Use USA/Europe Ruby, Sapphire, Emerald, FireRed or LeafGreen.`);
      await db.put('roms', { bytes, name, added: Date.now() }, game.id);
      results.push({ ok: true, message: `Added Pokémon ${game.title}.` });
    } catch (err) {
      results.push({ ok: false, message: `${file.name}: ${err.message}` });
    }
  }
  return results;
}

export async function importSave(gameId, file) {
  const game = GAME_BY_ID[gameId];
  const bytes = new Uint8Array(await file.arrayBuffer());
  const save = new Gen3Save(bytes, game.engine); // throws if it isn't a valid Gen III save
  await backupSave(gameId, 'Before importing a save file');
  await db.put('saves', { bytes, updated: Date.now() }, gameId);
  return save.trainer;
}

export async function backupSave(gameId, reason) {
  const current = await db.get('saves', gameId);
  if (!current) return;
  await db.put('backups', { game: gameId, bytes: current.bytes, at: Date.now(), reason });
  const mine = (await db.all('backups')).filter(b => b.game === gameId).sort((a, b) => b.at - a.at);
  for (const old of mine.slice(BACKUPS_PER_GAME)) await db.del('backups', old.id);
}

export async function runningGame() {
  const r = await db.get('meta', 'running');
  return r && Date.now() - r.at < RUNNING_STALE_MS ? r.game : null;
}

export async function loadState() {
  const romKeys = new Set(await db.keys('roms'));
  const saves = {};
  const saveErrors = {};
  for (const game of Object.values(GAMES)) {
    const rec = await db.get('saves', game.id);
    if (!rec) continue;
    try {
      saves[game.id] = new Gen3Save(rec.bytes, game.engine);
    } catch (err) {
      saveErrors[game.id] = err.message;
    }
  }
  const bank = await db.all('bank');
  const settings = { filter: 'hd4x', hdSprites: true, ...((await db.get('meta', 'settings')) ?? {}) };
  return { roms: romKeys, saves, saveErrors, bank, settings };
}

let romDataPromise = null;
let romDataSource = null;
export async function loadRomData(romKeys) {
  const source = DATA_SOURCE_ORDER.find(id => romKeys.has(id));
  if (!source) return null;
  if (source !== romDataSource) {
    romDataSource = source;
    romDataPromise = db.get('roms', source).then(rec => ({
      source,
      ...extractRomData(rec.bytes),
      sprites: extractSprites(rec.bytes),
    }));
  }
  return romDataPromise;
}

export async function writeSave(gameId, save, reason) {
  await backupSave(gameId, reason);
  await db.put('saves', { bytes: save.toBytes(), updated: Date.now() }, gameId);
}
