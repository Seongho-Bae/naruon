import type { Page, Route } from '@playwright/test';

const email = {
  id: 7,
  message_id: '<q2@example.com>',
  source_message_id: '<q2@example.com>',
  thread_id: 'thread-q2',
  sender: '김지현 PM',
  recipients: 'user@naruon.ai',
  reply_to: 'jihyun@naruon.ai',
  subject: 'Q2 출시 계획 및 우선순위 조정',
  date: '2026-05-11T09:30:00Z',
  body: 'Q2 출시 일정과 마케팅 계획을 우선순위 기준으로 재정렬해 보았습니다.',
  snippet: 'Q2 출시 계획과 우선순위 조정 요청입니다.',
  unread: true,
  reply_count: 2,
  score: 0.91,
};

const sibling = {
  ...email,
  id: 8,
  message_id: '<q2-reply@example.com>',
  body: '파트너 미팅 전까지 일정 확인이 필요합니다.',
};

const sentEmail = {
  ...email,
  id: 31,
  message_id: '<sent-q2@example.com>',
  thread_id: 'thread-sent-q2',
  sender: 'Seongho <user@naruon.ai>',
  recipients: 'partner@example.com',
  subject: '벤더 계약 답변 요청',
  date: '2026-05-11T12:30:00Z',
  snippet: 'Please reply when the vendor contract review is ready.',
  unread: false,
  reply_count: 1,
  requires_reply: true,
  is_self_sent: false,
};

const selfSentNote = {
  ...email,
  id: 32,
  message_id: '<self-note@example.com>',
  thread_id: 'thread-self-note',
  sender: 'user@naruon.ai',
  recipients: 'user@naruon.ai',
  subject: '나에게 보낸 지식 메모',
  date: '2026-05-11T13:10:00Z',
  snippet: '다음 분기 전략 회의 전에 지식으로 정리할 메모입니다.',
  unread: false,
  reply_count: 1,
  requires_reply: false,
  is_self_sent: true,
};

const sentFollowUp = {
  ...email,
  id: 33,
  message_id: '<sent-follow-up@example.com>',
  thread_id: 'thread-sent-follow-up',
  sender: 'Seongho <user@naruon.ai>',
  recipients: 'finance@example.com',
  subject: '예산 승인 후속 확인',
  date: '2026-05-11T14:20:00Z',
  snippet: 'Can you confirm whether the budget approval is ready?',
  unread: false,
  reply_count: 1,
  requires_reply: true,
  is_self_sent: false,
};

const sentResolved = {
  ...email,
  id: 34,
  message_id: '<sent-resolved@example.com>',
  thread_id: 'thread-sent-resolved',
  sender: 'Seongho <user@naruon.ai>',
  recipients: 'ops@example.com',
  subject: '운영 점검 회신 완료',
  date: '2026-05-11T15:00:00Z',
  snippet: '운영 점검 후속 메일이며 이미 회신이 연결된 스레드입니다.',
  unread: false,
  reply_count: 2,
  requires_reply: false,
  is_self_sent: false,
};

const sentKnowledge = {
  ...email,
  id: 35,
  message_id: '<sent-knowledge@example.com>',
  thread_id: 'thread-sent-knowledge',
  sender: 'user@naruon.ai',
  recipients: 'user@naruon.ai',
  subject: '고객 미팅 지식 정리',
  date: '2026-05-11T16:00:00Z',
  snippet: '고객 미팅에서 나온 판단 포인트를 지식으로 정리합니다.',
  unread: false,
  reply_count: 1,
  requires_reply: false,
  is_self_sent: true,
};

const mobileAttachmentResult = {
  ...email,
  id: 17,
  subject: '브랜드 에셋 검토 자료',
  sender: '박서연 디자이너',
  date: '2026-05-11T10:15:00Z',
  snippet: '모바일 워크스페이스에 필요한 브랜드 에셋과 첨부 자료입니다.',
};

const mobilePeopleResult = {
  ...email,
  id: 18,
  subject: '강민수 의사결정 메모',
  sender: '강민수 리드',
  date: '2026-05-11T11:00:00Z',
  snippet: '일정과 사람 맥락을 함께 확인해야 하는 의사결정 메모입니다.',
};

const calendarCandidate = {
  ...email,
  id: 27,
  subject: '파트너 미팅 일정 확정',
  sender: '이지은 파트너',
  date: '2026-05-12T13:00:00Z',
  snippet: '파트너 미팅 일정을 확정하고 캘린더에 반영해야 합니다.',
};

const aiHubPrompts = [
  { id: 101, title: 'Q2 출시 판단', description: '출시 일정과 파트너 리스크를 함께 검토합니다.' },
  { id: 102, title: '계약 리스크 점검', description: '계약서, 첨부, 메일 스레드를 판단 포인트로 정리합니다.' },
  { id: 103, title: '후속 실행 항목', description: '답장, 일정, 할 일을 담당자별 실행 흐름으로 나눕니다.' },
];

const runnerConfig = {
  workspace_id: 'workspace-org-acme',
  configured: true,
  fingerprint: '***abc12345',
  updated_at: '2026-05-27T06:00:00Z',
  connector_manifest: {
    role: 'self-hosted_connector',
    network_mode: 'outbound_only',
    control_plane_domain: 'naruon.net',
    local_protocols: ['imap', 'pop3', 'smtp', 'caldav', 'carddav', 'webdav'],
    prohibited_roles: ['smtp_server', 'imap_server', 'mx_host'],
    runner_usage: 'ci_smoke_only',
  },
};

const operationalSignals = {
  workspace_id: 'workspace-org-acme',
  audit_event: 'observability.operational_signals.viewed',
  telemetry: {
    prometheus_metrics_enabled: true,
    otel_traces_enabled: true,
    otel_endpoint_configured: true,
    otel_endpoint_host: 'otel-collector:4317',
  },
  connector: {
    workspace_id: 'workspace-org-acme',
    registration_state: 'registration_configured',
    connection_state: 'connected',
    active_connection_count: 1,
    control_plane_domain: 'naruon.net',
    network_mode: 'outbound_only',
    runner_usage: 'ci_smoke_only',
    local_protocols: ['imap', 'pop3', 'smtp', 'caldav', 'carddav', 'webdav'],
    last_heartbeat_at: '2026-05-27T12:00:00Z',
    last_disconnect_at: null,
    queue_depth_state: 'not_reported',
  },
  signals: [
    {
      signal_key: 'connector_heartbeat',
      display_name: 'Connector heartbeat',
      state: 'enabled',
      evidence_source: 'runner WebSocket manager',
      detail: 'Live heartbeat uses active outbound runner sockets.',
      provider_write_executed: false,
    },
    {
      signal_key: 'sync_lag',
      display_name: 'Sync lag',
      state: 'instrumentation_pending',
      evidence_source: 'provider adapters',
      detail: 'Provider sync lag will be emitted by source-backed connector jobs.',
      provider_write_executed: false,
    },
    {
      signal_key: 'writeback_conflicts',
      display_name: 'Writeback conflicts',
      state: 'intent_only',
      evidence_source: 'calendar and WebDAV writeback-intent APIs',
      detail: 'Conflict handling is surfaced at intent boundaries.',
      provider_write_executed: false,
    },
  ],
};

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
};

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    headers: CORS_HEADERS,
    body: JSON.stringify(body),
  });
}

export async function mockDashboardApi(page: Page, onApiRequest?: (path: string) => void) {
  await page.route('**/api/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    onApiRequest?.(path);

    if (request.method() === 'OPTIONS') {
      await route.fulfill({
        status: 204,
        headers: CORS_HEADERS,
      });
      return;
    }

    if (path === '/api/emails' && request.method() === 'GET') {
      if (url.searchParams.get('folder') === 'sent') {
        await fulfillJson(route, { emails: [sentEmail, selfSentNote, sentFollowUp, sentResolved, sentKnowledge] });
        return;
      }
      await fulfillJson(route, { emails: [email] });
      return;
    }

    if (path === '/api/prompts' && request.method() === 'GET') {
      await fulfillJson(route, aiHubPrompts);
      return;
    }

    if (path === '/api/runner-config' && request.method() === 'GET') {
      await fulfillJson(route, runnerConfig);
      return;
    }

    if (path === '/api/observability/operational-signals' && request.method() === 'GET') {
      await fulfillJson(route, operationalSignals);
      return;
    }

    if (path === '/api/search' && request.method() === 'POST') {
      let body: { query?: string } = {};
      try {
        body = JSON.parse(request.postData() || '{}') as { query?: string };
      } catch {
        body = {};
      }

      if (body.query?.includes('회의')) {
        await fulfillJson(route, { results: [calendarCandidate, sibling] });
        return;
      }

      await fulfillJson(route, { results: [email, mobileAttachmentResult, mobilePeopleResult] });
      return;
    }

    if (path === '/api/emails/7') {
      await fulfillJson(route, email);
      return;
    }

    if (path === '/api/emails/thread/thread-q2') {
      await fulfillJson(route, { thread: [email, sibling] });
      return;
    }

    if (path === '/api/llm/summarize') {
      await fulfillJson(route, {
        summary: '출시 일정, 마케팅 계획, 파트너 미팅을 하나의 실행 흐름으로 정리해야 합니다.',
        todos: ['리소스 배정 검토 회의', '마케팅 캠페인 오프'],
      });
      return;
    }

    if (path === '/api/llm/draft') {
      await fulfillJson(route, { draft: '검토 후 일정과 우선순위를 정리해 공유드리겠습니다.' });
      return;
    }

    if (path === '/api/emails/send') {
      await fulfillJson(route, { simulated: true });
      return;
    }

    if (path === '/api/calendar/writeback-sources' && request.method() === 'GET') {
      await fulfillJson(route, [
        {
          source_id: 'caldav-primary',
          provider: 'Customer CalDAV',
          protocol: 'caldav',
          owner_id: 'default',
          organization_id: 'org-acme',
          capabilities: ['read', 'write', 'etag'],
          writeback_enabled: true,
          etag: 'etag-caldav-primary',
        },
      ]);
      return;
    }

    if (path === '/api/calendar/writeback-intent' && request.method() === 'POST') {
      await fulfillJson(route, {
        workspace_id: 'default',
        target_source_id: 'caldav-primary',
        protocol: 'caldav',
        writeback_mode: 'customer_owned',
        requires_if_match: false,
        if_match: null,
        provenance: {
          created_by: 'default',
          source_provider: 'Customer CalDAV',
          source_protocol: 'caldav',
        },
        audit_event: 'calendar.writeback_intent.created',
      });
      return;
    }

    if (path === '/api/webdav/accounts' && request.method() === 'GET') {
      await fulfillJson(route, [
        {
          source_id: 'webdav_src_primary',
          server_url: 'https://webdav.naruon.net',
          username: 'demo_user',
          writeback_enabled: true,
        },
      ]);
      return;
    }

    if (path === '/api/webdav/folders' && request.method() === 'GET') {
      await fulfillJson(route, [
        {
          folder_id: 1,
          project_name: 'Naruon Roadmap 2026',
          webdav_path: '/Projects/Naruon_Roadmap_2026',
        },
        {
          folder_id: 2,
          project_name: 'Marketing Assets',
          webdav_path: '/Projects/Marketing_Assets',
        },
      ]);
      return;
    }

    if (path === '/api/webdav/writeback-intent' && request.method() === 'POST') {
      await fulfillJson(route, {
        intent: 'writeback',
        source_id: 'webdav_src_primary',
        server_url: 'https://webdav.naruon.net',
        requires_if_match: true,
        provenance: 'server-authoritative',
      });
      return;
    }

    if (path === '/api/emails/unique-thread-intent' && request.method() === 'POST') {
      await fulfillJson(route, {
        status: 'intent_ready',
        candidates_checked: 2,
        duplicates_found: 2,
        provider_write_executed: false,
        provenance: 'server-authoritative',
        audit_event: 'email.unique_thread_intent.created',
        thread_updates: [
          {
            candidate_key: 'zip-q2-root',
            canonical_thread_id: 'thread-q2-root',
            dedupe_key: 'q2-root@example.com',
            match_reason: 'message_id',
            existing_message_id: 'q2-root@example.com',
          },
          {
            candidate_key: 'forwarded-copy',
            canonical_thread_id: 'thread-q2-root',
            dedupe_key: 'sha256:duplicate',
            match_reason: 'fingerprint',
            existing_message_id: 'q2-root@example.com',
          },
        ],
      });
      return;
    }

    if (path === '/api/webdav/knowledge-materialization-intent' && request.method() === 'POST') {
      await fulfillJson(route, {
        intent: 'knowledge_materialization',
        status: 'intent_ready',
        task_id: 'task-self-knowledge',
        source_type: 'self_sent_knowledge',
        source_email_id: '<self-note@example.com>',
        source_thread_id: 'thread-self-note',
        source_id: 'webdav_src_primary',
        server_url: 'https://webdav.naruon.net',
        target_path: '/Naruon/Notes/task-self-knowledge.md',
        requires_if_match: true,
        provenance: 'server-authoritative',
        provider_write_executed: false,
        audit_event: 'webdav.self_sent_knowledge_intent.created',
      });
      return;
    }

    if (path === '/api/tasks' && request.method() === 'GET') {
      await fulfillJson(route, [
        {
          id: 'task-q2-owner',
          title: '리소스 배정 검토 회의',
          status: 'blocked',
          priority: 'urgent',
          source_type: 'email',
          source_email_id: '<q2@example.com>',
          related_thread_id: 'thread-q2',
          created_at: '2026-05-19T00:00:00Z',
          updated_at: '2026-05-21T00:00:00Z',
        },
        {
          id: 'task-reply-followup',
          title: '보낸 메일 회신 SLA 확인',
          status: 'in_progress',
          priority: 'high',
          source_type: 'email',
          source_email_id: '<sent-q2@example.com>',
          related_thread_id: 'thread-sent-q2',
          created_at: '2026-05-19T00:00:00Z',
          updated_at: '2026-05-22T00:00:00Z',
        },
        {
          id: 'task-calendar-writeback',
          title: '회의 후보 CalDAV 반영 검토',
          status: 'open',
          priority: 'normal',
          source_type: 'calendar',
          source_email_id: '<q2@example.com>',
          related_thread_id: 'thread-q2',
          created_at: '2026-05-19T00:00:00Z',
          updated_at: '2026-05-23T00:00:00Z',
        },
        {
          id: 'task-webdav-evidence',
          title: '첨부파일 WebDAV 폴더 정리',
          status: 'done',
          priority: 'low',
          source_type: 'webdav',
          source_email_id: '<q2@example.com>',
          related_thread_id: 'thread-q2',
          created_at: '2026-05-19T00:00:00Z',
          updated_at: '2026-05-24T00:00:00Z',
        },
        {
          id: 'task-self-knowledge',
          title: '나에게 보낸 지식 메모 정리',
          status: 'open',
          priority: 'normal',
          source_type: 'self_sent_knowledge',
          source_email_id: '<self-note@example.com>',
          related_thread_id: 'thread-self-note',
          created_at: '2026-05-19T00:00:00Z',
          updated_at: '2026-05-25T00:00:00Z',
        },
      ]);
      return;
    }

    if (path === '/api/tasks/from-email' && request.method() === 'POST') {
      await fulfillJson(route, {
        created: 2,
        tasks: [
          {
            id: 'task-q2-owner',
            title: '리소스 배정 검토 회의',
            status: 'open',
            priority: 'normal',
            source_type: 'email',
            source_email_id: '<q2@example.com>',
            related_thread_id: 'thread-q2',
            created_at: '2026-05-19T00:00:00Z',
            updated_at: '2026-05-19T00:00:00Z',
          },
          {
            id: 'task-q2-marketing',
            title: '마케팅 캠페인 오프',
            status: 'open',
            priority: 'normal',
            source_type: 'email',
            source_email_id: '<q2@example.com>',
            related_thread_id: 'thread-q2',
            created_at: '2026-05-19T00:00:00Z',
            updated_at: '2026-05-19T00:00:00Z',
          },
        ],
      });
      return;
    }

    if (path === '/api/tasks/task-q2-owner' && request.method() === 'PATCH') {
      await fulfillJson(route, {
        id: 'task-q2-owner',
        title: '리소스 배정 검토 회의',
        status: 'done',
        priority: 'urgent',
        source_type: 'email',
        source_email_id: '<q2@example.com>',
        related_thread_id: 'thread-q2',
        created_at: '2026-05-19T00:00:00Z',
        updated_at: '2026-05-27T08:00:00Z',
      });
      return;
    }

    if (path === '/api/network/graph') {
      await fulfillJson(route, {
        nodes: [
          { id: 'sender-1', label: '김지현 PM', title: 'PM' },
          { id: 'owner-1', label: '사용자', title: 'Naruon owner' },
        ],
        edges: [{ source: 'sender-1', target: 'owner-1', weight: 2, title: '관련 메일' }],
      });
      return;
    }

    if (path === '/api/ontology/relationships' && request.method() === 'GET') {
      await fulfillJson(route, [
        {
          sender_email: 'jihyun@naruon.ai',
          parent_sender_email: 'user@naruon.ai',
          source_message_id: '<q2@example.com>',
          source_thread_id: 'thread-q2',
          relationship_type: 'colleague',
          confidence_score: 0.85,
          next_action: 'track_reply_and_tasks',
          action_reason: 'Same-domain sender; preserve reply and task follow-up.',
        },
      ]);
      return;
    }

    await route.fulfill({ status: 404, headers: CORS_HEADERS, body: 'Not mocked' });
  });
}
