"""add provider writeback retry queue

Revision ID: 0002_provider_retry_queue
Revises: 0001_initial_control_plane
Create Date: 2026-06-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_provider_retry_queue"
down_revision = "0001_initial_control_plane"
_RETRY_TABLE = "provider_writeback_retry_items"


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if not inspector.has_table(_RETRY_TABLE):
        op.create_table(
            _RETRY_TABLE,
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

    existing_index_names = _existing_provider_writeback_retry_index_names(inspector)
    for index_name, column_names in _provider_writeback_retry_indexes():
        if index_name in existing_index_names:
            continue
        op.create_index(index_name, _RETRY_TABLE, column_names)
        existing_index_names.add(index_name)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if not inspector.has_table(_RETRY_TABLE):
        return

    existing_index_names = _existing_provider_writeback_retry_index_names(inspector)
    for index_name in reversed(_provider_writeback_retry_index_names()):
        if index_name in existing_index_names:
            op.drop_index(index_name, table_name=_RETRY_TABLE)
    op.drop_table(_RETRY_TABLE)


def _existing_provider_writeback_retry_index_names(inspector) -> set[str]:
    return {
        index["name"]
        for index in inspector.get_indexes(_RETRY_TABLE)
        if isinstance(index.get("name"), str)
    }


def _provider_writeback_retry_index_names() -> list[str]:
    return [index_name for index_name, _column_names in _provider_writeback_retry_indexes()]


def _provider_writeback_retry_indexes() -> list[tuple[str, list[str]]]:
    return [
        (
            "ix_provider_writeback_retry_items_scope_state",
            ["organization_id", "workspace_id", "retry_state", "next_retry_at"],
        ),
        (
            "ix_provider_writeback_retry_items_source_action",
            ["source_uid", "command_action"],
        ),
        ("ix_provider_writeback_retry_items_organization_id", ["organization_id"]),
        ("ix_provider_writeback_retry_items_workspace_id", ["workspace_id"]),
        ("ix_provider_writeback_retry_items_source_uid", ["source_uid"]),
        ("ix_provider_writeback_retry_items_command_action", ["command_action"]),
        ("ix_provider_writeback_retry_items_retry_state", ["retry_state"]),
        ("ix_provider_writeback_retry_items_last_error_code", ["last_error_code"]),
        ("ix_provider_writeback_retry_items_runner_request_uid", ["runner_request_uid"]),
        ("ix_provider_writeback_retry_items_next_retry_at", ["next_retry_at"]),
    ]
