// Generates the PWA icons with zero dependencies (node built-ins only).
// Design: calm dark field, a single breath-ring, one gold point at the nostril position.
// Usage: node tools/make-icons.mjs
import { deflateSync } from "node:zlib";
import { writeFileSync } from "node:fs";

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(buf) {
  let c = 0xffffffff;
  for (const b of buf) c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([len, body, crc]);
}
function png(width, height, rgba) {
  const raw = Buffer.alloc((width * 4 + 1) * height);
  for (let y = 0; y < height; y++) {
    raw[y * (width * 4 + 1)] = 0; // filter: none
    rgba.copy(raw, y * (width * 4 + 1) + 1, y * width * 4, (y + 1) * width * 4);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 6; // 8-bit RGBA
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 9 })),
    chunk("IEND", Buffer.alloc(0))
  ]);
}

// identity palette (matches the :root tokens in sit-tracker-v2.html)
const BG = [0x0a, 0x0e, 0x15], RING = [0x8e, 0xc3, 0xea], DOT = [0xd4, 0xb0, 0x78], GLOW = [0x55, 0x67, 0x9e];
function drawIcon(size, padded) {
  const buf = Buffer.alloc(size * size * 4);
  const cx = size / 2, cy = size / 2;
  const scale = padded ? 0.72 : 1; // maskable safe zone
  const rMid = size * 0.30 * scale, rW = size * 0.045 * scale;
  const dotR = size * 0.075 * scale, dotY = cy - rMid; // point on top of the ring
  const glowR = size * 0.46 * scale;
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4;
      let [r, g, b] = BG;
      const d = Math.hypot(x - cx, y - cy);
      // soft orb glow behind the ring (the app's hero motif)
      const gA = Math.exp(-(d * d) / (glowR * glowR)) * 0.22;
      r = r + (GLOW[0] - r) * gA;
      g = g + (GLOW[1] - g) * gA;
      b = b + (GLOW[2] - b) * gA;
      const ringDist = Math.abs(d - rMid);
      const aaRing = Math.max(0, Math.min(1, rW - ringDist + 0.5));
      if (aaRing > 0) {
        r = r + (RING[0] - r) * aaRing;
        g = g + (RING[1] - g) * aaRing;
        b = b + (RING[2] - b) * aaRing;
      }
      const dd = Math.hypot(x - cx, y - dotY);
      const aaDot = Math.max(0, Math.min(1, dotR - dd + 0.5));
      if (aaDot > 0) {
        r = r + (DOT[0] - r) * aaDot;
        g = g + (DOT[1] - g) * aaDot;
        b = b + (DOT[2] - b) * aaDot;
      }
      buf[i] = r; buf[i + 1] = g; buf[i + 2] = b; buf[i + 3] = 255;
    }
  }
  return png(size, size, buf);
}

writeFileSync("icons/icon-192.png", drawIcon(192, false));
writeFileSync("icons/icon-512.png", drawIcon(512, false));
writeFileSync("icons/icon-maskable-512.png", drawIcon(512, true));
writeFileSync("icons/apple-touch-icon.png", drawIcon(180, false));
console.log("icons written: 192, 512, maskable-512, apple-touch-180");
