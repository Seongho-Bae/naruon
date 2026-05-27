# Branding & GNB Details Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the missing high-fidelity UI requirements from `frontend/branding` mockups, make the startup screen configurable, and ensure responsive/hamburger menu behaviors are fully functional and tested across resolutions.

**Architecture:** Use existing React components but elevate them with actual detailed functionality as per the mockups. Enhance `DashboardLayout` and `WorkspaceHome` to respect user preferences for the initial screen. 

**Tech Stack:** Next.js (App Router), Tailwind CSS, React, Playwright for E2E resolution testing.

---

### Task 1: Configurable Startup Screen

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/store/userPreferences.ts` (or similar state management)
- Test: `frontend/src/app/page.test.tsx`

- [ ] **Step 1: Add user preference for startup view**
- [ ] **Step 2: Update `Home` page logic to read preference**
- [ ] **Step 3: Render either `WorkspaceHome`, `EmailList`, or `Calendar` accordingly**
- [ ] **Step 4: Update E2E and Unit Tests**

### Task 2: Mobile Responsive & Hamburger Menu Verification

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx` or `Navigation.tsx`
- Test: `tests/e2e/mobile-hamburger.spec.ts`

- [ ] **Step 1: Write Playwright E2E test for mobile viewport**
- [ ] **Step 2: Ensure Hamburger menu toggles correctly and prevents body scroll**
- [ ] **Step 3: Ensure bottom action bars and panels are safe-area padded**
- [ ] **Step 4: Fix any UI issues detected in resolution tests**

### Task 3: GNB Detail Views (Projects, Tasks, Data)

**Files:**
- Modify: `frontend/src/app/projects/page.tsx`
- Modify: `frontend/src/app/tasks/page.tsx`
- Modify: `frontend/src/app/data/page.tsx`

- [ ] **Step 1: Implement Project List, Milestones, and Decision Log UI**
- [ ] **Step 2: Implement Tasks Kanban, Delegation, and Detailed View UI**
- [ ] **Step 3: Implement Data Repository, Pipeline Status, and Embedding Stats UI**
- [ ] **Step 4: Write tests for these new detail views**
