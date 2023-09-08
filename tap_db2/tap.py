"""DB2 tap class."""

from __future__ import annotations
from singer_sdk import PluginBase, SQLTap
from singer_sdk import typing as th, about
from singer_sdk.helpers.capabilities import PluginCapabilities, CapabilitiesEnum
from singer_sdk.helpers import _classproperty

from tap_db2.client import DB2Stream


class TapDB2(SQLTap):
    """`Tap-DB2` is a Singer tap for IBM DB2 data sources."""

    name = "tap-db2"
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
            th.ArrayType(
                th.ObjectType(
                    th.Property("key", th.StringType, required=True, description="The parameter key."),
                    th.Property("value", th.StringType, required=True, description="The parameter value."),
                )
            ),
            required=False,
            description="Additional parameters to be appended to the connection string. This is an array of objects. Each object must contain the keys 'key' and 'value'.",
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

    @classmethod
    def _get_about_info(cls: type[PluginBase]) -> about.AboutInfo:
        """Returns capabilities and other tap metadata.

        Returns:
            A dictionary containing the relevant 'about' information.
        """
        return about.AboutInfo(
            name=cls.name,
            description=cls.__doc__,
            version=cls.get_plugin_version(),
            sdk_version=cls.get_sdk_version(),
            supported_python_versions=cls.get_supported_python_versions(),
            capabilities=cls.capabilities,
            settings=cls.config_jsonschema,
        )

    @_classproperty.classproperty
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
