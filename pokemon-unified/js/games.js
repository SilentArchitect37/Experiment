// Static facts about the five supported cartridges and how they fit into one campaign.

export const ENGINE = { RS: 'rs', E: 'e', FRLG: 'frlg' };

export const GAMES = {
  AXVE: { id: 'ruby',     code: 'AXVE', title: 'Ruby',      region: 'Hoenn', engine: ENGINE.RS,   color: '#c8323c' },
  AXPE: { id: 'sapphire', code: 'AXPE', title: 'Sapphire',  region: 'Hoenn', engine: ENGINE.RS,   color: '#2f5fc4' },
  BPEE: { id: 'emerald',  code: 'BPEE', title: 'Emerald',   region: 'Hoenn', engine: ENGINE.E,    color: '#1f9d63' },
  BPRE: { id: 'firered',  code: 'BPRE', title: 'FireRed',   region: 'Kanto', engine: ENGINE.FRLG, color: '#e2582b' },
  BPGE: { id: 'leafgreen',code: 'BPGE', title: 'LeafGreen', region: 'Kanto', engine: ENGINE.FRLG, color: '#58a83a' },
};

export const GAME_BY_ID = Object.fromEntries(Object.values(GAMES).map(g => [g.id, g]));

// Offsets from the pret decompilations (include/global.h, include/constants/flags.h).
export const ENGINE_LAYOUT = {
  [ENGINE.RS]:   { flagsOffset: 0x1220, badge1Flag: 0x807, gameClearFlag: 0x804, partyCountOffset: 0x234, partyOffset: 0x238, lastItemId: 0x15C },
  [ENGINE.E]:    { flagsOffset: 0x1270, badge1Flag: 0x867, gameClearFlag: 0x864, partyCountOffset: 0x234, partyOffset: 0x238, lastItemId: 0x178 },
  [ENGINE.FRLG]: { flagsOffset: 0x0EE0, badge1Flag: 0x820, gameClearFlag: 0x82C, partyCountOffset: 0x034, partyOffset: 0x038, lastItemId: 0x176 },
};

export const BADGES = {
  Kanto: ['Boulder', 'Cascade', 'Thunder', 'Rainbow', 'Soul', 'Marsh', 'Volcano', 'Earth'],
  Hoenn: ['Stone', 'Knuckle', 'Dynamo', 'Heat', 'Balance', 'Feather', 'Mind', 'Rain'],
};

// The campaign stitches the cartridges into one journey. A chapter unlocks when the
// previous chapter's goal is met in any of its listed games.
export const CHAPTERS = [
  {
    id: 'kanto', title: 'Chapter I — Kanto', games: ['firered', 'leafgreen'],
    blurb: 'Leave Pallet Town, earn the eight Kanto badges and become Champion at Indigo Plateau.',
    goal: { badges: 8, champion: true },
  },
  {
    id: 'hoenn', title: 'Chapter II — Hoenn', games: ['emerald', 'ruby', 'sapphire'],
    blurb: 'Bring your team south through the Pokémon Bank and conquer Hoenn, Team Magma, Team Aqua and the Elite Four.',
    goal: { badges: 8, champion: true },
  },
  {
    id: 'master', title: 'Chapter III — Pokémon Master', games: ['firered', 'leafgreen', 'emerald', 'ruby', 'sapphire'],
    blurb: 'Use every cartridge and the Bank to complete the combined National Pokédex.',
    goal: { dexOwned: 386 },
  },
];
