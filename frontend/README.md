# AI Email Client Frontend

> 나루온 (Naruon) — AI 이메일 워크스페이스의 프론트엔드 앱.

Next.js app for the threaded inbox, email detail pane, AI summary, action items, reply composer, and network graph.

## Setup

```bash
npm install
npm test
npm run lint
npm run build
npm run dev
```

Open <http://localhost:3000>. The app expects the backend at `NEXT_PUBLIC_API_URL`, defaulting to <http://localhost:8000>.

## Threading UI contract

- Inbox rows show selected state and thread message counts.
- Search results use the same date/thread metadata shape as inbox results.
- Detail view clears stale conversation state when switching emails.
- Conversation history shows oldest-to-newest order and marks the selected message.
- Thread fetch failures are visible and retryable.
- Reply sends include `In-Reply-To` and `References` metadata.

## Local docs note

This project uses Next.js 16. The local guidance lives under `node_modules/next/dist/docs/` after `npm install`.
