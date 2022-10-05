"""add lon table and populate lat,lon

Revision ID: b0e573a9ca60
Revises: 242da1c9b127
Create Date: 2022-10-05 14:03:01.645481

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from modules.database.db import SatImage


# revision identifiers, used by Alembic.
revision = 'b0e573a9ca60'
down_revision = '242da1c9b127'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('sat_images', 'lat')



def downgrade() -> None:
    pass
