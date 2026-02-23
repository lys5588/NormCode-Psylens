import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { RunInspector } from './RunInspector';
import './index.css';

const roots = new WeakMap<HTMLElement, Root>();

function mount(element: HTMLElement, runId: string) {
  unmount(element);
  const root = createRoot(element);
  root.render(
    <React.StrictMode>
      <RunInspector runId={runId} />
    </React.StrictMode>,
  );
  roots.set(element, root);
}

function unmount(element: HTMLElement) {
  const existing = roots.get(element);
  if (existing) {
    existing.unmount();
    roots.delete(element);
  }
}

try {
  (window as unknown as Record<string, unknown>).NormCodeInspector = { mount, unmount };
  console.log('[Dashboard] NormCodeInspector registered on window');
} catch (e) {
  console.error('[Dashboard] Failed to register on window:', e);
}

export { mount, unmount };
