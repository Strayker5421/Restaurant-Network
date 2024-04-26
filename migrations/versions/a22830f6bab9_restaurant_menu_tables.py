"""restaurant, menu tables

Revision ID: a22830f6bab9
Revises: fc604464f87f
Create Date: 2024-04-26 19:38:34.492151

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a22830f6bab9'
down_revision = 'fc604464f87f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('restaurant',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('image_path', sa.Text(), nullable=True),
    sa.Column('status', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('menu',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dish_name', sa.String(length=255), nullable=False),
    sa.Column('image_path', sa.Text(), nullable=True),
    sa.Column('status', sa.Boolean(), nullable=True),
    sa.Column('restaurant_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dish_name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('menu')
    op.drop_table('restaurant')
    # ### end Alembic commands ###
