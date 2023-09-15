"""DB2 stream class."""

from __future__ import annotations
from datetime import datetime

import typing as t

import ibm_db_sa

import sqlalchemy  # noqa: TCH002
from singer_sdk import SQLStream
from singer_sdk.helpers._state import STARTING_MARKER
from dateutil.relativedelta import relativedelta

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
            query = query.order_by(replication_key_col)
            start_val = self.get_starting_replication_key_value(context)
            if start_val:
                query = query.where(replication_key_col >= start_val)

        if self.ABORT_AT_RECORD_COUNT is not None:
            query = query.limit(self.ABORT_AT_RECORD_COUNT + 1)

        execute_generator = True
        with self.connector._connect() as conn:
            if "query_partitioning" in self.config:
                partition_config = None
                for stream in self.config["query_partitioning"]:
                    if stream["stream"] == self.tap_stream_id:
                        partition_config = stream
                        break
                    elif stream["stream"] == "*":
                        partition_config = stream

                if partition_config is not None:
                    execute_generator = False
                    start_val_limit = "" if not self.replication_key or not start_val else f"where {replication_key_col} >= {start_val}"
                    lower_limit = conn.exec_driver_sql(
                        f"SELECT MIN({partition_config['key']}) FROM {self.fully_qualified_name} {start_val_limit};"
                    ).first()[0]

                    if "partition_by_date" in partition_config:
                        partition_by_date = partition_config["partition_by_date"]
                        delta = relativedelta(
                            days=partition_by_date["days"],
                            months=partition_by_date["months"],
                            years=partition_by_date["years"],
                        )
                        termination_limit = datetime.now()
                    else:
                        delta = partition_config["partition_by_number"]["partition_size"]
                        termination_limit = conn.exec_driver_sql(
                            f"SELECT MAX({partition_config['key']}) FROM {self.fully_qualified_name} {start_val_limit};"
                        ).first()[0]
                    upper_limit = lower_limit + delta

                    while upper_limit < termination_limit:
                        limited_query = query.where(table.columns[partition_config["key"]] >= lower_limit).where(
                            table.columns[partition_config["key"]] < upper_limit
                        )
                        for record in conn.execute(limited_query):
                            transformed_record = self.post_process(dict(record._mapping))
                            if transformed_record is None:
                                # Record filtered out during post_process()
                                continue
                            yield transformed_record
                        lower_limit = upper_limit
                        upper_limit = upper_limit + delta

            if execute_generator is True:
                for record in conn.execute(query):
                    transformed_record = self.post_process(dict(record._mapping))
                    if transformed_record is None:
                        # Record filtered out during post_process()
                        continue
                    yield transformed_record


class ROWID(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'ROWID'"""

    __visit_name__ = "ROWID"


class VARG(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'VARG'"""

    __visit_name__ = "VARG"


ibm_db_sa.base.ischema_names["ROWID"] = ROWID
ibm_db_sa.base.ischema_names["VARG"] = ROWID
