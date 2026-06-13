# 2026-05-29 AI Hub Source-Backed Surface

## Verified gap

- `frontend/branding/naruon-ux-mockup-8.png` defines AI Hub as five
  operational surfaces: Prompt Studio, Workflow, AI Agent, Evaluation, and Run
  History.
- The current `AIHubLayout` rendered static prompt, workflow, provider, score,
  and log examples. It did not call a signed backend API and could not prove
  whether the UI was backed by real prompt/provider/audit evidence.
- `docs/plans/2026-05-29-security-durable-audit-surface.md` already added
  durable provider audit events, so AI Hub can now use those scoped events
  instead of fake execution logs.

## Implemented slice

- Add signed `GET /api/ai-hub/surface`.
- Build the surface from existing source-backed objects:
  - `PromptTemplate` rows owned by the signed user. Global `is_shared` prompts
    are intentionally excluded until prompt rows have durable tenant/workspace
    scope;
  - organization-scoped `LLMProvider` rows for admin roles only, exposing only
    non-secret metadata;
  - durable `SecurityAuditEvent` rows for provider governance events.
- Return opaque stable keys for prompt, workflow, agent, and event cards instead
  of exposing sequential database identifiers.
- Replace static AI Hub UI fixtures with API-wired tabs and empty/error/loading
  states.
- Preserve the HttpOnly cookie-backed proxy session and keep browser
  `Authorization` plus public identity headers out of frontend requests.

## Verification

- Backend tests cover signed-session AI Hub reads, source evidence rendering,
  secret redaction, opaque keys, member provider redaction, shared prompt leak
  prevention, public identity header rejection, and PostgreSQL smoke behavior
  when a local test database is available.
- Frontend tests cover bearer fetch headers and all five operational AI Hub tabs.
- Browser evidence must capture desktop, tablet/mobile scroll, and hamburger
  navigation after this route is included in the responsive E2E pass.

## Remaining roadmap

- Add a durable workflow registry before allowing workflow edits in AI Hub.
- Add tenant/workspace scope columns to prompt templates before returning shared
  prompt rows from AI Hub.
- Add a real evaluation result store before presenting model benchmark trends as
  historical evaluation data.
- Connect run history to actual agent execution rows once workflow execution is
  persisted; until then the surface must label prompt/provider/audit evidence as
  operational evidence, not completed agent runs.
