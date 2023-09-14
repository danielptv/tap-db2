"""DB2 stream class."""

from __future__ import annotations
from datetime import datetime

import typing as t

import ibm_db_sa

import sqlalchemy  # noqa: TCH002
from singer_sdk import SQLStream
from singer_sdk.helpers._state import STARTING_MARKER

from tap_db2.connector import DB2Connector


class DB2Stream(SQLStream):
    """Stream class for IBM DB2 streams."""

    connector_class = DB2Connector

    def get_starting_replication_key_value(
        self,
        context: dict | None,
    ) -> t.Any | None:  # noqa: ANN401
        """Get starting replication key.

        Args:
            context: Stream partition or context dictionary.

        Returns:
            Starting replication value.
        """
        state = self.get_context_state(context)

        if not state or not state.get(STARTING_MARKER):
            return None
        # Format timestamp to precision supported by DB2 queries
        timestamp = datetime.fromisoformat(state.get(STARTING_MARKER))
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")


class ROWID(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'ROWID'"""

    __visit_name__ = "ROWID"


class VARG(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'VARG'"""

    __visit_name__ = "VARG"


ibm_db_sa.base.ischema_names["ROWID"] = ROWID
ibm_db_sa.base.ischema_names["VARG"] = ROWID
