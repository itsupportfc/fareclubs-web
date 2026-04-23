/**
 * fetch() wrapper that aborts after `timeoutMs` milliseconds.
 */
export async function fetchWithTimeout(url, options, timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(
        () =>
            controller.abort(
                new DOMException("Request timed out", "TimeoutError"),
            ),
        timeoutMs,
    );
    try {
        return await fetch(url, { ...options, signal: controller.signal });
    } finally {
        clearTimeout(timer);
    }
}
