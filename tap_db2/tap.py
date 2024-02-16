"""DB2 tap class."""

from __future__ import annotations

from singer_sdk import SQLTap
from singer_sdk import typing as th
from singer_sdk.helpers._classproperty import classproperty
from singer_sdk.helpers.capabilities import CapabilitiesEnum, PluginCapabilities, TapCapabilities

from tap_db2.stream import DB2Stream


class TapDB2(SQLTap):
    """`Tap-DB2` is a Singer tap for IBM DB2 data sources."""

    name = "tap-db2"
    package_name = "tap-ibm-db2"
    default_stream_class = DB2Stream

    config_jsonschema = th.PropertiesList(
        th.Property("host", th.HostnameType, required=True, default="localhost", description="The DB2 hostname."),
        th.Property("port", th.IntegerType, required=True, default=50000, description="The DB2 port."),
        th.Property("database", th.StringType, required=True, description="The DB2 database."),
        th.Property("schema", th.StringType, description="The DB2 schema."),
        th.Property("user", th.StringType, required=True, description="The DB2 username."),
        th.Property("password", th.StringType, required=True, secret=True, description="The DB2 password."),
        th.Property(
            "encryption",
            th.ObjectType(
                th.Property(
                    "ssl_server_certificate",
                    th.StringType(),
                    required=False,
                    description="The path to the SSL server certificate.",
                ),
                th.Property(
                    "ssl_client_key_store_db",
                    th.ObjectType(
                        th.Property(
                            "database",
                            th.StringType(),
                            required=True,
                            description="The full path to the client keystore database.",
                        ),
                        th.Property(
                            "password",
                            th.StringType(),
                            secret=True,
                            required=False,
                            description="The keystore password.",
                        ),
                        th.Property(
                            "key_stash",
                            th.StringType(),
                            required=False,
                            description="The full path to the client key stash.",
                        ),
                    ),
                ),
            ),
            required=False,
            description="Encryption settings for the DB2 connection. Setting this to an empty object will append 'SECURITY=SSL' to the connection string. For more information check out [python-ibmdb](https://github.com/ibmdb/python-ibmdb#example-of-ssl-connection-string).",
        ),
        th.Property(
            "connection_parameters",
            th.ObjectType(),
            required=False,
            description="Additional parameters to be appended to the connection string. This is an objects containing key-value pairs.",
        ),
        th.Property(
            "sqlalchemy_execution_options",
            th.ObjectType(),
            required=False,
            description="Additional execution options to be passed to SQLAlchemy. This is an objects containing key-value pairs.",
        ),
        th.Property(
            "query_partitioning",
            th.ObjectType(
                additional_properties=th.CustomType(
                    {
                        "type": ["object", "null"],
                        "properties": {
                            "primary_key": {"type": ["string"]},
                            "partition_size": {"type": ["integer"]},
                        },
                    }
                )
            ),
            required=False,
            description="Partition query into smaller subsets. Useful when working with DB2 that has set strict resource limits per query. Only works for streams with numeric primary keys.",
        ),
        th.Property(
            "filter",
            th.ObjectType(
                additional_properties=th.CustomType(
                    {
                        "type": ["object", "null"],
                        "properties": {
                            "where": {"type": ["string"]},
                        },
                    }
                )
            ),
            required=False,
            description="Apply a custom WHERE condition per stream. Unlike the filter available in stream_maps, this will be evaluated BEFORE extracting the data.",
        ),
        th.Property(
            "ignore_supplied_tables",
            th.BooleanType(),
            default=True,
            required=False,
            description="Ignore DB2-supplied user tables. For more info check out [Db2-supplied user tables](https://www.ibm.com/docs/en/db2-for-zos/12?topic=db2-supplied-user-tables).",
        ),
        th.Property(
            "ignore_views",
            th.BooleanType(),
            default=False,
            required=False,
            description="Ignore views.",
        ),
        th.Property(
            "stream_maps",
            th.ObjectType(
                additional_properties=th.CustomType(
                    {
                        "type": ["object", "string", "null"],
                        "properties": {
                            "__filter__": {"type": ["string", "null"]},
                            "__source__": {"type": ["string", "null"]},
                            "__alias__": {"type": ["string", "null"]},
                            "__else__": {
                                "type": ["string", "null"],
                                "enum": [None, "__NULL__"],
                            },
                            "__key_properties__": {
                                "type": ["array", "null"],
                                "items": {"type": "string"},
                            },
                        },
                        "additionalProperties": {"type": ["string", "null"]},
                    },
                ),
            ),
            required=False,
            description="Config object for stream maps capability. For more information check out [Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html).",
        ),
        th.Property(
            "stream_map_config",
            th.ObjectType(),
            required=False,
            description="User-defined config values to be used within map expressions.",
        ),
    ).to_dict()

    @classproperty
    def capabilities(self) -> list[CapabilitiesEnum]:
        """Get capabilities.

        Returns:
            A list of plugin capabilities.
        """
        return [
            PluginCapabilities.ABOUT,
            PluginCapabilities.STREAM_MAPS,
            TapCapabilities.CATALOG,
            TapCapabilities.STATE,
            TapCapabilities.DISCOVER,
        ]


if __name__ == "__main__":
    TapDB2.cli()  # pylint: disable=no-value-for-parameter
