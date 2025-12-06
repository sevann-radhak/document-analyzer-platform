"""create documents table

Revision ID: 004
Revises: 003
Create Date: 2024-12-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('classification', sa.String(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('s3_key', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('s3_key')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_s3_key'), 'documents', ['s3_key'], unique=True)
    op.create_index(op.f('ix_documents_classification'), 'documents', ['classification'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_classification'), table_name='documents')
    op.drop_index(op.f('ix_documents_s3_key'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')

