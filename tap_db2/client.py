"""SQL client handling.

This includes db2Stream and db2Connector.
"""

from __future__ import annotations
from datetime import datetime

import typing as t

import ibm_db_sa

import sqlalchemy  # noqa: TCH002
from sqlalchemy.engine import Engine
from singer_sdk import SQLConnector, SQLStream, typing as th
from singer_sdk.helpers._state import STARTING_MARKER


class DB2Connector(SQLConnector):
    """Connects to the IBM DB2 SQL source."""

    def get_sqlalchemy_url(self, config: dict) -> str:
        """Concatenate a SQLAlchemy URL for use in connecting to the source.

        Args:
            config: A dict with connection parameters

        Returns:
            SQLAlchemy connection string
        """
        connection_url = (
            f"ibm_db_sa://{config['user']}:"
            f"{config['password']}@{config['host']}"
            f":{config['port']}/"
            f"{config['database']};"
        )
        if (
            "encryption" in config
            and "encryption_method" in config["encryption"]
            and config["encryption"]["encryption_method"] != "none"
        ):
            connection_url += "SECURITY=SSL;"
            if "ssl_server_certificate" in config["encryption"]:
                connection_url += f"SSLServerCertificate={config['encryption']['ssl_server_certificate']};"
        if "connection_parameters" in config:
            for key, value in config["connection_parameters"].items():
                connection_url += f"{key}={value};"
        return connection_url

    def create_engine(self) -> Engine:
        if "sqlalchemy_execution_options" in self.config:
            sqlalchemy_connection_kwargs = {"execution_options": self.config["sqlalchemy_execution_options"]}
            return sqlalchemy.create_engine(self.sqlalchemy_url, **sqlalchemy_connection_kwargs)
        return sqlalchemy.create_engine(self.sqlalchemy_url)

    @staticmethod
    def to_jsonschema_type(
        sql_type: (str | sqlalchemy.types.TypeEngine | type[sqlalchemy.types.TypeEngine] | t.Any),  # noqa: ANN401
    ) -> dict:
        """Return a JSON Schema representation of the provided type.

        Raises:
            ValueError: If the type received could not be translated to jsonschema.

        Returns:
            The JSON Schema representation of the provided type.
        """
        # Map DATE to date-time in JSON Schema
        if isinstance(sql_type, sqlalchemy.DATE):
            return th.DateTimeType.type_dict

        return SQLConnector.to_jsonschema_type(sql_type)

    def discover_catalog_entries(self) -> list[dict]:
        """Return a list of catalog entries from discovery.

        Returns:
            The discovered catalog entries as a list.
        """
        result: list[dict] = []
        engine = self._engine
        inspected = sqlalchemy.inspect(engine)
        for schema_name in self.get_schema_names(engine, inspected):
            # Iterate through each table and view
            for table_name, is_view in self.get_object_names(
                engine,
                inspected,
                schema_name,
            ):
                # Filter by schema
                # Connection parameter 'CURRENTSCHEMA=mySchema;' doesn't work
                # https://www.ibm.com/support/pages/525-error-nullidsysstat-package-when-trying-set-current-schema-against-db2-zos-database
                target_schema = self.config["schema"] if "schema" in self.config else None
                if target_schema is None or target_schema.strip().lower() == schema_name.strip().lower():
                    catalog_entry = self.discover_catalog_entry(
                        engine,
                        inspected,
                        schema_name,
                        table_name,
                        is_view,
                    )
                    result.append(catalog_entry.to_dict())

        return result

    @staticmethod
    def get_fully_qualified_name(
        table_name: str | None = None,
        schema_name: str | None = None,
        db_name: str | None = None,
        delimiter: str = ".",
    ) -> str:
        """Concatenates a fully qualified name from the parts.

        Args:
            table_name: The name of the table.
            schema_name: The name of the schema. Defaults to None.
            db_name: The name of the database. Defaults to None.
            delimiter: Generally: '.' for SQL names and '-' for Singer names.

        Raises:
            ValueError: If all 3 name parts not supplied.

        Returns:
            The fully qualified name as a string.
        """
        return SQLConnector.get_fully_qualified_name(
            table_name=table_name.strip().upper(),
            schema_name=schema_name.strip().upper(),
            db_name=None,
            delimiter=".",
        )


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

        if not state:
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
