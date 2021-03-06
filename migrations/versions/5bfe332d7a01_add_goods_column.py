"""add goods column

Revision ID: 5bfe332d7a01
Revises: 43aa4b95837e
Create Date: 2021-01-04 17:21:17.483748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bfe332d7a01'
down_revision = '43aa4b95837e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mf_goods', sa.Column('prop_type', sa.Integer(), nullable=True, comment='道具类型'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('mf_goods', 'prop_type')
    # ### end Alembic commands ###
