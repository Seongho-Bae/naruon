import { apiClient } from './api-client';

export type ExecutionQueueStatus = 'queued' | 'done';

export interface ExecutionQueueItem {
  id: number;
  sourceMailboxAccountId: number | null;
  sourceEmailId: number | null;
  sourceThreadId: string | null;
  sourceMessageId: string | null;
  sourceSnippet: string | null;
  title: string;
  sender: string;
  status: ExecutionQueueStatus;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
}

interface ExecutionItemApiResponse {
  id: number;
  user_id: string;
  source_mailbox_account_id: number | null;
  source_email_id: number | null;
  source_thread_id: string | null;
  source_message_id: string | null;
  source_snippet: string | null;
  title: string;
  sender: string;
  status: ExecutionQueueStatus;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

const STORAGE_KEY_PREFIX = 'naruon.executionQueue';
const EVENT_NAME = 'naruon.execution-queue.updated';
let volatileQueue: ExecutionQueueItem[] = [];

function getStorageKey() {
  if (apiClient.getBearerToken()) {
    return null;
  }
  const currentUserId = apiClient.getCurrentUserId() || 'anonymous';
  const currentOrganizationId = apiClient.getCurrentOrganizationId() || 'no-org';
  return `${STORAGE_KEY_PREFIX}.${currentOrganizationId}.${currentUserId}`;
}

function emitQueueUpdated() {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(EVENT_NAME));
}

function persistQueue(items: ExecutionQueueItem[]) {
  if (typeof window === 'undefined') return;
  const storageKey = getStorageKey();
  if (!storageKey) {
    volatileQueue = items;
    emitQueueUpdated();
    return;
  }
  window.localStorage.setItem(storageKey, JSON.stringify(items));
  emitQueueUpdated();
}

function normalizeExecutionItem(item: ExecutionItemApiResponse): ExecutionQueueItem {
  return {
    id: item.id,
    sourceMailboxAccountId: item.source_mailbox_account_id,
    sourceEmailId: item.source_email_id,
    sourceThreadId: item.source_thread_id,
    sourceMessageId: item.source_message_id,
    sourceSnippet: item.source_snippet,
    title: item.title,
    sender: item.sender,
    status: item.status,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
    completedAt: item.completed_at,
  };
}

export function listExecutionQueue(): ExecutionQueueItem[] {
  if (typeof window === 'undefined') return [];
  const storageKey = getStorageKey();
  if (!storageKey) return volatileQueue;
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as ExecutionQueueItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function refreshExecutionQueue(): Promise<ExecutionQueueItem[]> {
  try {
    const data = await apiClient.get<{ items: ExecutionItemApiResponse[] }>('/api/execution-items');
    const items = data.items.map(normalizeExecutionItem);
    persistQueue(items);
    return items;
  } catch {
    return listExecutionQueue();
  }
}

export async function queueEmailExecutionItem(email: { id: number; subject: string | null; sender: string }) {
  const data = await apiClient.post<{ item: ExecutionItemApiResponse }>('/api/execution-items/from-email', { email_id: email.id });
  const nextItem = normalizeExecutionItem(data.item);
  const queue = listExecutionQueue();
  const updated = [nextItem, ...queue.filter((item) => item.id !== nextItem.id)];
  persistQueue(updated);
  return nextItem;
}

export async function markExecutionQueueItemDone(emailId: number) {
  let queue = listExecutionQueue();
  let target = queue.find((item) => item.sourceEmailId === emailId || item.id === emailId) || null;
  if (!target) {
    queue = await refreshExecutionQueue();
    target = queue.find((item) => item.sourceEmailId === emailId || item.id === emailId) || null;
  }
  if (!target) return null;

  const data = await apiClient.patch<{ item: ExecutionItemApiResponse }>(`/api/execution-items/${target.id}`, { status: 'done' });
  const updatedItem = normalizeExecutionItem(data.item);
  const updatedQueue = listExecutionQueue().map((item) => (
    item.id === updatedItem.id ? updatedItem : item
  ));
  persistQueue(updatedQueue);
  return updatedItem;
}

export function subscribeExecutionQueue(listener: () => void) {
  if (typeof window === 'undefined') return () => undefined;
  window.addEventListener(EVENT_NAME, listener);
  return () => window.removeEventListener(EVENT_NAME, listener);
}
