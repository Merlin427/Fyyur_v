"""empty message

Revision ID: 8ae2a79171ff
Revises: e9aa0f202696
Create Date: 2020-07-20 17:42:20.892643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ae2a79171ff'
down_revision = 'e9aa0f202696'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('show_venue_id_fkey', 'show', type_='foreignkey')
    op.drop_constraint('show_artist_id_fkey', 'show', type_='foreignkey')
    op.create_foreign_key(None, 'show', 'venue', ['venue_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'show', 'artist', ['artist_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'show', type_='foreignkey')
    op.drop_constraint(None, 'show', type_='foreignkey')
    op.create_foreign_key('show_artist_id_fkey', 'show', 'artist', ['artist_id'], ['id'])
    op.create_foreign_key('show_venue_id_fkey', 'show', 'venue', ['venue_id'], ['id'])
    # ### end Alembic commands ###