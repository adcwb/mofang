"""add user tansaction password

Revision ID: ee09eb96fed6
Revises: 27caa5c6beda
Create Date: 2020-12-11 20:03:40.402782

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee09eb96fed6'
down_revision = '27caa5c6beda'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mf_user', sa.Column('_transaction_password', sa.String(length=255), nullable=True, comment='交易密码'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('mf_user', '_transaction_password')
    # ### end Alembic commands ###
