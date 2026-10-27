# Gen III Unified

Ruby, Sapphire, Emerald, FireRed and LeafGreen played as **one connected game**, in the browser.

You add your own cartridge dumps. The hub then ties the five games together:

| | |
|---|---|
| **Journey** | A three-chapter campaign: become Kanto Champion (FireRed/LeafGreen), bring your team to Hoenn and conquer it (Emerald/Ruby/Sapphire), then complete the combined 386 Pokédex. Progress is read live from your saves. |
| **One trainer profile** | A single badge case (16 badges), total play time and Champion titles across every cartridge. |
| **Combined Pokédex** | Union of caught/seen flags from all five saves. Missing-only filter and per-region views. |
| **Pokémon Bank** | Move Pokémon between any two games' PC boxes, or park them in an unlimited Bank. Shows species, level, nature, ability, moves, IVs/EVs, OT and origin. |
| **Upgraded graphics** | In-game HD upscaling (4× / 2× ScaleHQ shaders) or a CRT filter. The hub's sprites use Scale2x×2 upscaling. |
| **Emulator extras** | Fast-forward, save states, rebindable controls and a touch gamepad on phones (EmulatorJS, mGBA core). |

## Running it

ES modules need a web server (opening `index.html` as a file won't work):

```sh
cd pokemon-unified
python3 -m http.server 8000     # or: npm start
```

Open <http://localhost:8000>, drop your `.gba` or `.zip` dumps onto the page, and press **Play**.
Supported: the English (USA/Europe) releases — game codes `AXVE`, `AXPE`, `BPEE`, `BPRE`, `BPGE`. Tested with
Ruby/Sapphire Rev 2, Emerald, and FireRed/LeafGreen Rev 1. Other English revisions should work too, because data
tables are located by signature.

The emulator loads from `cdn.emulatorjs.org` at a pinned version (`js/config.js`). To run fully
offline, download `https://cdn.emulatorjs.org/4.2.3/data/` into `vendor/emulatorjs/` and point
`EMULATORJS_DATA` there.

## How it works

- **No game data in this repository.** Species/move/item names, Pokédex numbers, growth rates and
  sprites are extracted at runtime from *your* ROMs (`js/romdata.js`). Tables are found by content
  signature, not hard-coded addresses.
- **Saves stay in your browser** (IndexedDB). While you play, the in-game battery save is copied back
  every few seconds and on exit. Import or export standard 128 KiB `.sav` files on the Cartridges tab,
  and keep using them in any other emulator or on real hardware through a flash cart.
- **Save editing follows the pret decompilations** (`pokeemerald`, `pokefirered`, `pokeruby`): two
  14-sector slots, per-sector checksums, the PC storage spread over sectors 5–13, and Pokémon data
  encrypted with `PID ^ OTID` and shuffled by `PID % 24`. The Bank only rewrites the PC-storage sectors
  of the newest slot. The older slot stays untouched as the game's own fallback.
- **Every change is backed up first.** The last ten versions of each save are kept (Settings →
  *Download latest backups*). Games that are running in another tab are locked against Bank edits.
- Held items that don't exist in Ruby/Sapphire are removed when a Pokémon is deposited there.

### Why not a single merged ROM?

Porting FireRed's Kanto into Emerald's engine means converting every map, tileset, script, trainer,
encounter table and song between two engines that differ in all of those formats. That's a
months-long ROM-hack project, and the result would be a modified copyrighted ROM that can't be shared.
This project connects the original, unmodified games instead, so every cartridge plays exactly as
designed.

## Tests

```sh
npm test
# optional: real-data checks against your own files
GEN3_ROM_DIR=/path/to/roms GEN3_FR_SAVE=fr.sav GEN3_EM_SAVE=em.sav npm test
```

The real-data checks were run against all five ROMs and against saves created by playing FireRed and
Emerald in the bundled emulator. A FireRed Bulbasaur was moved into Emerald's PC through the hub.
Emerald still boots the edited save, and FireRed reloads and re-saves its edited save normally.

## Layout

```
index.html / play.html   hub and emulator pages
js/app.js                hub UI (journey, cartridges, Pokédex, Bank, settings)
js/play.js               EmulatorJS wrapper + save sync
js/save.js               Gen III save reader/writer
js/pokemon.js            Pokémon decryption/encryption
js/bank.js               transfers between games
js/profile.js            merged progress + campaign
js/romdata.js            runtime extraction of names/sprites from ROMs
js/games.js              per-game offsets and campaign definition
```
