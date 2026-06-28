import { useEffect, useRef } from 'react';
import { useThemeStore } from '../../store/themeStore';

const MONTHS = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'];

/**
 * Collected vs disbursed area/line chart, drawn on canvas. Values in ₹ lakhs.
 * Re-renders on theme change and on container resize.
 */
export default function CollectionsChart({
  months = MONTHS,
  collected = [38, 44, 41, 52, 49, 58, 63, 60, 71, 68, 76, 82],
  disbursed = [22, 31, 28, 36, 33, 30, 42, 39, 47, 44, 51, 49],
  height = 260,
}) {
  const canvasRef = useRef(null);
  const { theme } = useThemeStore();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const draw = () => {
      const dark = theme === 'dark';
      const ctx = canvas.getContext('2d');
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      const W = canvas.clientWidth || 600;
      const H = height;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);

      const padL = 38, padR = 12, padT = 14, padB = 26;
      const plotW = W - padL - padR, plotH = H - padT - padB;
      const maxV = Math.max(90, ...collected, ...disbursed);
      const muted = dark ? '#7C8DA8' : '#6B7B96';
      const grid = dark ? '#1C2D49' : '#E4E9F0';
      const accent = dark ? '#1EB67E' : '#0E9F6E';
      const blue = '#3B6FD4';
      const surface = dark ? '#0E1D33' : '#FFFFFF';

      const X = (i) => padL + (plotW * i) / (months.length - 1);
      const Y = (v) => padT + plotH * (1 - v / maxV);

      ctx.font = '11px ui-monospace, monospace';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      for (let g = 0; g <= 3; g++) {
        const val = (maxV / 3) * g;
        const y = Y(val);
        ctx.strokeStyle = grid;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();
        ctx.fillStyle = muted;
        ctx.fillText(Math.round(val), padL - 8, y);
      }
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      months.forEach((m, i) => {
        ctx.fillStyle = muted;
        ctx.fillText(m, X(i), H - padB + 7);
      });

      const path = (data) => {
        ctx.beginPath();
        data.forEach((v, i) => {
          const x = X(i), y = Y(v);
          if (i === 0) ctx.moveTo(x, y);
          else {
            const px = X(i - 1), py = Y(data[i - 1]);
            const cx = (px + x) / 2;
            ctx.bezierCurveTo(cx, py, cx, y, x, y);
          }
        });
      };

      // collected area + line
      const grad = ctx.createLinearGradient(0, padT, 0, padT + plotH);
      grad.addColorStop(0, 'rgba(14,159,110,.34)');
      grad.addColorStop(1, 'rgba(14,159,110,0)');
      path(collected);
      ctx.lineTo(X(collected.length - 1), Y(0));
      ctx.lineTo(X(0), Y(0));
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();
      path(collected);
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2.6;
      ctx.lineJoin = 'round';
      ctx.stroke();

      // disbursed dashed line
      ctx.save();
      ctx.setLineDash([5, 5]);
      path(disbursed);
      ctx.strokeStyle = blue;
      ctx.lineWidth = 2.2;
      ctx.stroke();
      ctx.restore();

      const dot = (data, color) => {
        const x = X(data.length - 1), y = Y(data[data.length - 1]);
        ctx.beginPath();
        ctx.arc(x, y, 4.5, 0, 7);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(x, y, 4.5, 0, 7);
        ctx.strokeStyle = surface;
        ctx.lineWidth = 2;
        ctx.stroke();
      };
      dot(collected, accent);
      dot(disbursed, blue);
    };

    draw();
    let rt;
    const onResize = () => {
      clearTimeout(rt);
      rt = setTimeout(draw, 120);
    };
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      clearTimeout(rt);
    };
  }, [theme, months, collected, disbursed, height]);

  return <canvas ref={canvasRef} style={{ display: 'block', width: '100%' }} height={height} />;
}
