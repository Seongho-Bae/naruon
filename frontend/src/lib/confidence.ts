export function toConfidencePercent(confidence: number | undefined): number | undefined {
  if (typeof confidence !== "number" || !Number.isFinite(confidence)) {
    return undefined;
  }

  const percent = confidence >= 0 && confidence <= 1 ? confidence * 100 : confidence;
  return Math.round(Math.min(100, Math.max(0, percent)));
}
