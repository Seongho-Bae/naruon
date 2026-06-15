"""add provider writeback retry queue

Revision ID: 0002_provider_retry_queue
Revises: 0001_initial_control_plane
Create Date: 2026-06-15 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = "0002_provider_retry_queue"
down_revision = "0001_initial_control_plane"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if not inspector.has_table("provider_writeback_retry_items"):
        op.create_table(
            "provider_writeback_retry_items",
            sa.Column("retry_item_uid", sa.String(), nullable=False),
            sa.Column("organization_id", sa.String(), nullable=False),
            sa.Column("workspace_id", sa.String(), nullable=False),
            sa.Column("source_uid", sa.String(), nullable=True),
            sa.Column("command_action", sa.String(), nullable=False),
            sa.Column("command_payload_encrypted", sa.String(), nullable=False),
            sa.Column("retry_state", sa.String(), nullable=False),
            sa.Column("last_error_code", sa.String(), nullable=False),
            sa.Column("runner_request_uid", sa.String(), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("retry_item_uid"),
        )
    for statement in _provider_writeback_retry_index_sql():
        connection.execute(sa.text(statement))


def downgrade() -> None:
    connection = op.get_bind()
    for index_name in reversed(_provider_writeback_retry_index_names()):
        connection.execute(sa.text(f"DROP INDEX IF EXISTS {index_name}"))
    connection.execute(sa.text("DROP TABLE IF EXISTS provider_writeback_retry_items"))


def _provider_writeback_retry_index_names() -> list[str]:
    return [
        "ix_provider_writeback_retry_items_scope_state",
        "ix_provider_writeback_retry_items_source_action",
        "ix_provider_writeback_retry_items_organization_id",
        "ix_provider_writeback_retry_items_workspace_id",
        "ix_provider_writeback_retry_items_source_uid",
        "ix_provider_writeback_retry_items_command_action",
        "ix_provider_writeback_retry_items_retry_state",
        "ix_provider_writeback_retry_items_last_error_code",
        "ix_provider_writeback_retry_items_runner_request_uid",
        "ix_provider_writeback_retry_items_next_retry_at",
    ]


def _provider_writeback_retry_index_sql() -> list[str]:
    return [
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_scope_state
        ON provider_writeback_retry_items
        (organization_id, workspace_id, retry_state, next_retry_at)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_source_action
        ON provider_writeback_retry_items (source_uid, command_action)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_organization_id
        ON provider_writeback_retry_items (organization_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_workspace_id
        ON provider_writeback_retry_items (workspace_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_source_uid
        ON provider_writeback_retry_items (source_uid)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_command_action
        ON provider_writeback_retry_items (command_action)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_retry_state
        ON provider_writeback_retry_items (retry_state)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_last_error_code
        ON provider_writeback_retry_items (last_error_code)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_runner_request_uid
        ON provider_writeback_retry_items (runner_request_uid)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_provider_writeback_retry_items_next_retry_at
        ON provider_writeback_retry_items (next_retry_at)
        """,
    ]
