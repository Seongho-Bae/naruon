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

Open <http://localhost:3000>. The app expects the backend at `NEXT_PUBLIC_API_URL`, defaulting to <http://localhost:8000>. For local browser development against protected backend routes, set `NEXT_PUBLIC_API_AUTH_TOKEN` to a signed local bearer token whose `sub` matches the fixture owner; do not use public frontend tokens as a production authentication boundary.

## Threading UI contract

- Inbox rows show selected state and thread message counts.
- Search results use the same date/thread metadata shape as inbox results.
- Detail view clears stale conversation state when switching emails.
- Conversation history shows oldest-to-newest order and marks the selected message.
- Thread fetch failures are visible and retryable.
- Reply sends include `In-Reply-To` and `References` metadata.

## Local docs note

This project uses Next.js 16. The local guidance lives under `node_modules/next/dist/docs/` after `npm install`.
