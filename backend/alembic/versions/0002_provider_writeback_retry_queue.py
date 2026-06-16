"""add provider writeback retry queue

Revision ID: 0002_provider_retry_queue
Revises: 0001_initial_control_plane
Create Date: 2026-06-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_provider_retry_queue"
down_revision = "0001_initial_control_plane"

_RETRY_ITEMS_TABLE = "provider_writeback_retry_items"


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if not inspector.has_table(_RETRY_ITEMS_TABLE):
        op.create_table(
            _RETRY_ITEMS_TABLE,
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
    _create_indexes(if_not_exists=True)


def downgrade() -> None:
    _drop_indexes(if_exists=True)
    op.drop_table(_RETRY_ITEMS_TABLE, if_exists=True)


def _create_indexes(*, if_not_exists: bool = False) -> None:
    op.create_index(
        "ix_provider_writeback_retry_items_scope_state",
        _RETRY_ITEMS_TABLE,
        ["organization_id", "workspace_id", "retry_state", "next_retry_at"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_source_action",
        _RETRY_ITEMS_TABLE,
        ["source_uid", "command_action"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_organization_id",
        _RETRY_ITEMS_TABLE,
        ["organization_id"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_workspace_id",
        _RETRY_ITEMS_TABLE,
        ["workspace_id"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_source_uid",
        _RETRY_ITEMS_TABLE,
        ["source_uid"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_command_action",
        _RETRY_ITEMS_TABLE,
        ["command_action"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_retry_state",
        _RETRY_ITEMS_TABLE,
        ["retry_state"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_last_error_code",
        _RETRY_ITEMS_TABLE,
        ["last_error_code"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_runner_request_uid",
        _RETRY_ITEMS_TABLE,
        ["runner_request_uid"],
        if_not_exists=if_not_exists,
    )
    op.create_index(
        "ix_provider_writeback_retry_items_next_retry_at",
        _RETRY_ITEMS_TABLE,
        ["next_retry_at"],
        if_not_exists=if_not_exists,
    )


def _drop_indexes(*, if_exists: bool = False) -> None:
    op.drop_index(
        "ix_provider_writeback_retry_items_next_retry_at",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_runner_request_uid",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_last_error_code",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_retry_state",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_command_action",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_source_uid",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_workspace_id",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_organization_id",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_source_action",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
    op.drop_index(
        "ix_provider_writeback_retry_items_scope_state",
        table_name=_RETRY_ITEMS_TABLE,
        if_exists=if_exists,
    )
