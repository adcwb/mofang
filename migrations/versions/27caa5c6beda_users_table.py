"""users table

Revision ID: 27caa5c6beda
Revises: 
Create Date: 2020-12-01 16:08:51.114406

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27caa5c6beda'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mf_user',
    sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
    sa.Column('is_deleted', sa.Boolean(), nullable=True, comment='逻辑删除'),
    sa.Column('orders', sa.Integer(), nullable=True, comment='排序'),
    sa.Column('status', sa.Boolean(), nullable=True, comment='状态(是否显示,是否激活)'),
    sa.Column('created_time', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_time', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.Column('name', sa.String(length=255), nullable=True, comment='用户账户'),
    sa.Column('nickname', sa.String(length=255), nullable=True, comment='用户昵称'),
    sa.Column('_password', sa.String(length=255), nullable=True, comment='登录密码'),
    sa.Column('age', sa.SmallInteger(), nullable=True, comment='年龄'),
    sa.Column('money', sa.Numeric(precision=7, scale=2), nullable=True, comment='账户余额'),
    sa.Column('ip_address', sa.String(length=255), nullable=True, comment='登录IP'),
    sa.Column('intro', sa.String(length=500), nullable=True, comment='个性签名'),
    sa.Column('avatar', sa.String(length=255), nullable=True, comment='头像url地址'),
    sa.Column('sex', sa.SmallInteger(), nullable=True, comment='性别'),
    sa.Column('email', sa.String(length=32), nullable=False, comment='邮箱地址'),
    sa.Column('mobile', sa.String(length=32), nullable=False, comment='手机号码'),
    sa.Column('unique_id', sa.String(length=255), nullable=True, comment='客户端唯一标记符'),
    sa.Column('province', sa.String(length=255), nullable=True, comment='省份'),
    sa.Column('city', sa.String(length=255), nullable=True, comment='城市'),
    sa.Column('area', sa.String(length=255), nullable=True, comment='地区'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mf_user_email'), 'mf_user', ['email'], unique=False)
    op.create_index(op.f('ix_mf_user_ip_address'), 'mf_user', ['ip_address'], unique=False)
    op.create_index(op.f('ix_mf_user_mobile'), 'mf_user', ['mobile'], unique=False)
    op.create_index(op.f('ix_mf_user_name'), 'mf_user', ['name'], unique=False)
    op.create_index(op.f('ix_mf_user_unique_id'), 'mf_user', ['unique_id'], unique=False)
    op.create_table('mf_user_profile',
    sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
    sa.Column('name', sa.String(length=255), nullable=True, comment='名称/标题'),
    sa.Column('is_deleted', sa.Boolean(), nullable=True, comment='逻辑删除'),
    sa.Column('orders', sa.Integer(), nullable=True, comment='排序'),
    sa.Column('status', sa.Boolean(), nullable=True, comment='状态(是否显示,是否激活)'),
    sa.Column('created_time', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_time', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
    sa.Column('education', sa.Integer(), nullable=True, comment='学历教育'),
    sa.Column('middle_school', sa.String(length=255), nullable=True, comment='初中/中专'),
    sa.Column('high_school', sa.String(length=255), nullable=True, comment='高中/高职'),
    sa.Column('college_school', sa.String(length=255), nullable=True, comment='大学/大专'),
    sa.Column('profession_cate', sa.String(length=255), nullable=True, comment='职业类型'),
    sa.Column('profession_info', sa.String(length=255), nullable=True, comment='职业名称'),
    sa.Column('position', sa.SmallInteger(), nullable=True, comment='职位/职称'),
    sa.Column('emotion_status', sa.SmallInteger(), nullable=True, comment='情感状态'),
    sa.Column('birthday', sa.DateTime(), nullable=True, comment='生日'),
    sa.Column('hometown_province', sa.String(length=255), nullable=True, comment='家乡省份'),
    sa.Column('hometown_city', sa.String(length=255), nullable=True, comment='家乡城市'),
    sa.Column('hometown_area', sa.String(length=255), nullable=True, comment='家乡地区'),
    sa.Column('hometown_address', sa.String(length=255), nullable=True, comment='家乡地址'),
    sa.Column('living_province', sa.String(length=255), nullable=True, comment='现居住省份'),
    sa.Column('living_city', sa.String(length=255), nullable=True, comment='现居住城市'),
    sa.Column('living_area', sa.String(length=255), nullable=True, comment='现居住地区'),
    sa.Column('living_address', sa.String(length=255), nullable=True, comment='现居住地址'),
    sa.ForeignKeyConstraint(['user_id'], ['mf_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('mf_user_profile')
    op.drop_index(op.f('ix_mf_user_unique_id'), table_name='mf_user')
    op.drop_index(op.f('ix_mf_user_name'), table_name='mf_user')
    op.drop_index(op.f('ix_mf_user_mobile'), table_name='mf_user')
    op.drop_index(op.f('ix_mf_user_ip_address'), table_name='mf_user')
    op.drop_index(op.f('ix_mf_user_email'), table_name='mf_user')
    op.drop_table('mf_user')
    # ### end Alembic commands ###
