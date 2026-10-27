// Runs one cartridge in EmulatorJS and keeps its battery save in sync with the hub's storage.
import * as db from './db.js';
import { GAME_BY_ID } from './games.js';
import { Gen3Save } from './save.js';
import { EMULATORJS_DATA, FILTERS, DEFAULT_FILTER } from './config.js';

const params = new URLSearchParams(location.search);
const game = GAME_BY_ID[params.get('game')];
const statusEl = document.getElementById('status');
const status = msg => { statusEl.textContent = msg; };

const LOCK_INTERVAL = 3000;
let lastSaved = null;
let emulatorReady = false;

function sameBytes(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

async function persistSave() {
  if (!emulatorReady) return;
  const gm = window.EJS_emulator?.gameManager;
  const data = gm?.getSaveFile();
  if (!data || sameBytes(data, lastSaved)) return;
  try {
    new Gen3Save(data, game.engine); // only keep images the game itself would accept
  } catch {
    return; // e.g. before the first in-game save the flash is blank
  }
  lastSaved = Uint8Array.from(data);
  await db.put('saves', { bytes: lastSaved, updated: Date.now() }, game.id);
  status(`Saved ${new Date().toLocaleTimeString()}`);
}

async function heartbeat() {
  await db.put('meta', { game: game.id, at: Date.now() }, 'running');
}

async function start() {
  if (!game) { status('Unknown game.'); return; }
  document.getElementById('title').textContent = `Pokémon ${game.title}`;
  document.title = `Pokémon ${game.title} — Gen III Unified`;
  const rom = await db.get('roms', game.id);
  if (!rom) { status('This cartridge has not been added yet. Go back to the hub to add it.'); return; }
  const stored = await db.get('saves', game.id);
  const settings = (await db.get('meta', 'settings')) ?? {};
  const filter = FILTERS[settings.filter] ?? FILTERS[DEFAULT_FILTER];

  await heartbeat();
  setInterval(heartbeat, LOCK_INTERVAL);

  Object.assign(window, {
    EJS_player: '#game',
    EJS_core: 'gba',
    EJS_gameName: `pokemon-${game.id}`,
    EJS_gameID: game.code,
    EJS_gameUrl: URL.createObjectURL(new Blob([rom.bytes])),
    EJS_pathtodata: EMULATORJS_DATA,
    EJS_startOnLoaded: true,
    EJS_color: game.color,
    EJS_disableDatabases: true,
    EJS_defaultOptions: { shader: filter.shader },
    EJS_Buttons: { loadSavFiles: false, saveSavFiles: false },
    EJS_onGameStart: () => {
      const gm = window.EJS_emulator.gameManager;
      if (stored?.bytes) {
        const path = gm.getSaveFilePath();
        const dirs = path.split('/').slice(0, -1);
        let dir = '';
        for (const part of dirs) {
          if (!part) continue;
          dir += '/' + part;
          if (!gm.FS.analyzePath(dir).exists) gm.FS.mkdir(dir);
        }
        if (gm.FS.analyzePath(path).exists) gm.FS.unlink(path);
        gm.FS.writeFile(path, stored.bytes);
        gm.loadSaveFiles();
        gm.functions.restart(); // reboot so the game reads the injected save
        lastSaved = Uint8Array.from(stored.bytes);
        status('Save loaded');
      } else {
        status('New adventure — save in-game to keep progress');
      }
      emulatorReady = true;
      setInterval(persistSave, 4000);
    },
  });

  const script = document.createElement('script');
  script.src = EMULATORJS_DATA + 'loader.js';
  document.body.appendChild(script);
}

async function leave(e) {
  e?.preventDefault();
  await persistSave();
  await db.del('meta', 'running');
  location.href = 'index.html';
}

document.getElementById('back').addEventListener('click', leave);
window.addEventListener('pagehide', () => { persistSave(); db.del('meta', 'running'); });
document.addEventListener('visibilitychange', () => { if (document.hidden) persistSave(); });
start().catch(err => status(err.message));
