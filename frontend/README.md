# AI Email Client Frontend

Next.js app for the threaded inbox, email detail pane, AI summary, action items, reply composer, and network graph.

## Setup

```bash
npm install
npm test
npm run lint
npm run build
npm run dev
```

Open <http://localhost:3000>. Browser requests use the same-origin `/api/backend/...` proxy. Set server-side `API_INTERNAL_URL` when the frontend server should reach a backend other than <http://localhost:8000>. For local demos only, set `API_PROXY_ALLOW_SHARED_TOKEN=true` and `API_AUTH_TOKEN` to a signed local token; production should use per-user authentication rather than the shared-token proxy.

## Threading UI contract

- Inbox rows show selected state and thread message counts.
- Search results use the same date/thread metadata shape as inbox results.
- Detail view clears stale conversation state when switching emails.
- Conversation history shows oldest-to-newest order and marks the selected message.
- Thread fetch failures are visible and retryable.
- Reply sends include `In-Reply-To` and `References` metadata.

## Local docs note

This project uses Next.js 16. The local guidance lives under `node_modules/next/dist/docs/` after `npm install`.
