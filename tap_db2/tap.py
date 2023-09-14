"""DB2 tap class."""

from __future__ import annotations
from singer_sdk import SQLTap
from singer_sdk import typing as th
from singer_sdk.helpers.capabilities import PluginCapabilities, CapabilitiesEnum
from singer_sdk.helpers._classproperty import classproperty

from tap_db2.connector import DB2Stream


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
