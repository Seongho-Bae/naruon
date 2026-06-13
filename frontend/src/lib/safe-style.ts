export function boundedPercent(value: unknown) {
  const numericValue = typeof value === 'number'
    ? value
    : typeof value === 'string' && value.trim() !== ''
      ? Number(value)
      : 0;
  if (!Number.isFinite(numericValue)) return 0;
  return Math.max(0, Math.min(100, numericValue));
}

export function boundedPercentStyle(value: unknown) {
  return { width: `${boundedPercent(value)}%` };
}

export function formatBoundedPercent(value: unknown) {
  return `${boundedPercent(value)}%`;
}
