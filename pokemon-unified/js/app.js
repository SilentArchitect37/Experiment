// Hub UI: journey, cartridges, combined Pokédex, the Bank and settings.
import * as db from './db.js';
import { GAMES, GAME_BY_ID, BADGES } from './games.js';
import { Gen3Save, BOX_COUNT, BOX_CAPACITY } from './save.js';
import { decodeBoxMon, ORIGIN_GAMES } from './pokemon.js';
import { listBoxes, withdraw, deposit, firstEmptySlot } from './bank.js';
import { summarize, campaign, hasDex } from './profile.js';
import { levelFromExp } from './romdata.js';
import { spriteUrl } from './sprites.js';
import { FILTERS } from './config.js';
import * as lib from './library.js';
import { titleCase, formatPlayTime, escapeHtml as h, download, BALLS, STAT_NAMES, TYPES } from './format.js';

const GAME_ORDER = ['firered', 'leafgreen', 'emerald', 'ruby', 'sapphire'];
const view = document.getElementById('view');

const state = {
  tab: 'journey',
  data: null,
  romData: null,
  running: null,
  dexFilter: 'all',
  dexMissing: false,
  panes: [{ src: 'bank', box: 0 }, { src: null, box: 0 }],
  selected: null, // { pane, slot }
};

// ---------- helpers ----------

function toast(message, kind = 'info') {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.className = `toast show ${kind}`;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.className = 'toast'; }, 4200);
}

const speciesName = s => titleCase(state.romData?.speciesNames[s] ?? `#${s}`);
const moveName = m => titleCase(state.romData?.moveNames[m] ?? `Move ${m}`);
const itemName = i => titleCase(state.romData?.itemNames[i] ?? `Item ${i}`);

function monLevel(mon) {
  return state.romData ? levelFromExp(state.romData, mon.species, mon.experience) : '?';
}

function sprite(species, { shiny = false, cls = '' } = {}) {
  const url = state.romData ? spriteUrl(state.romData.sprites, species, { shiny, hd: state.data.settings.hdSprites }) : null;
  return url ? `<img class="sprite ${cls}" src="${url}" alt="" loading="lazy">` : `<span class="sprite placeholder ${cls}">?</span>`;
}

function gameBadge(id) {
  const g = GAME_BY_ID[id];
  return `<span class="chip" style="--c:${g.color}">${g.title}</span>`;
}

async function refresh() {
  state.data = await lib.loadState();
  state.running = await lib.runningGame();
  state.romData = await lib.loadRomData(state.data.roms).catch(err => { console.error(err); return null; });
  if (!state.panes[1].src || (state.panes[1].src !== 'bank' && !state.data.saves[state.panes[1].src])) {
    state.panes[1].src = GAME_ORDER.find(id => state.data.saves[id]) ?? 'bank';
  }
  if (state.panes[0].src !== 'bank' && !state.data.saves[state.panes[0].src]) state.panes[0].src = 'bank';
  render();
}

function summary() {
  return summarize(state.data.saves);
}

// ---------- header ----------

function renderStrip(sum) {
  const strip = document.getElementById('trainer-strip');
  const entries = Object.entries(sum.perGame);
  if (!entries.length) { strip.innerHTML = ''; return; }
  const [, main] = entries.sort((a, b) => totalSeconds(b[1].trainer) - totalSeconds(a[1].trainer))[0];
  strip.innerHTML = `
    <div class="stat"><span class="label">Trainer</span><strong>${h(main.trainer.name || '—')}</strong></div>
    <div class="stat"><span class="label">Badges</span><strong>${sum.badgeCount}/16</strong></div>
    <div class="stat"><span class="label">Pokédex</span><strong>${sum.ownedCount}/386</strong></div>
    <div class="stat"><span class="label">Time</span><strong>${formatPlayTime(sum.playSeconds)}</strong></div>`;
}

const totalSeconds = t => t.playTime.hours * 3600 + t.playTime.minutes * 60 + t.playTime.seconds;

function render() {
  document.querySelectorAll('.tabs button').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === state.tab)));
  const sum = summary();
  renderStrip(sum);
  const banner = document.getElementById('banner');
  banner.hidden = !state.running;
  if (state.running) banner.textContent = `Pokémon ${GAME_BY_ID[state.running].title} is running in another tab. Close it before moving Pokémon in or out of that game.`;
  const renderers = { journey: renderJourney, cartridges: renderCartridges, dex: renderDex, bank: renderBank, settings: renderSettings };
  view.innerHTML = renderers[state.tab](sum);
  bind();
}

// ---------- journey ----------

function onboarding() {
  return `
    <section class="hero">
      <h2>Start your journey</h2>
      <p>Add your own cartridge dumps (<code>.gba</code> or <code>.zip</code>) for Ruby, Sapphire, Emerald, FireRed and LeafGreen.
      They stay in this browser and are never uploaded anywhere.</p>
      ${dropZone()}
      <ol class="steps">
        <li><strong>Kanto</strong> — begin in FireRed or LeafGreen and become Champion.</li>
        <li><strong>Hoenn</strong> — send your team south through the Pokémon Bank and take on Emerald.</li>
        <li><strong>Master</strong> — use every version to complete one combined 386 Pokédex.</li>
      </ol>
    </section>`;
}

function dropZone() {
  return `
    <label class="drop" data-drop>
      <input type="file" accept=".gba,.zip" multiple data-rom-input hidden>
      <span class="drop-icon" aria-hidden="true">＋</span>
      <span><strong>Drop ROMs here</strong> or click to choose files</span>
    </label>`;
}

function renderJourney(sum) {
  if (!state.data.roms.size) return onboarding();
  const chapters = campaign(sum);
  const current = chapters.find(c => !c.done) ?? chapters.at(-1);
  return `
    <section class="journey">
      ${chapters.map(ch => chapterCard(ch, sum, ch === current)).join('')}
    </section>
    <section class="panel">
      <h3>Badge case</h3>
      <div class="badge-case">
        ${['Kanto', 'Hoenn'].map(region => `
          <div class="badge-row">
            <span class="region">${region}${sum.champion[region] ? ' <span class="crown" title="Champion">★</span>' : ''}</span>
            ${BADGES[region].map((name, i) => `<span class="badge ${sum.badges[region][i] ? 'got' : ''} ${region.toLowerCase()}" title="${name} Badge"><i></i>${name}</span>`).join('')}
          </div>`).join('')}
      </div>
    </section>`;
}

function chapterCard(ch, sum, isCurrent) {
  let progress;
  if (ch.goal.dexOwned) {
    progress = `<div class="bar"><span style="width:${(sum.ownedCount / 386) * 100}%"></span></div>
      <p class="muted">${sum.ownedCount} of 386 caught across all cartridges · ${sum.seenCount} seen</p>`;
  } else {
    const best = ch.games.map(id => sum.perGame[id]).filter(Boolean).sort((a, b) => b.badges - a.badges)[0];
    const badges = best?.badges ?? 0;
    progress = `<div class="bar"><span style="width:${(badges / 8) * 100 * (best?.champion ? 1 : 0.9)}%"></span></div>
      <p class="muted">${badges}/8 badges${best?.champion ? ' · Champion' : ''}</p>`;
  }
  const status = ch.done ? '<span class="pill done">Complete</span>'
    : ch.unlocked ? '<span class="pill now">In progress</span>'
    : '<span class="pill">Up next</span>';
  const buttons = ch.games.map(id => {
    const g = GAME_BY_ID[id];
    const has = state.data.roms.has(id);
    return has
      ? `<a class="btn play" style="--c:${g.color}" href="play.html?game=${id}">▶ ${g.title}</a>`
      : `<span class="btn disabled" title="Add the ${g.title} ROM on the Cartridges tab">${g.title}</span>`;
  }).join('');
  const tip = ch.id === 'hoenn' && sum.champion.Kanto && !ch.done
    ? '<p class="tip">Tip: open the <a href="#" data-goto="bank">Pokémon Bank</a> to bring your Kanto team along.</p>' : '';
  return `
    <article class="chapter ${isCurrent ? 'current' : ''} ${ch.done ? 'done' : ''}">
      <header><h3>${ch.title}</h3>${status}</header>
      <p>${ch.blurb}</p>
      ${progress}
      ${tip}
      <div class="row">${buttons}</div>
    </article>`;
}

// ---------- cartridges ----------

function renderCartridges() {
  return `
    ${dropZone()}
    <section class="carts">
      ${GAME_ORDER.map(id => cartCard(GAME_BY_ID[id])).join('')}
    </section>`;
}

function cartCard(game) {
  const hasRom = state.data.roms.has(game.id);
  const save = state.data.saves[game.id];
  const err = state.data.saveErrors[game.id];
  let info = '<p class="muted">No save yet — start a new adventure.</p>';
  if (save) {
    const t = save.trainer;
    info = `<dl class="facts">
      <dt>Trainer</dt><dd>${h(t.name)} <span class="muted">ID ${String(t.tid).padStart(5, '0')}</span></dd>
      <dt>Badges</dt><dd>${save.badges.filter(Boolean).length}/8${save.champion ? ' · Champion ★' : ''}</dd>
      <dt>Played</dt><dd>${t.playTime.hours}h ${t.playTime.minutes}m</dd>
      <dt>Party</dt><dd class="party">${save.party.map(p => { const m = decodeBoxMon(p.raw); return m ? sprite(m.isEgg ? 0 : m.species, { shiny: m.shiny, cls: 'mini' }) : ''; }).join('')}</dd>
    </dl>`;
  } else if (err) {
    info = `<p class="error">Save could not be read: ${h(err)}</p>`;
  }
  return `
    <article class="cart ${hasRom ? '' : 'missing'}" style="--c:${game.color}">
      <div class="cart-label"><span>${game.region}</span><strong>${game.title}</strong></div>
      ${hasRom ? info : '<p class="muted">ROM not added yet.</p>'}
      <div class="row">
        ${hasRom ? `<a class="btn play" style="--c:${game.color}" href="play.html?game=${game.id}">▶ Play</a>` : ''}
        ${hasRom ? `<label class="btn ghost">Import save<input type="file" accept=".sav,.srm,.fla,.zip" data-import-save="${game.id}" hidden></label>` : ''}
        ${save ? `<button class="btn ghost" data-export-save="${game.id}">Export save</button>` : ''}
      </div>
    </article>`;
}

// ---------- Pokédex ----------

function nationalToSpecies() {
  const map = new Array(387).fill(0);
  state.romData?.nationalDex.forEach((n, s) => { if (n >= 1 && n <= 386 && !map[n]) map[n] = s; });
  return map;
}

function renderDex(sum) {
  if (!state.romData) return '<p class="empty">Add at least one ROM to see the Pokédex.</p>';
  const toSpecies = nationalToSpecies();
  const ranges = { all: [1, 386], kanto: [1, 151], johto: [152, 251], hoenn: [252, 386] };
  const [lo, hi] = ranges[state.dexFilter];
  const owners = n => Object.entries(state.data.saves).filter(([, s]) => hasDex(s.dexFlags('owned'), n)).map(([id]) => id);
  const cells = [];
  for (let n = lo; n <= hi; n++) {
    const owned = hasDex(sum.owned, n);
    if (state.dexMissing && owned) continue;
    const seen = hasDex(sum.seen, n);
    const s = toSpecies[n];
    const label = owned || seen ? speciesName(s) : '???';
    const where = owned ? owners(n).map(id => GAME_BY_ID[id].title).join(', ') : '';
    cells.push(`
      <div class="dex-cell ${owned ? 'owned' : seen ? 'seen' : 'unseen'}" title="${h(label)}${where ? ' — caught in ' + where : ''}">
        <span class="num">${String(n).padStart(3, '0')}</span>
        ${owned || seen ? sprite(s) : '<span class="sprite placeholder">?</span>'}
        <span class="name">${h(label)}</span>
      </div>`);
  }
  return `
    <section class="panel dex-head">
      <div><strong>${sum.ownedCount}</strong> caught · <strong>${sum.seenCount}</strong> seen · combined from every cartridge</div>
      <div class="row">
        ${Object.keys(ranges).map(k => `<button class="btn ghost ${state.dexFilter === k ? 'active' : ''}" data-dex-filter="${k}">${titleCase(k)}</button>`).join('')}
        <label class="check"><input type="checkbox" data-dex-missing ${state.dexMissing ? 'checked' : ''}> Missing only</label>
      </div>
    </section>
    <section class="dex-grid">${cells.join('') || '<p class="empty">Nothing missing here — great work!</p>'}</section>`;
}

// ---------- Bank ----------

function paneSlots(pane) {
  if (pane.src === 'bank') {
    const records = state.data.bank.slice().sort((a, b) => a.id - b.id);
    const pages = Math.max(1, Math.ceil((records.length + 1) / BOX_CAPACITY));
    pane.box = Math.min(pane.box, pages - 1);
    const page = records.slice(pane.box * BOX_CAPACITY, (pane.box + 1) * BOX_CAPACITY);
    return {
      boxCount: pages,
      boxName: `Bank ${pane.box + 1}`,
      slots: Array.from({ length: BOX_CAPACITY }, (_, i) => page[i] ? { raw: page[i].raw, mon: decodeBoxMon(page[i].raw), bankId: page[i].id, from: page[i].from } : null),
    };
  }
  const save = state.data.saves[pane.src];
  const boxes = listBoxes(save);
  return { boxCount: BOX_COUNT, boxName: boxes[pane.box].name, slots: boxes[pane.box].slots };
}

function renderPane(index) {
  const pane = state.panes[index];
  const other = state.panes[1 - index];
  const options = [['bank', 'Pokémon Bank'], ...GAME_ORDER.filter(id => state.data.saves[id]).map(id => [id, GAME_BY_ID[id].title])];
  const { boxCount, boxName, slots } = paneSlots(pane);
  const color = pane.src === 'bank' ? '#7c5cff' : GAME_BY_ID[pane.src].color;
  const sel = state.selected;
  return `
    <section class="pane" style="--c:${color}">
      <header>
        <select data-pane-src="${index}">
          ${options.map(([v, label]) => `<option value="${v}" ${v === pane.src ? 'selected' : ''} ${v !== 'bank' && v === other.src ? 'disabled' : ''}>${label}</option>`).join('')}
        </select>
        <div class="box-nav">
          <button class="btn ghost" data-box-step="${index}:-1" aria-label="Previous box">‹</button>
          <span>${h(boxName)} <span class="muted">${pane.box + 1}/${boxCount}</span></span>
          <button class="btn ghost" data-box-step="${index}:1" aria-label="Next box">›</button>
        </div>
      </header>
      <div class="box-grid">
        ${slots.map((s, i) => {
          const isSel = sel && sel.pane === index && sel.slot === i;
          if (!s) return `<button class="slot empty ${sel && sel.pane !== index ? 'target' : ''}" data-slot="${index}:${i}" aria-label="Empty slot"></button>`;
          const m = s.mon;
          return `<button class="slot ${isSel ? 'selected' : ''} ${m.isBadEgg ? 'bad' : ''}" data-slot="${index}:${i}" title="${h(m.isEgg ? 'Egg' : m.nickname)}">
            ${m.isBadEgg ? '<span class="sprite placeholder">!</span>' : m.isEgg ? '<span class="egg"></span>' : sprite(m.species, { shiny: m.shiny })}
            ${m.shiny ? '<span class="shiny">★</span>' : ''}
          </button>`;
        }).join('')}
      </div>
    </section>`;
}

function selectedEntry() {
  if (!state.selected) return null;
  return paneSlots(state.panes[state.selected.pane]).slots[state.selected.slot];
}

function renderDetail() {
  const entry = selectedEntry();
  if (!entry) {
    return `<aside class="detail empty-detail">
      <p><strong>Select a Pokémon</strong> to see its details.</p>
      <p class="muted">Then click an empty slot on the other side, or press “Move”, to transfer it. Every change keeps a backup of the save it touches.</p>
    </aside>`;
  }
  const m = entry.mon;
  if (m.isBadEgg) return '<aside class="detail"><p class="error">This slot holds corrupted data (a “Bad Egg”). It can’t be moved.</p></aside>';
  const other = state.panes[1 - state.selected.pane];
  const otherName = other.src === 'bank' ? 'the Bank' : GAME_BY_ID[other.src].title;
  const base = state.romData?.baseStats[m.species];
  const ability = base ? titleCase(state.romData.abilityNames[base.abilities[m.abilitySlot] || base.abilities[0]]) : '';
  const types = base ? [...new Set(base.types)].map(t => `<span class="type t${t}">${TYPES[t]}</span>`).join('') : '';
  return `
    <aside class="detail">
      <div class="detail-head">
        ${m.isEgg ? '<span class="egg big"></span>' : sprite(m.species, { shiny: m.shiny, cls: 'big' })}
        <div>
          <h3>${h(m.isEgg ? 'Egg' : m.nickname)} ${m.shiny ? '<span class="shiny">★</span>' : ''}</h3>
          ${m.isEgg ? '' : `<p>${speciesName(m.species)} · Lv ${monLevel(m)}</p><p>${types}</p>`}
        </div>
      </div>
      ${m.isEgg ? '' : `<dl class="facts">
        <dt>Nature</dt><dd>${m.nature}</dd>
        <dt>Ability</dt><dd>${ability}</dd>
        <dt>Item</dt><dd>${m.heldItem ? itemName(m.heldItem) : '—'}</dd>
        <dt>OT</dt><dd>${h(m.otName)} <span class="muted">${String(m.tid).padStart(5, '0')}</span></dd>
        <dt>Origin</dt><dd>${ORIGIN_GAMES[m.originGame] ?? 'Unknown'} · ${BALLS[m.ball] ?? ''} Ball · met Lv ${m.metLevel || 'egg'}</dd>
      </dl>
      <div class="moves">${m.moves.filter(Boolean).map(mv => `<span>${moveName(mv)}</span>`).join('')}</div>
      <table class="ivs"><tr>${STAT_NAMES.map(s => `<th>${s}</th>`).join('')}</tr>
        <tr>${m.ivs.map(v => `<td class="${v === 31 ? 'max' : ''}">${v}</td>`).join('')}</tr>
        <tr>${m.evs.map(v => `<td class="muted">${v}</td>`).join('')}</tr></table>
      <p class="muted small">IVs (top) · EVs (bottom)</p>`}
      <button class="btn play wide" data-move>Move to ${otherName} →</button>
    </aside>`;
}

function renderBank() {
  if (!Object.keys(state.data.saves).length) {
    return `<p class="empty">The Bank moves Pokémon between cartridges. Play a game and save in-game (or import a save on the Cartridges tab) to get started.</p>`;
  }
  return `
    <section class="bank">
      ${renderPane(0)}
      ${renderDetail()}
      ${renderPane(1)}
    </section>
    <p class="muted small center">The Bank can only change a game while it isn't running. Pokémon move between PC boxes; party Pokémon must be deposited in a PC in-game first.</p>`;
}

async function moveSelected(target = null) {
  const sel = state.selected;
  const entry = selectedEntry();
  if (!sel || !entry) return;
  const fromPane = state.panes[sel.pane];
  const toPane = state.panes[1 - sel.pane];
  if (fromPane.src === toPane.src) { toast('Pick two different places to move between.', 'error'); return; }
  const running = await lib.runningGame();
  if ([fromPane.src, toPane.src].includes(running)) { toast(`Close ${GAME_BY_ID[running].title} first.`, 'error'); return; }
  try {
    const saves = {};
    const loadSave = id => (saves[id] ??= new Gen3Save(state.data.saves[id].toBytes(), GAME_BY_ID[id].engine));
    let raw;
    if (fromPane.src === 'bank') raw = entry.raw;
    else raw = withdraw(loadSave(fromPane.src), fromPane.box, sel.slot);

    let notes = [];
    if (toPane.src !== 'bank') {
      const save = loadSave(toPane.src);
      const spot = target ?? (firstEmptySlotInBox(save, toPane.box) ?? firstEmptySlot(save, toPane.box));
      notes = deposit(save, raw, spot).notes;
    }
    for (const id of Object.keys(saves)) await lib.backupSave(id, `Bank transfer of ${entry.mon.nickname}`);
    await db.transaction(['saves', 'bank'], stores => {
      for (const [id, save] of Object.entries(saves)) stores.saves.put({ bytes: save.toBytes(), updated: Date.now() }, id);
      if (fromPane.src === 'bank') stores.bank.delete(entry.bankId);
      if (toPane.src === 'bank') stores.bank.add({ raw: Uint8Array.from(raw), from: fromPane.src, added: Date.now() });
    });
    state.selected = null;
    toast(`${entry.mon.isEgg ? 'Egg' : entry.mon.nickname} moved to ${toPane.src === 'bank' ? 'the Bank' : GAME_BY_ID[toPane.src].title}.${notes.length ? ' ' + notes.join(' ') : ''}`, 'ok');
    await refresh();
  } catch (err) {
    toast(err.message, 'error');
  }
}

function firstEmptySlotInBox(save, box) {
  for (let slot = 0; slot < BOX_CAPACITY; slot++) {
    if (!decodeBoxMon(save.getBoxMon(box, slot))) return { box, slot };
  }
  return null;
}

// ---------- settings ----------

function renderSettings() {
  const s = state.data.settings;
  return `
    <section class="panel settings">
      <h3>Graphics</h3>
      <label>In-game filter
        <select data-setting="filter">
          ${Object.entries(FILTERS).map(([k, f]) => `<option value="${k}" ${s.filter === k ? 'selected' : ''}>${f.label}</option>`).join('')}
        </select>
      </label>
      <p class="muted small">HD Smooth upscales the 240×160 picture with the ScaleHQ shader; Retro CRT emulates a curved tube. You can also change shaders and speed (fast-forward, save states) from the emulator's own menu while playing.</p>
      <label class="check"><input type="checkbox" data-setting="hdSprites" ${s.hdSprites ? 'checked' : ''}> HD sprites in the hub (Scale2x ×2 upscaling)</label>
    </section>
    <section class="panel settings">
      <h3>Data</h3>
      <p class="muted">Your ROMs, saves and Bank live only in this browser's storage. Export saves from the Cartridges tab to keep copies elsewhere.</p>
      <div class="row">
        <button class="btn ghost" data-export-bank>Export Bank (${state.data.bank.length} Pokémon)</button>
        <button class="btn ghost" data-backups>Download latest backups</button>
        <button class="btn danger" data-wipe>Delete everything…</button>
      </div>
    </section>
    <section class="panel settings">
      <h3>About</h3>
      <p class="muted small">Emulation by EmulatorJS (mGBA core). Names and sprites are read from your own ROMs at runtime; this project contains no game data.</p>
    </section>`;
}

// ---------- events ----------

function bind() {
  view.querySelectorAll('[data-rom-input]').forEach(input => input.addEventListener('change', () => handleRoms(input.files)));
  view.querySelectorAll('[data-drop]').forEach(zone => {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('over'));
    zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('over'); handleRoms(e.dataTransfer.files); });
  });
  view.querySelectorAll('[data-goto]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); state.tab = a.dataset.goto; render(); }));
  view.querySelectorAll('[data-import-save]').forEach(input => input.addEventListener('change', async () => {
    const id = input.dataset.importSave;
    try {
      if (await lib.runningGame() === id) throw new Error('Close the game before importing a save.');
      const t = await lib.importSave(id, input.files[0]);
      toast(`Imported ${GAME_BY_ID[id].title} save for ${t.name}.`, 'ok');
      await refresh();
    } catch (err) { toast(err.message, 'error'); }
  }));
  view.querySelectorAll('[data-export-save]').forEach(btn => btn.addEventListener('click', async () => {
    const id = btn.dataset.exportSave;
    const rec = await db.get('saves', id);
    download(rec.bytes, `Pokemon ${GAME_BY_ID[id].title}.sav`);
  }));
  view.querySelectorAll('[data-dex-filter]').forEach(b => b.addEventListener('click', () => { state.dexFilter = b.dataset.dexFilter; render(); }));
  view.querySelector('[data-dex-missing]')?.addEventListener('change', e => { state.dexMissing = e.target.checked; render(); });
  view.querySelectorAll('[data-pane-src]').forEach(sel => sel.addEventListener('change', () => {
    const pane = state.panes[+sel.dataset.paneSrc];
    pane.src = sel.value; pane.box = 0; state.selected = null; render();
  }));
  view.querySelectorAll('[data-box-step]').forEach(b => b.addEventListener('click', () => {
    const [i, d] = b.dataset.boxStep.split(':').map(Number);
    const pane = state.panes[i];
    const count = paneSlots(pane).boxCount;
    pane.box = (pane.box + d + count) % count;
    if (state.selected?.pane === i) state.selected = null;
    render();
  }));
  view.querySelectorAll('[data-slot]').forEach(b => b.addEventListener('click', () => {
    const [pane, slot] = b.dataset.slot.split(':').map(Number);
    const filled = !b.classList.contains('empty');
    if (filled) { state.selected = state.selected?.pane === pane && state.selected.slot === slot ? null : { pane, slot }; render(); return; }
    if (state.selected && state.selected.pane !== pane) {
      const target = state.panes[pane].src === 'bank' ? null : { box: state.panes[pane].box, slot };
      moveSelected(target);
    }
  }));
  view.querySelector('[data-move]')?.addEventListener('click', () => moveSelected());
  view.querySelectorAll('[data-setting]').forEach(input => input.addEventListener('change', async () => {
    const settings = { ...state.data.settings, [input.dataset.setting]: input.type === 'checkbox' ? input.checked : input.value };
    await db.put('meta', settings, 'settings');
    await refresh();
    toast('Settings saved.', 'ok');
  }));
  view.querySelector('[data-export-bank]')?.addEventListener('click', () => {
    const rows = state.data.bank.map(r => ({ from: r.from, added: new Date(r.added).toISOString(), pk3: btoa(String.fromCharCode(...r.raw)) }));
    download(new TextEncoder().encode(JSON.stringify(rows, null, 2)), 'pokemon-bank.json');
  });
  view.querySelector('[data-backups]')?.addEventListener('click', async () => {
    const backups = (await db.all('backups')).sort((a, b) => b.at - a.at);
    if (!backups.length) { toast('No backups yet — they are made automatically before every change.'); return; }
    const seen = new Set();
    for (const b of backups) {
      if (seen.has(b.game)) continue;
      seen.add(b.game);
      download(b.bytes, `Pokemon ${GAME_BY_ID[b.game].title} backup ${new Date(b.at).toISOString().slice(0, 19).replace(/:/g, '-')}.sav`);
    }
  });
  view.querySelector('[data-wipe]')?.addEventListener('click', async () => {
    if (!confirm('Delete all ROMs, saves, backups and Bank Pokémon from this browser? Export anything you want to keep first.')) return;
    for (const store of ['roms', 'saves', 'bank', 'meta', 'backups']) for (const k of await db.keys(store)) await db.del(store, k);
    toast('Everything was deleted.');
    await refresh();
  });
}

async function handleRoms(files) {
  const results = await lib.importFiles(files);
  toast(results.map(r => r.message).join(' '), results.every(r => r.ok) ? 'ok' : 'error');
  await refresh();
}

document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => {
  state.tab = b.dataset.tab;
  state.selected = null;
  render();
}));

window.addEventListener('focus', refresh);
refresh().catch(err => { view.innerHTML = `<p class="error">${h(err.message)}</p>`; });
