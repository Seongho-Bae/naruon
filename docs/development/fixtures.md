# Fixture Import Workflow

The blessed local fixture path is `backend/import_fixtures.py`. It imports `.eml` files from `backend/tests/fixtures` and persists the canonical `thread_id` returned by `assign_thread_id`.

## Local command

```bash
cd backend
python3 import_fixtures.py
```

Inside Docker Compose:

```bash
docker compose exec backend python import_fixtures.py
```

## Included threading fixture

The `threading-basic-*` fixtures model one three-message conversation:

1. `threading-basic-01-root.eml`, root message with `Reply-To`.
2. `threading-basic-02-reply.eml`, reply with `In-Reply-To` and `References`.
3. `threading-basic-03-reply.eml`, second reply with full reference chain.

Use this fixture to verify inbox grouping, thread detail ordering, reply metadata, and search contract shape.

## Embeddings and offline mode

When `OPENAI_API_KEY` is set, the importer stores real embeddings. When it is blank, the root fixture importer stores zero-vector embeddings so local threading can be proven without external network access. Semantic search still requires a configured tenant OpenAI key because query-time embeddings are generated at request time.
