/**
 * Small date/time helpers.
 *
 * We intentionally keep formatting logic in one place to avoid drift across pages.
 */

/**
 * Format a unix timestamp in seconds using the user's locale.
 */
export function formatUnixSeconds(ts: number): string {
  try {
    return new Date(ts * 1000).toLocaleString()
  } catch {
    return String(ts)
  }
}
