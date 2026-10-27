// Merges every cartridge's progress into one trainer profile.
import { GAME_BY_ID, CHAPTERS } from './games.js';

export function summarize(saves) {
  // saves: { [gameId]: Gen3Save }
  const owned = new Uint8Array(52);
  const seen = new Uint8Array(52);
  const regions = { Kanto: new Array(8).fill(false), Hoenn: new Array(8).fill(false) };
  const champion = { Kanto: false, Hoenn: false };
  let seconds = 0;
  const perGame = {};
  for (const [id, save] of Object.entries(saves)) {
    const game = GAME_BY_ID[id];
    const o = save.dexFlags('owned');
    const s = save.dexFlags('seen');
    for (let i = 0; i < 52; i++) { owned[i] |= o[i]; seen[i] |= s[i]; }
    const badges = save.badges;
    badges.forEach((b, i) => { regions[game.region][i] ||= b; });
    champion[game.region] ||= save.champion;
    const t = save.trainer;
    seconds += t.playTime.hours * 3600 + t.playTime.minutes * 60 + t.playTime.seconds;
    perGame[id] = { trainer: t, badges: badges.filter(Boolean).length, champion: save.champion, owned: countBits(o) };
  }
  return {
    owned, seen,
    ownedCount: countBits(owned),
    seenCount: countBits(seen),
    badges: regions,
    badgeCount: regions.Kanto.filter(Boolean).length + regions.Hoenn.filter(Boolean).length,
    champion,
    playSeconds: seconds,
    perGame,
  };
}

export function hasDex(flags, national) {
  const i = national - 1;
  return !!(flags[i >> 3] & (1 << (i & 7)));
}

function countBits(flags) {
  let n = 0;
  for (let i = 0; i < 386; i++) if (flags[i >> 3] & (1 << (i & 7))) n++;
  return n;
}

function chapterComplete(chapter, summary) {
  const { goal } = chapter;
  if (goal.dexOwned) return summary.ownedCount >= goal.dexOwned;
  return chapter.games.some(id => {
    const g = summary.perGame[id];
    return g && g.badges >= goal.badges && (!goal.champion || g.champion);
  });
}

export function campaign(summary) {
  let unlocked = true;
  return CHAPTERS.map(ch => {
    const done = chapterComplete(ch, summary);
    const state = { ...ch, unlocked, done };
    unlocked = unlocked && done;
    return state;
  });
}
