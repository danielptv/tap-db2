"""DB2 stream class."""

from __future__ import annotations

import typing as t
from datetime import datetime

import ibm_db_sa
import sqlalchemy  # noqa: TCH002
from singer_sdk import SQLStream
from singer_sdk.connectors import SQLConnector
from singer_sdk.helpers._state import STARTING_MARKER
from singer_sdk.tap_base import Tap
from sqlalchemy import func, select

from tap_db2.connector import DB2Connector


class DB2Stream(SQLStream):
    """Stream class for IBM DB2 streams."""

    connector_class = DB2Connector

    def __init__(self, tap: Tap, catalog_entry: dict, connector: SQLConnector | None = None) -> None:
        super().__init__(tap, catalog_entry, connector)
        self.query_partitioning_pk = None
        self.query_partitioning_size = None
        self._is_sorted = super().is_sorted

        partitioning_configs = self.config.get("query_partitioning", {})
        if self.tap_stream_id in partitioning_configs:
            self.query_partitioning_pk = partitioning_configs[self.tap_stream_id]["primary_key"]
            self.query_partitioning_size = partitioning_configs[self.tap_stream_id]["partition_size"]
        elif "*" in partitioning_configs:
            self.query_partitioning_pk = partitioning_configs["*"]["primary_key"]
            self.query_partitioning_size = partitioning_configs["*"]["partition_size"]

        if self.replication_key and self.query_partitioning_pk and self.replication_key != self.query_partitioning_pk:
            self.is_sorted = False

    @property
    def is_sorted(self):
        return self._is_sorted

    @is_sorted.setter
    def is_sorted(self, value):
        self._is_sorted = value

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

    # Get records from stream
    def get_records(self, context: dict | None) -> t.Iterable[dict[str, t.Any]]:
        """Return a generator of record-type dictionary objects.

        If the stream has a replication_key value defined, records will be sorted by the
        incremental key. If the stream also has an available starting bookmark, the
        records will be filtered for values greater than or equal to the bookmark value.

        Args:
            context: If partition context is provided, will read specifically from this
                data slice.

        Yields:
            One dict per record.

        Raises:
            NotImplementedError: If partition is passed in context and the stream does
                not support partitioning.
        """
        if context:
            msg = f"Stream '{self.name}' does not support partitioning."
            raise NotImplementedError(msg)

        selected_column_names = self.get_selected_schema()["properties"].keys()
        table = self.connector.get_table(
            full_table_name=self.fully_qualified_name,
            column_names=selected_column_names,
        )
        query = table.select()
        if self.replication_key:
            replication_key_col = table.columns[self.replication_key]
            query = (
                query.order_by(replication_key_col)
                if self.query_partitioning_pk is None
                else query.order_by(table.columns[self.query_partitioning_pk])
            )
            start_val = self.get_starting_replication_key_value(context)
            if start_val:
                query = query.where(replication_key_col >= start_val)

        if self.ABORT_AT_RECORD_COUNT is not None:
            query = query.limit(self.ABORT_AT_RECORD_COUNT + 1)

        with self.connector._connect() as conn:
            if self.query_partitioning_pk is None:
                for record in conn.execute(query):
                    transformed_record = self.post_process(dict(record._mapping))
                    if transformed_record is None:
                        # Record filtered out during post_process()
                        continue
                    yield transformed_record

            else:
                limit = self.query_partitioning_size
                primary_key = self.query_partitioning_pk
                lower_limit = None

                termination_query = select(func.count(table.columns[primary_key]))  # pylint: disable=not-callable
                if self.replication_key and start_val:
                    termination_query = termination_query.where(replication_key_col >= start_val)
                termination_limit = conn.execute(termination_query).first()[0]
                fetched_count = 0

                while fetched_count < termination_limit:
                    limited_query = query.limit(limit)
                    if lower_limit is not None:
                        limited_query = limited_query.where(table.columns[primary_key] > lower_limit)

                    for record in conn.execute(limited_query):
                        transformed_record = self.post_process(dict(record._mapping))
                        if transformed_record is None:
                            # Record filtered out during post_process()
                            continue
                        lower_limit = transformed_record[primary_key]
                        fetched_count += 1
                        yield transformed_record


class ROWID(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'ROWID'"""

    __visit_name__ = "ROWID"


class VARG(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'VARG'"""

    __visit_name__ = "VARG"


ibm_db_sa.base.ischema_names["ROWID"] = ROWID
ibm_db_sa.base.ischema_names["VARG"] = ROWID
