"""isochrone cache table (PostGIS optional)

Revision ID: 001
Revises:
Create Date: 2026-06-20

Stores GeoJSON polygon geometries as JSONB. PostGIS extension enabled for future
ST_DWithin stop queries; geometry column uses JSONB to avoid WKB serialization
in the API cache layer.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS isochrone_cache (
            cache_key VARCHAR(64) PRIMARY KEY,
            prefix VARCHAR(32) NOT NULL,
            geometry JSONB NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_isochrone_cache_expires ON isochrone_cache (expires_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS isochrone_cache")
