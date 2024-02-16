"""DB2 connector class."""

from __future__ import annotations

import re
import typing as t

import sqlalchemy  # noqa: TCH002
from singer_sdk import SQLConnector
from singer_sdk import typing as th
from sqlalchemy.engine import Engine

SUPPLIED_USER_TABLES_PATTERN = r"^(DSN_|PLAN_TABLE)"


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
            f":{str(config['port'])}/"
            f"{config['database']};"
        )
        if "encryption" in config:
            connection_url += "SECURITY=SSL;"
            if "ssl_server_certificate" in config["encryption"]:
                connection_url += f"SSLServerCertificate={config['encryption']['ssl_server_certificate']};"
            if "ssl_client_key_store_db" in config["encryption"]:
                connection_url += f"SSLClientKeyStoreDB={config['encryption']['ssl_client_key_store_db']['database']};"
                if "password" in config["encryption"]["ssl_client_key_store_db"]:
                    connection_url += (
                        f"SSLClientKeyStoreDBPassword={config['encryption']['ssl_client_key_store_db']['password']};"
                    )
                if "key_stash" in config["encryption"]["ssl_client_key_store_db"]:
                    connection_url += (
                        f"SSLClientKeyStash={config['encryption']['ssl_client_key_store_db']['key_stash']};"
                    )
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
        sql_type: str | sqlalchemy.types.TypeEngine | type[sqlalchemy.types.TypeEngine] | t.Any,  # noqa: ANN401
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
                if is_view and "ignore_views" in self.config and self.config["ignore_views"]:
                    continue
                if not re.match(SUPPLIED_USER_TABLES_PATTERN, table_name, re.IGNORECASE) or (
                    "ignore_supplied_tables" in self.config and not self.config["ignore_supplied_tables"]
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
