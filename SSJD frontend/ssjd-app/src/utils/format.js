// Indian-locale money + number formatting helpers.

const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

/** Full INR currency, e.g. ₹1,84,500 */
export function fmtINR(n) {
  const v = Number(n);
  return Number.isFinite(v) ? inr.format(v) : '₹0';
}

/** Compact INR in lakhs / crores, e.g. ₹8.24 Cr, ₹4.62 L, ₹12,400 */
export function fmtCompact(n) {
  const v = Number(n) || 0;
  const abs = Math.abs(v);
  const sign = v < 0 ? '-' : '';
  if (abs >= 1e7) return `${sign}₹${(abs / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `${sign}₹${(abs / 1e5).toFixed(2)} L`;
  return inr.format(v);
}

/** Plain grouped number, e.g. 1,248 */
export function fmtNum(n) {
  return new Intl.NumberFormat('en-IN').format(Number(n) || 0);
}

/** First letters of a name for avatars, e.g. "Ramesh Kumar" -> "RK" */
export function initials(name = '') {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || '')
    .join('') || '?';
}

/** Deterministic avatar color from a string. */
const AVATAR_COLORS = ['#3B6FD4', '#0E9F6E', '#7C5CE0', '#C9821B', '#0EA5A5', '#D2557A'];
export function avatarColor(seed = '') {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[h % AVATAR_COLORS.length];
}
