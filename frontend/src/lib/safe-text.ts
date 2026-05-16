const UNSAFE_TEXT_CONTROL_CHARACTERS = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g;

/**
 * Converts untrusted API text into safe React text-node content.
 *
 * React escapes string children before inserting them into the DOM. This helper
 * keeps email display fields on that safe text-node path and strips control
 * characters that can make user-supplied mail content ambiguous in the UI.
 */
export function toSafeReactText(value: string | null | undefined, fallback = '') {
  return (value ?? fallback).replace(UNSAFE_TEXT_CONTROL_CHARACTERS, '\uFFFD');
}
