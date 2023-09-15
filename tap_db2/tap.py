"""DB2 tap class."""

from __future__ import annotations
from singer_sdk import SQLTap
from singer_sdk import typing as th
from singer_sdk.helpers.capabilities import PluginCapabilities, CapabilitiesEnum
from singer_sdk.helpers._classproperty import classproperty

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
            th.ArrayType(
                th.ObjectType(
                    th.Property("stream", th.StringType(), required=True, description="The stream name."),
                    th.Property("key", th.StringType(), required=True, description="The column name."),
                    th.Property(
                        "partition_by_date",
                        th.ObjectType(
                            th.Property("days", th.IntegerType(), required=True, description="The number of days."),
                            th.Property("months", th.IntegerType(), required=True, description="The number of years."),
                            th.Property("years", th.IntegerType(), required=True, description="The number of years."),
                        ),
                        required=False,
                        description="Partitioning using a column of type 'datetime'. The partition size can be defined by the number of days, months and years.",
                    ),
                    th.Property(
                        "partition_by_number",
                        th.ObjectType(th.Property("partition_size", th.IntegerType(), required=True, description="The partition size.")),
                        required=False,
                        description="Partitioning using a column of type 'number'. The partition size can be defined by setting partition_size.",
                    ),
                ),
            ),
            required=False,
            description="Partition query into smaller subsets. Useful when working with DB2 that has set strict resource limits per query. Partitioning is supported for columns of type 'number' and 'datetime'. Note: The currently supported methods do not guarantee a constant partition size.",
        ),
        th.Property(
            "stream_maps",
            th.ObjectType(),
            description="Config object for stream maps capability. For more information check out [Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html).",
        ),
        th.Property(
            "stream_map_config",
            th.ObjectType(),
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
    TapDB2.cli()
