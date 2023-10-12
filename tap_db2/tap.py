"""DB2 tap class."""

from __future__ import annotations

from singer_sdk import SQLTap
from singer_sdk import typing as th
from singer_sdk.helpers._classproperty import classproperty
from singer_sdk.helpers.capabilities import CapabilitiesEnum, PluginCapabilities

from tap_db2.stream import DB2Stream


class TapDB2(SQLTap):
    """`Tap-DB2` is a Singer tap for IBM DB2 data sources."""

    name = "tap-db2"
    package_name = "tap-ibm-db2"
    default_stream_class = DB2Stream

    config_jsonschema = th.PropertiesList(
        th.Property("host", th.HostnameType, required=True, description="The DB2 hostname."),
        th.Property("port", th.StringType, required=True, description="The DB2 port."),
        th.Property("database", th.StringType, required=True, description="The DB2 database."),
        th.Property("schema", th.StringType, description="The DB2 schema."),
        th.Property("user", th.StringType, required=True, description="The DB2 username."),
        th.Property("password", th.StringType, required=True, secret=True, description="The DB2 password."),
        th.Property(
            "encryption",
            th.ObjectType(
                th.Property(
                    "encryption_method",
                    th.StringType,
                    allowed_values=["none", "encrypted_verify_certificate"],
                    required=True,
                    description="The encryption method. Valid values are 'encrypted_verify_certificate' and 'none'.",
                ),
                th.Property(
                    "ssl_server_certificate", th.StringType, description="The path to the SSL server certificate."
                ),
            ),
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
            description="Partition query into smaller subsets. Useful when working with DB2 that has set strict resource limits per query.",
        ),
        th.Property(
            "ignore_supplied_tables",
            th.BooleanType(),
            default=True,
            required=False,
            description="Ignore DB2-supplied user tables. For more info check out [Db2-supplied user tables](https://www.ibm.com/docs/en/db2-for-zos/12?topic=db2-supplied-user-tables).",
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
            PluginCapabilities.STREAM_MAPS,
        ]


if __name__ == "__main__":
    TapDB2.cli()  # pylint: disable=no-value-for-parameter
