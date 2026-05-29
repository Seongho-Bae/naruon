import datetime
import hashlib

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import AuthContext, get_auth_context, is_admin_role
from db.models import LLMProvider, PromptTemplate, SecurityAuditEvent
from db.session import get_db

router = APIRouter(prefix="/api/ai-hub", tags=["ai-hub"])


class AiHubSummaryCard(BaseModel):
    summary_key: str
    label_text: str
    value_text: str
    detail_text: str
    state_code: str


class AiHubPromptCard(BaseModel):
    prompt_key: str
    prompt_title: str
    description_text: str | None
    shared_scope: bool
    owner_label: str
    updated_at: datetime.datetime | None


class AiHubWorkflowCard(BaseModel):
    workflow_key: str
    workflow_title: str
    trigger_source: str
    state_code: str
    evidence_text: str


class AiHubAgentCard(BaseModel):
    agent_key: str
    agent_title: str
    model_label: str
    state_code: str
    configured: bool
    governance_text: str


class AiHubEvaluationMetric(BaseModel):
    metric_key: str
    metric_label: str
    score_value: int
    trend_text: str


class AiHubRunEvent(BaseModel):
    event_key: str
    event_title: str
    state_code: str
    evidence_source: str
    observed_at: datetime.datetime | None
    detail_text: str | None


class AiHubSurfaceResponse(BaseModel):
    summary_cards: list[AiHubSummaryCard]
    prompt_cards: list[AiHubPromptCard]
    workflow_cards: list[AiHubWorkflowCard]
    agent_cards: list[AiHubAgentCard]
    evaluation_metrics: list[AiHubEvaluationMetric]
    run_events: list[AiHubRunEvent]


def _stable_key(prefix: str, *parts: object) -> str:
    digest = hashlib.sha256(
        "|".join(str(part or "") for part in parts).encode("utf-8")
    ).hexdigest()
    return f"{prefix}_{digest[:16]}"


def _prompt_card(prompt: PromptTemplate) -> AiHubPromptCard:
    return AiHubPromptCard(
        prompt_key=_stable_key("prompt", prompt.created_by, prompt.id, prompt.title),
        prompt_title=prompt.title,
        description_text=prompt.description,
        shared_scope=bool(prompt.is_shared),
        owner_label=prompt.created_by,
        updated_at=prompt.updated_at,
    )


def _agent_card(provider: LLMProvider) -> AiHubAgentCard:
    configured = bool(provider.api_key)
    if provider.is_active and configured:
        state_code = "active"
    elif configured:
        state_code = "configured"
    else:
        state_code = "needs_key"

    return AiHubAgentCard(
        agent_key=_stable_key(
            "agent",
            provider.organization_id,
            provider.id,
            provider.name,
        ),
        agent_title=provider.name,
        model_label=provider.provider_type,
        state_code=state_code,
        configured=configured,
        governance_text="organization llm provider registry",
    )


def _workflow_cards(
    prompts: list[AiHubPromptCard],
    active_provider_count: int,
) -> list[AiHubWorkflowCard]:
    workflow_state = "ready" if active_provider_count else "needs_provider"
    evidence_text = (
        "active organization provider is available"
        if active_provider_count
        else "active organization provider is required"
    )
    return [
        AiHubWorkflowCard(
            workflow_key=_stable_key("workflow", prompt.prompt_key),
            workflow_title=f"{prompt.prompt_title} 실행 흐름",
            trigger_source="prompt_template",
            state_code=workflow_state,
            evidence_text=evidence_text,
        )
        for prompt in prompts[:5]
    ]


def _run_events(
    prompts: list[PromptTemplate],
    audit_events: list[SecurityAuditEvent],
) -> list[AiHubRunEvent]:
    events = [
        AiHubRunEvent(
            event_key=_stable_key("event", event.event_uid),
            event_title=f"{event.resource_type} {event.event_action}",
            state_code="recorded",
            evidence_source=event.evidence_source,
            observed_at=event.observed_at,
            detail_text=event.detail_text,
        )
        for event in audit_events
    ]
    if events:
        return events

    return [
        AiHubRunEvent(
            event_key=_stable_key("event", prompt.created_by, prompt.id, prompt.title),
            event_title=f"prompt template updated: {prompt.title}",
            state_code="recorded",
            evidence_source="prompt_templates",
            observed_at=prompt.updated_at,
            detail_text=prompt.description,
        )
        for prompt in prompts[:5]
    ]


def _score(active_provider_count: int, prompt_count: int, audit_count: int) -> int:
    provider_score = 40 if active_provider_count else 0
    prompt_score = min(40, prompt_count * 10)
    audit_score = min(20, audit_count * 5)
    return provider_score + prompt_score + audit_score


def _evaluation_metrics(
    prompt_count: int,
    provider_count: int,
    active_provider_count: int,
    audit_count: int,
) -> list[AiHubEvaluationMetric]:
    return [
        AiHubEvaluationMetric(
            metric_key="prompt_coverage",
            metric_label="프롬프트 커버리지",
            score_value=min(100, prompt_count * 20),
            trend_text=f"{prompt_count} source-backed prompt templates",
        ),
        AiHubEvaluationMetric(
            metric_key="provider_readiness",
            metric_label="Provider 준비도",
            score_value=100 if active_provider_count else 0,
            trend_text=f"{active_provider_count}/{provider_count} active providers",
        ),
        AiHubEvaluationMetric(
            metric_key="audit_evidence",
            metric_label="운영 증거",
            score_value=min(100, audit_count * 20),
            trend_text=f"{audit_count} scoped audit events",
        ),
        AiHubEvaluationMetric(
            metric_key="execution_readiness",
            metric_label="실행 준비도",
            score_value=_score(active_provider_count, prompt_count, audit_count),
            trend_text="derived from provider, prompt, and audit evidence",
        ),
    ]


def _summary_cards(
    prompt_count: int,
    workflow_count: int,
    provider_count: int,
    active_provider_count: int,
    run_event_count: int,
    readiness_score: int,
) -> list[AiHubSummaryCard]:
    return [
        AiHubSummaryCard(
            summary_key="prompt_templates",
            label_text="프롬프트",
            value_text=str(prompt_count),
            detail_text="source-backed templates",
            state_code="ready" if prompt_count else "empty",
        ),
        AiHubSummaryCard(
            summary_key="workflow_blueprints",
            label_text="워크플로우",
            value_text=str(workflow_count),
            detail_text="prompt-derived execution flows",
            state_code="ready" if workflow_count else "empty",
        ),
        AiHubSummaryCard(
            summary_key="ai_providers",
            label_text="AI 에이전트",
            value_text=f"{active_provider_count}/{provider_count}",
            detail_text="active organization providers",
            state_code="ready" if active_provider_count else "needs_provider",
        ),
        AiHubSummaryCard(
            summary_key="evaluation_readiness",
            label_text="평가",
            value_text=f"{readiness_score}%",
            detail_text="derived operational readiness",
            state_code="ready" if readiness_score >= 60 else "attention",
        ),
        AiHubSummaryCard(
            summary_key="run_events",
            label_text="실행 이력",
            value_text=str(run_event_count),
            detail_text="scoped source evidence",
            state_code="ready" if run_event_count else "empty",
        ),
    ]


async def _list_prompts(
    db: AsyncSession,
    auth_context: AuthContext,
) -> list[PromptTemplate]:
    result = await db.execute(
        select(PromptTemplate)
        .where(
            or_(
                PromptTemplate.created_by == auth_context.user_id,
                PromptTemplate.is_shared.is_(True),
            )
        )
        .order_by(desc(PromptTemplate.updated_at))
        .limit(8)
    )
    return list(result.scalars().all())


async def _list_providers(
    db: AsyncSession,
    auth_context: AuthContext,
) -> list[LLMProvider]:
    if auth_context.organization_id is None:
        return []
    result = await db.execute(
        select(LLMProvider)
        .where(LLMProvider.organization_id == auth_context.organization_id)
        .order_by(desc(LLMProvider.updated_at))
        .limit(8)
    )
    return list(result.scalars().all())


async def _list_audit_events(
    db: AsyncSession,
    auth_context: AuthContext,
) -> list[SecurityAuditEvent]:
    if auth_context.organization_id is None:
        return []
    statement = (
        select(SecurityAuditEvent)
        .where(
            SecurityAuditEvent.organization_id == auth_context.organization_id,
            SecurityAuditEvent.workspace_id == auth_context.workspace_id,
            SecurityAuditEvent.resource_type == "llm_provider",
        )
        .order_by(desc(SecurityAuditEvent.observed_at))
        .limit(8)
    )
    if not is_admin_role(auth_context.role):
        statement = statement.where(
            SecurityAuditEvent.actor_user_id == auth_context.user_id
        )
    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/surface", response_model=AiHubSurfaceResponse)
async def get_ai_hub_surface(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> AiHubSurfaceResponse:
    prompts = await _list_prompts(db, auth_context)
    providers = await _list_providers(db, auth_context)
    audit_events = await _list_audit_events(db, auth_context)

    prompt_cards = [_prompt_card(prompt) for prompt in prompts]
    active_provider_count = sum(
        1 for provider in providers if provider.is_active and provider.api_key
    )
    workflow_cards = _workflow_cards(prompt_cards, active_provider_count)
    agent_cards = [_agent_card(provider) for provider in providers]
    run_events = _run_events(prompts, audit_events)
    readiness_score = _score(
        active_provider_count,
        len(prompt_cards),
        len(audit_events),
    )

    return AiHubSurfaceResponse(
        summary_cards=_summary_cards(
            len(prompt_cards),
            len(workflow_cards),
            len(providers),
            active_provider_count,
            len(run_events),
            readiness_score,
        ),
        prompt_cards=prompt_cards,
        workflow_cards=workflow_cards,
        agent_cards=agent_cards,
        evaluation_metrics=_evaluation_metrics(
            len(prompt_cards),
            len(providers),
            active_provider_count,
            len(audit_events),
        ),
        run_events=run_events,
    )
