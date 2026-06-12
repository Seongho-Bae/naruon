## 2025-06-08 - [Debounce NetworkGraph ResizeObserver]
**Learning:** React components containing Vis-network canvases will rapidly and continuously refit on viewport changes via ResizeObserver. The synchronous `network.fit()` calls block the main thread and degrade user experience if not throttled/debounced.
**Action:** When utilizing `ResizeObserver` for redrawing or fitting complex components like graphs, always wrap the heavy operation inside a debounce `setTimeout` and ensure that tests utilize `vi.useFakeTimers()` to verify the execution.
