import { useEffect, useRef } from 'react';
import { useThemeStore } from '../../store/themeStore';

function useColors() {
  const { theme } = useThemeStore();
  const dark = theme === 'dark';
  return {
    theme,
    grid: dark ? '#1D2836' : '#E6EBF1',
    text: dark ? '#5D6B7C' : '#94A0AE',
    accent: dark ? '#23D29A' : '#0BA371',
    surface: dark ? '#0F1722' : '#FFFFFF',
  };
}

/** Smooth area+line chart. data: [{label, value}] */
export function AreaLine({ data = [], height = 200 }) {
  const ref = useRef(null);
  const c = useColors();
  useEffect(() => {
    const cv = ref.current; if (!cv || !data.length) return;
    const draw = () => {
      const ctx = cv.getContext('2d');
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      const W = cv.clientWidth || 480, H = height;
      cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      const padL = 34, padR = 10, padT = 12, padB = 22;
      const pw = W - padL - padR, ph = H - padT - padB;
      const vals = data.map(d => d.value);
      const max = Math.max(...vals, 1), min = Math.min(...vals, 0);
      const X = i => padL + (pw * i) / Math.max(1, data.length - 1);
      const Y = v => padT + ph * (1 - (v - min) / Math.max(1, max - min));
      ctx.font = '10px "Space Grotesk", monospace'; ctx.fillStyle = c.text;
      ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
      for (let g = 0; g <= 3; g++) {
        const v = min + (max - min) * (g / 3), y = Y(v);
        ctx.strokeStyle = c.grid; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
        ctx.fillText(Math.round(v), padL - 6, y);
      }
      ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      data.forEach((d, i) => { if (i % Math.ceil(data.length / 6 || 1) === 0) ctx.fillText(d.label, X(i), H - padB + 6); });
      const path = () => {
        ctx.beginPath();
        data.forEach((d, i) => {
          const x = X(i), y = Y(d.value);
          if (i === 0) ctx.moveTo(x, y);
          else { const px = X(i - 1), py = Y(data[i - 1].value), cx = (px + x) / 2; ctx.bezierCurveTo(cx, py, cx, y, x, y); }
        });
      };
      const grad = ctx.createLinearGradient(0, padT, 0, padT + ph);
      grad.addColorStop(0, 'rgba(11,163,113,.26)'); grad.addColorStop(1, 'rgba(11,163,113,0)');
      path(); ctx.lineTo(X(data.length - 1), Y(min)); ctx.lineTo(X(0), Y(min)); ctx.closePath(); ctx.fillStyle = grad; ctx.fill();
      path(); ctx.strokeStyle = c.accent; ctx.lineWidth = 2.4; ctx.lineJoin = 'round'; ctx.stroke();
      const lx = X(data.length - 1), ly = Y(data[data.length - 1].value);
      ctx.beginPath(); ctx.arc(lx, ly, 4, 0, 7); ctx.fillStyle = c.accent; ctx.fill();
      ctx.beginPath(); ctx.arc(lx, ly, 4, 0, 7); ctx.strokeStyle = c.surface; ctx.lineWidth = 2; ctx.stroke();
    };
    draw();
    const onR = () => draw(); window.addEventListener('resize', onR);
    return () => window.removeEventListener('resize', onR);
  }, [data, height, c.theme]); // eslint-disable-line
  return <canvas ref={ref} style={{ display: 'block', width: '100%' }} height={height} />;
}

/** Donut chart. data: [{label, value, color}]. Shows a centered total. */
export function Donut({ data = [], size = 150, centerLabel = '' }) {
  const ref = useRef(null);
  const c = useColors();
  useEffect(() => {
    const cv = ref.current; if (!cv) return;
    const total = data.reduce((s, d) => s + (d.value || 0), 0);
    const draw = () => {
      const ctx = cv.getContext('2d');
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      cv.width = size * dpr; cv.height = size * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, size, size);
      const cx = size / 2, cy = size / 2, r = size / 2 - 6, inner = r * 0.62;
      if (total <= 0) {
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.strokeStyle = c.grid; ctx.lineWidth = r - inner; ctx.stroke();
      } else {
        let a = -Math.PI / 2;
        data.forEach((d) => {
          if (!d.value) return;
          const slice = (d.value / total) * Math.PI * 2;
          ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r, a, a + slice); ctx.closePath();
          ctx.fillStyle = d.color; ctx.fill();
          a += slice;
        });
        ctx.beginPath(); ctx.arc(cx, cy, inner, 0, Math.PI * 2); ctx.fillStyle = c.surface; ctx.fill();
      }
      ctx.fillStyle = c.text; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.font = '700 14px "Space Grotesk", sans-serif';
      ctx.fillText(centerLabel, cx, cy);
    };
    draw();
  }, [data, size, centerLabel, c.theme]); // eslint-disable-line
  return <canvas ref={ref} style={{ width: size, height: size }} />;
}

/** Vertical bars. data: [{label, value}] */
export function Bars({ data = [], height = 200 }) {
  const ref = useRef(null);
  const c = useColors();
  useEffect(() => {
    const cv = ref.current; if (!cv || !data.length) return;
    const draw = () => {
      const ctx = cv.getContext('2d');
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      const W = cv.clientWidth || 480, H = height;
      cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      const padL = 34, padR = 10, padT = 12, padB = 22;
      const pw = W - padL - padR, ph = H - padT - padB;
      const max = Math.max(...data.map(d => d.value), 1);
      ctx.font = '10px "Space Grotesk", monospace'; ctx.fillStyle = c.text;
      ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
      for (let g = 0; g <= 3; g++) {
        const v = (max / 3) * g, y = padT + ph * (1 - g / 3);
        ctx.strokeStyle = c.grid; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
        ctx.fillText(Math.round(v), padL - 6, y);
      }
      const bw = pw / data.length;
      ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      data.forEach((d, i) => {
        const x = padL + bw * i + bw * 0.2, w = bw * 0.6;
        const h = ph * (d.value / max), y = padT + ph - h;
        ctx.fillStyle = c.accent; ctx.beginPath();
        const r = Math.min(4, w / 2); ctx.roundRect(x, y, w, h, [r, r, 0, 0]); ctx.fill();
        if (i % Math.ceil(data.length / 6 || 1) === 0) { ctx.fillStyle = c.text; ctx.fillText(d.label, x + w / 2, H - padB + 6); }
      });
    };
    draw();
    const onR = () => draw(); window.addEventListener('resize', onR);
    return () => window.removeEventListener('resize', onR);
  }, [data, height, c.theme]); // eslint-disable-line
  return <canvas ref={ref} style={{ display: 'block', width: '100%' }} height={height} />;
}
