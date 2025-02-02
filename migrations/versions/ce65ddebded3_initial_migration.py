"""Initial migration

Revision ID: ce65ddebded3
Revises: 
Create Date: 2025-01-08 13:02:00.428178

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce65ddebded3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
    sa.Column('sha256_content', sa.String(length=255), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('orig_filename', sa.String(length=255), nullable=False),
    sa.Column('file_type', sa.String(length=50), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_files'))
    )
    with op.batch_alter_table('files', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_files_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_files_filename'), ['filename'], unique=False)
        batch_op.create_index(batch_op.f('ix_files_orig_filename'), ['orig_filename'], unique=False)
        batch_op.create_index(batch_op.f('ix_files_sha256_content'), ['sha256_content'], unique=False)
        batch_op.create_index(batch_op.f('ix_files_updated_at'), ['updated_at'], unique=False)

    op.create_table('documents',
    sa.Column('type', sa.String(length=255), nullable=False),
    sa.Column('file_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], name=op.f('fk_documents_file_id_files')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_documents'))
    )
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_documents_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_file_id'), ['file_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_type'), ['type'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_updated_at'), ['updated_at'], unique=False)

    op.create_table('analysis_results',
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('analysis_result', sa.JSON(), nullable=False),
    sa.Column('analysis_steps', sa.JSON(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_analysis_results_document_id_documents')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_analysis_results'))
    )
    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_analysis_results_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_analysis_results_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_analysis_results_updated_at'), ['updated_at'], unique=False)

    op.create_table('pages',
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=False),
    sa.Column('page_content', sa.Text(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_pages_document_id_documents')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pages'))
    )
    with op.batch_alter_table('pages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pages_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_pages_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pages_page_number'), ['page_number'], unique=False)
        batch_op.create_index(batch_op.f('ix_pages_updated_at'), ['updated_at'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pages_updated_at'))
        batch_op.drop_index(batch_op.f('ix_pages_page_number'))
        batch_op.drop_index(batch_op.f('ix_pages_document_id'))
        batch_op.drop_index(batch_op.f('ix_pages_created_at'))

    op.drop_table('pages')
    with op.batch_alter_table('analysis_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_analysis_results_updated_at'))
        batch_op.drop_index(batch_op.f('ix_analysis_results_document_id'))
        batch_op.drop_index(batch_op.f('ix_analysis_results_created_at'))

    op.drop_table('analysis_results')
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_documents_updated_at'))
        batch_op.drop_index(batch_op.f('ix_documents_type'))
        batch_op.drop_index(batch_op.f('ix_documents_file_id'))
        batch_op.drop_index(batch_op.f('ix_documents_created_at'))

    op.drop_table('documents')
    with op.batch_alter_table('files', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_files_updated_at'))
        batch_op.drop_index(batch_op.f('ix_files_sha256_content'))
        batch_op.drop_index(batch_op.f('ix_files_orig_filename'))
        batch_op.drop_index(batch_op.f('ix_files_filename'))
        batch_op.drop_index(batch_op.f('ix_files_created_at'))

    op.drop_table('files')
    # ### end Alembic commands ###
