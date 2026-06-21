"""add ai hub workflow registry and run records

Revision ID: 0004_ai_hub_workflow_runs
Revises: 0003_prompt_template_scope
Create Date: 2026-06-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_ai_hub_workflow_runs"
down_revision = "0003_prompt_template_scope"

_WORKFLOW_TABLE = "workflow_definitions"
_RUN_TABLE = "agent_run_records"


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not inspector.has_table(_WORKFLOW_TABLE):
        op.create_table(
            _WORKFLOW_TABLE,
            sa.Column("workflow_uid", sa.String(), nullable=False),
            sa.Column("organization_id", sa.String(), nullable=False),
            sa.Column("workspace_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("workflow_name", sa.String(), nullable=False),
            sa.Column("workflow_description", sa.Text(), nullable=True),
            sa.Column("steps_json", sa.JSON(), nullable=False),
            sa.Column("state_code", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("workflow_uid"),
        )

    if not inspector.has_table(_RUN_TABLE):
        op.create_table(
            _RUN_TABLE,
            sa.Column("run_uid", sa.String(), nullable=False),
            sa.Column("workflow_uid", sa.String(), nullable=False),
            sa.Column("organization_id", sa.String(), nullable=False),
            sa.Column("workspace_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("status_code", sa.String(), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("result_summary", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(
                ["workflow_uid"],
                ["workflow_definitions.workflow_uid"],
            ),
            sa.PrimaryKeyConstraint("run_uid"),
        )

    for table_name, indexes in _ai_hub_indexes().items():
        for index_name, column_names in indexes:
            op.create_index(
                index_name,
                table_name,
                column_names,
                if_not_exists=True,
            )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if inspector.has_table(_RUN_TABLE):
        for index_name, _column_names in reversed(_ai_hub_indexes()[_RUN_TABLE]):
            op.drop_index(index_name, table_name=_RUN_TABLE, if_exists=True)
        op.drop_table(_RUN_TABLE)

    if inspector.has_table(_WORKFLOW_TABLE):
        for index_name, _column_names in reversed(
            _ai_hub_indexes()[_WORKFLOW_TABLE]
        ):
            op.drop_index(index_name, table_name=_WORKFLOW_TABLE, if_exists=True)
        op.drop_table(_WORKFLOW_TABLE)


def _ai_hub_indexes() -> dict[str, list[tuple[str, list[str]]]]:
    return {
        _WORKFLOW_TABLE: [
            (
                "ix_workflow_definitions_scope_time",
                ["organization_id", "workspace_id", "updated_at"],
            ),
            (
                "ix_workflow_definitions_owner_scope",
                ["user_id", "organization_id", "workspace_id", "updated_at"],
            ),
        ],
        _RUN_TABLE: [
            (
                "ix_agent_run_records_scope_time",
                ["organization_id", "workspace_id", "started_at"],
            ),
            (
                "ix_agent_run_records_owner_scope",
                ["user_id", "organization_id", "workspace_id", "started_at"],
            ),
            (
                "ix_agent_run_records_workflow_time",
                ["workflow_uid", "started_at"],
            ),
        ],
    }
