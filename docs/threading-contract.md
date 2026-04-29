# Email Threading Contract

## Canonical owner

`backend/services/threading_service.py` owns persisted `thread_id` assignment. Parsers extract headers. Importers and API code must not recompute a competing thread ID.

## Header normalization

- Persisted `thread_id` strips surrounding angle brackets and whitespace.
- `Message-ID`, `In-Reply-To`, and `References` are retained on the email row for outbound replies and debugging.
- `Reply-To` is captured separately and used before the display `From` value when drafting replies.

## Assignment order

1. If `In-Reply-To` matches an imported parent, reuse that parent thread.
2. If any `References` ancestor matches an imported message, reuse that thread.
3. If no parent exists yet, use the oldest `References` value as the deterministic root.
4. If there are no references but `In-Reply-To` exists, use it as the deterministic parent root.
5. If there are no threading headers, use the message ID.
6. If the message ID is missing, generate a surrogate UUID.

## API behavior

- Inbox list returns one item per thread and exact `reply_count` across persisted rows available to the endpoint.
- Thread detail returns messages oldest to newest.
- Search returns message-level results with list-compatible `date`, `thread_id`, and `reply_count` fields.
- Send returns honest status. A simulated local send is not presented as real delivery.

## Current ownership boundary

Email rows are single-user development data today. Multi-user production safety requires an owner/mailbox key on `emails` and matching filters in email and search endpoints.
