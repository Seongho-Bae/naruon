import logging
from email import utils as email_utils
from typing import Any, Dict
from sqlalchemy import select
from db.models import Email, SenderRelationship
from services.email_service import process_self_to_self
from services.knowledge_extractor import extract_knowledge_from_self_sent

logger = logging.getLogger(__name__)


class OntologyService:
    def __init__(self):
        self.relationships = {}

    def next_action_for_relationship(self, relationship_type: str) -> Dict[str, str]:
        normalized_type = relationship_type.strip().lower()
        if normalized_type == "newsletter":
            return {
                "next_action": "summarize_then_archive",
                "action_reason": "Bulk sender; summarize signal before lowering priority.",
            }
        if normalized_type == "colleague":
            return {
                "next_action": "track_reply_and_tasks",
                "action_reason": "Same-domain sender; preserve reply and task follow-up.",
            }
        if normalized_type in {"client", "vendor"}:
            return {
                "next_action": "prepare_response_draft",
                "action_reason": "External business sender; keep response intent visible.",
            }
        return {
            "next_action": "classify_sender",
            "action_reason": "Relationship is unknown; capture more evidence first.",
        }

    def analyze_sender_relationship(
        self, user_email: str, sender_email: str, email_content: str
    ) -> Dict[str, Any]:
        """
        Analyze content to build the user's sender relationship graph.
        """
        # A simple stub logic for Phase 10 implementation
        relationship_type = "Unknown"
        confidence = 0.5

        if "unsubscribe" in email_content.lower():
            relationship_type = "Newsletter"
            confidence = 0.9
        elif "@" in user_email and "@" in sender_email:
            user_domain = user_email.split("@")[1].lower()
            sender_domain = sender_email.split("@")[1].lower()
            if user_domain == sender_domain:
                relationship_type = "Colleague"
                confidence = 0.85

        action = self.next_action_for_relationship(relationship_type)
        logger.info(
            "Analyzed sender relationship %s as %s with confidence %.2f",
            sender_email,
            relationship_type,
            confidence,
        )
        return {
            "type": relationship_type,
            "confidence": confidence,
            **action,
        }

    async def save_relationship(
        self,
        session,
        user_email: str,
        sender_email: str,
        email_content: str,
        user_id: str,
        organization_id: str | None,
    ):
        analysis = self.analyze_sender_relationship(
            user_email, sender_email, email_content
        )

        stmt = select(SenderRelationship).where(
            SenderRelationship.user_id == user_id,
            SenderRelationship.sender_email == sender_email,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.relationship_type = analysis["type"]
            existing.confidence_score = analysis["confidence"]
        else:
            new_rel = SenderRelationship(
                user_id=user_id,
                organization_id=organization_id,
                sender_email=sender_email,
                relationship_type=analysis["type"],
                confidence_score=analysis["confidence"],
            )
            session.add(new_rel)
        return analysis

    async def process_knowledge_node(
        self,
        session,
        email_data: dict,
        user_id: str,
        organization_id: str | None,
        source_email: Email | None = None,
    ):
        sender = str(email_data.get("sender") or "")
        _, sender_address = email_utils.parseaddr(sender)
        if not process_self_to_self(email_data, sender_address):
            return None
        if source_email is None:
            logger.info(
                "Skipping self-sent knowledge extraction for user %s without source email row",
                user_id,
            )
            return None
        if (
            source_email.user_id != user_id
            or source_email.organization_id != organization_id
        ):
            return None
        return await extract_knowledge_from_self_sent(session, source_email)


ontology_service = OntologyService()
