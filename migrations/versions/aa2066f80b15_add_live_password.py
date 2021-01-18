"""add live password

Revision ID: aa2066f80b15
Revises: d88bf4793397
Create Date: 2021-01-14 17:50:52.406901

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'aa2066f80b15'
down_revision = 'd88bf4793397'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mf_live_stream', sa.Column('room_password', sa.String(length=255), nullable=True, comment='房间密码'))
    op.alter_column('mf_live_stream', 'room_name',
               existing_type=mysql.VARCHAR(length=255),
               comment='房间名称',
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('mf_live_stream', 'room_name',
               existing_type=mysql.VARCHAR(length=255),
               comment=None,
               existing_comment='房间名称',
               existing_nullable=True)
    op.drop_column('mf_live_stream', 'room_password')
    # ### end Alembic commands ###
