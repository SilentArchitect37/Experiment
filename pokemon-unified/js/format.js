export function titleCase(s) {
  if (!s) return '';
  return s.toLowerCase().replace(/(^|[\s\-.(])([a-zé])/g, (_, p, c) => p + c.toUpperCase());
}

export function formatPlayTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}:${String(m).padStart(2, '0')}`;
}

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function download(bytes, filename) {
  const url = URL.createObjectURL(new Blob([bytes]));
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const BALLS = ['', 'Master', 'Ultra', 'Great', 'Poké', 'Safari', 'Net', 'Dive', 'Nest', 'Repeat', 'Timer', 'Luxury', 'Premier'];
export const STAT_NAMES = ['HP', 'Atk', 'Def', 'Spe', 'SpA', 'SpD'];
export const TYPES = ['Normal', 'Fighting', 'Flying', 'Poison', 'Ground', 'Rock', 'Bug', 'Ghost', 'Steel', '???', 'Fire', 'Water', 'Grass', 'Electric', 'Psychic', 'Ice', 'Dragon', 'Dark'];
