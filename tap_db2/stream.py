"""DB2 stream class."""

from __future__ import annotations

import typing as t
from datetime import datetime

import ibm_db_sa  # type: ignore
import sqlalchemy as sa
from singer_sdk import SQLStream
from singer_sdk.helpers._state import STARTING_MARKER

from tap_db2.connector import DB2Connector

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context


class DB2Stream(SQLStream):
    """Stream class for IBM DB2 streams."""

    connector_class = DB2Connector

    def get_starting_replication_key_value(
        self,
        context: Context | None,
    ) -> t.Any | None:
        """Get starting replication key.

        Args:
            context: Stream partition or context dictionary.

        Returns:
            Starting replication value.
        """
        state = self.get_context_state(context)

        if not state or not (timestamp_str := state.get(STARTING_MARKER)):
            return None
        # Format timestamp to precision supported by DB2 queries
        timestamp = datetime.fromisoformat(str(timestamp_str))
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Get records from stream
    def get_records(self, context: Context | None) -> t.Iterable[dict[str, t.Any]]:
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

        partition_key, partition_size = self._get_partition_config()

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
                if partition_key is None
                else query.order_by(table.columns[partition_key])
            )
            start_val = self.get_starting_replication_key_value(context)
            if start_val:
                query = query.where(replication_key_col >= start_val)

        if self.ABORT_AT_RECORD_COUNT is not None:
            query = query.limit(self.ABORT_AT_RECORD_COUNT + 1)

        query = self._apply_filter_config(query)

        with self.connector._connect() as conn:
            if partition_key is None:
                for record in conn.execute(query):
                    transformed_record = self.post_process(dict(record._mapping))
                    if transformed_record is None:
                        # Record filtered out during post_process()
                        continue
                    yield transformed_record

            else:
                return self._get_partitioned_records(query, table, conn)

    def _get_partition_config(self) -> tuple[str | None, int | None]:
        partitioning_configs = self.config.get("query_partition", {})
        partition_config = partitioning_configs.get(
            self.tap_stream_id
        ) or partitioning_configs.get("*")

        if partition_config:
            partition_key = partition_config.get("partition_key")
            partition_size = partition_config.get("partition_size")
        else:
            partition_key, partition_size = None, None

        return partition_key, partition_size

    def _apply_filter_config(self, query: sa.sql.select) -> sa.sql.select:
        filter_configs = self.config.get("filter", {})
        if self.tap_stream_id in filter_configs:
            query = query.where(sa.text(filter_configs[self.tap_stream_id]["where"]))
        elif "*" in filter_configs:
            query = query.where(sa.text(filter_configs["*"]["where"]))
        return query

    def _get_partitioned_records(
        self, query: sa.sql.select, table: sa.Table, conn: sa.engine.Connection
    ) -> t.Iterable[dict[str, t.Any]]:
        partition_key, partition_size = self._get_partition_config()
        lower_limit = None

        termination_query = sa.select(sa.func.count(table.columns[partition_key]))
        if query.whereclause is not None:
            termination_query = termination_query.where(query.whereclause)
        termination_query_result = conn.execute(termination_query).first()
        assert termination_query_result is not None, "Invalid termination query"
        termination_limit = int(str(termination_query_result[0]))
        fetched_count = 0

        while fetched_count < termination_limit:
            limited_query = query.limit(partition_size)
            if lower_limit is not None:
                limited_query = limited_query.where(
                    table.columns[partition_key] > lower_limit
                )
            for record in conn.execute(limited_query):
                transformed_record = self.post_process(dict(record._mapping))

                if transformed_record is None:
                    # Record filtered out during post_process()
                    continue
                lower_limit = transformed_record[partition_key]
                fetched_count += 1
                yield transformed_record

    @property
    def is_sorted(self) -> bool:
        """Expect stream to be sorted.

        When `True`, incremental streams will attempt to resume if unexpectedly
        interrupted.

        Returns:
            `True` if stream is sorted. Defaults to `False`.
        """
        partition_key, _ = self._get_partition_config()
        return self.replication_method == "INCREMENTAL" and partition_key is None


class ROWID(sa.sql.sqltypes.String):
    """Custom SQL type for 'ROWID'."""

    __visit_name__ = "ROWID"


class VARG(sa.sql.sqltypes.String):
    """Custom SQL type for 'VARG'."""

    __visit_name__ = "VARG"


ibm_db_sa.base.ischema_names["ROWID"] = ROWID
ibm_db_sa.base.ischema_names["VARG"] = ROWID
