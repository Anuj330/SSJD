/** Circular progress ring (conic-gradient). `value` is 0–100. */
export default function Ring({ value = 0, size = 96, label = 'repaid' }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className="relative shrink-0 rounded-full"
      style={{
        width: size,
        height: size,
        background: `conic-gradient(var(--color-primary-600) ${pct}%, var(--color-gray-200, #E4E9F0) 0)`,
      }}
    >
      <div className="absolute inset-[9px] rounded-full bg-white dark:bg-gray-900" />
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="num text-xl font-bold text-gray-900 dark:text-gray-100">{Math.round(pct)}%</div>
          <div className="text-[10px] text-gray-400 dark:text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  );
}
