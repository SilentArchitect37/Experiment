// Turns the decoded 64×64 cartridge sprites into images, optionally upscaled with Scale2x
// (applied twice → 256×256) for crisp "HD" edges without blurring the pixel art.
const cache = new Map();

function scale2x(src, w, h) {
  const dst = new Uint32Array(w * 2 * h * 2);
  const at = (x, y) => src[Math.min(h - 1, Math.max(0, y)) * w + Math.min(w - 1, Math.max(0, x))];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const p = at(x, y), a = at(x, y - 1), b = at(x + 1, y), c = at(x - 1, y), d = at(x, y + 1);
      let e0 = p, e1 = p, e2 = p, e3 = p;
      if (a !== d && c !== b) {
        if (c === a) e0 = a;
        if (a === b) e1 = b;
        if (d === c) e2 = c;
        if (b === d) e3 = d;
      }
      const o = y * 2 * w * 2 + x * 2;
      dst[o] = e0; dst[o + 1] = e1; dst[o + w * 2] = e2; dst[o + w * 2 + 1] = e3;
    }
  }
  return dst;
}

export function spriteUrl(sprites, species, { shiny = false, hd = true } = {}) {
  const key = `${species}:${shiny}:${hd}`;
  if (cache.has(key)) return cache.get(key);
  const entry = sprites?.[species];
  if (!entry) return null;
  const rgba = shiny ? entry.shiny : entry.normal;
  let px = new Uint32Array(rgba.buffer.slice(0));
  let size = 64;
  if (hd) {
    px = scale2x(px, size, size); size *= 2;
    px = scale2x(px, size, size); size *= 2;
  }
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  ctx.putImageData(new ImageData(new Uint8ClampedArray(px.buffer), size, size), 0, 0);
  const url = canvas.toDataURL();
  cache.set(key, url);
  return url;
}
