# Naruon Domain Model Realignment

## Overview
Previous implementations (T-004, T-005, T-006) introduced generic features (`/ai-hub`, `/prompt-studio`, `/settings`) that drifted away from the core UI/UX mocks and created ambiguous bounded contexts for Identity, Tenant configuration, and Self-hosted runner topologies.

This document realigns the Ubiquitous Language and Bounded Contexts.

## Bounded Contexts

### 1. Identity & Organization Context
- **Organization (Workspace):** Represents a corporate entity. Billing and data isolation occur at this level.
- **Organization Admin:** A user with privileges to configure Organization-wide integrations (SSO, Org-wide LLM providers like BYOK, Enterprise Self-hosted runner tokens).
- **Member:** A standard user within an Organization.
- *Previous Error:* "Admin" was used as a generic string across the app without distinguishing System Admin (Naruon SaaS owner) vs. Organization Admin.

### 2. Provider Integration Context (BYOK & LLM)
- **Bring Your Own Key (BYOK):** Organizations can supply their own OpenAI/Anthropic/Gemini keys.
- **Naruon Managed LLM:** A fallback/default if the Organization pays Naruon directly.
- *Previous Error:* The `/settings` UI allowed any user to create "Providers" globally, lacking Workspace/Organization bounding.

### 3. Mailbox Configuration Context
- **Mailbox (Email Account):** Belongs to a Member. A Member can have multiple Mailboxes (e.g., Google, Outlook, Custom IMAP/SMTP).
- *Previous Error:* The app provided no UI for users to configure their IMAP/SMTP credentials.

### 4. Runner Topology Context
- **Self-Hosted Runner (Relay Proxy):** A stateless agent deployed within a corporate intranet to route IMAP/SMTP traffic securely without exposing the intranet to the public internet.
- **Topology:** The runner connects outbound to Naruon (via WebSocket or gRPC tunnel) and routes traffic to the internal Mail Server. It is bound to an Organization.
- *Previous Error:* Runner boundaries were documented but not tied to the Organization context UI.

## Ubiquitous Language & Frontend Nav
The Frontend layout MUST strictly adhere to the provided Figma/UI UX mockups (`frontend/branding/uiux/uiux4.png`).
- **Mail Actions:** 메일 작성
- **Mail Navigation:** 받은 메일, 중요 메일, 보낸 메일, 임시 보관함, 전체 메일
- **AI Hub Navigation (AI 허브 BETA):** 맥락 종합, 판단 포인트, 실행 항목
- **Projects Navigation (프로젝트):** (Dynamic user projects)
- **Labels (라벨):** (Dynamic user labels)
- **Insights (오늘의 인사이트):** 업무 집중 시간 등 하단 위젯

*No "Prompt Studio" or generic "Settings" should replace the core mail navigation layout.* Settings must be accessed via user profile or a dedicated config modal/page, NOT dominating the primary sidebar.

## Action Items
1. Restore `DashboardLayout.tsx` to match `uiux4.png` strictly.
2. Draft proper Organization and User database schemas to fix the identity boundary.
