"""SQL client handling.

This includes db2Stream and db2Connector.
"""

from __future__ import annotations

import typing as t

import ibm_db_sa

import sqlalchemy  # noqa: TCH002
from singer_sdk import SQLConnector, SQLStream, typing as th
from singer_sdk._singerlib import CatalogEntry, Schema, MetadataMapping
from sqlalchemy.engine import Engine


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
            for param in config["connection_parameters"]:
                connection_url += f"{param['key']}={param['value']};"
        return connection_url

    def create_engine(self) -> Engine:
        return sqlalchemy.create_engine(
            self.sqlalchemy_url
            # echo=False,
            # json_serializer=self.serialize_json,
            # json_deserializer=self.deserialize_json,
        )

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

    def discover_catalog_entry(
        self,
        engine: Engine,  # noqa: ARG002
        inspected: sqlalchemy.Inspector,
        schema_name: str,
        table_name: str,
        is_view: bool,  # noqa: FBT001
    ) -> CatalogEntry:
        """Create `CatalogEntry` object for the given table or a view.

        Args:
            engine: SQLAlchemy engine
            inspected: SQLAlchemy inspector instance for engine
            schema_name: Schema name to inspect
            table_name: Name of the table or a view
            is_view: Flag whether this object is a view, returned by `get_object_names`

        Returns:
            `CatalogEntry` object for the given table or a view
        """
        # Initialize unique stream name
        if "schema" in self.config:
            unique_stream_id = table_name.strip().upper()
        else:
            unique_stream_id = self.get_fully_qualified_name(
                db_name=None,
                schema_name=schema_name.strip().upper(),
                table_name=table_name.strip().upper(),
                delimiter="-",
            )

        # Detect key properties
        possible_primary_keys: list[list[str]] = []
        pk_def = inspected.get_pk_constraint(table_name, schema=schema_name)
        if pk_def and "constrained_columns" in pk_def:
            possible_primary_keys.append(pk_def["constrained_columns"])

        possible_primary_keys.extend(
            index_def["column_names"]
            for index_def in inspected.get_indexes(table_name, schema=schema_name)
            if index_def.get("unique", False)
        )

        key_properties = next(iter(possible_primary_keys), None)

        # Initialize columns list
        table_schema = th.PropertiesList()
        for column_def in inspected.get_columns(table_name, schema=schema_name):
            column_name = column_def["name"]
            is_nullable = column_def.get("nullable", False)
            jsonschema_type: dict = self.to_jsonschema_type(
                t.cast(sqlalchemy.types.TypeEngine, column_def["type"]),
            )
            table_schema.append(
                th.Property(
                    name=column_name,
                    wrapped=th.CustomType(jsonschema_type),
                    required=not is_nullable,
                ),
            )
        schema = table_schema.to_dict()

        # Initialize available replication methods
        addl_replication_methods: list[str] = [""]  # By default an empty list.
        replication_method = next(reversed(["FULL_TABLE", *addl_replication_methods]))

        # Create the catalog entry object
        return CatalogEntry(
            tap_stream_id=unique_stream_id,
            stream=unique_stream_id,
            table=table_name.upper(),
            key_properties=key_properties,
            schema=Schema.from_dict(schema),
            is_view=is_view,
            replication_method=replication_method,
            metadata=MetadataMapping.get_standard_metadata(
                schema_name=schema_name,
                schema=schema,
                replication_method=replication_method,
                key_properties=key_properties,
                valid_replication_keys=None,  # Must be defined by user
            ),
            database=None,  # Expects single-database context
            row_count=None,
            stream_alias=None,
            replication_key=None,  # Must be defined by user
        )


class DB2Stream(SQLStream):
    """Stream class for IBM DB2 streams."""

    connector_class = DB2Connector


class ROWID(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'ROWID'"""

    __visit_name__ = "ROWID"


class VARG(sqlalchemy.sql.sqltypes.String):
    """Custom SQL type for 'VARG'"""

    __visit_name__ = "VARG"


ibm_db_sa.base.ischema_names["ROWID"] = ROWID
ibm_db_sa.base.ischema_names["VARG"] = ROWID
