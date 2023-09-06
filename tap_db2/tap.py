"""DB2 tap class."""

from __future__ import annotations

from singer_sdk import SQLTap
from singer_sdk import typing as th

from tap_db2.client import DB2Stream


class TapDB2(SQLTap):
    """`Tap-DB2` is a Singer tap for IBM DB2 data sources."""

    name = "tap-db2"
    default_stream_class = DB2Stream

    config_jsonschema = th.PropertiesList(
        th.Property(
            "host",
            th.HostnameType,
            required=True,
        ),
        th.Property(
            "port",
            th.StringType,
            required=True,
        ),
        th.Property(
            "database",
            th.StringType,
            required=True,
        ),
        th.Property(
            "schema",
            th.StringType,
        ),
        th.Property(
            "user",
            th.StringType,
            required=True,
        ),
        th.Property(
            "password",
            th.StringType,
            required=True,
            secret=True,
        ),
        th.Property(
            "encryption",
            th.ObjectType(
                th.Property(
                    "encryption_method",
                    th.StringType,
                    allowed_values=["none", "encrypted_verify_certificate"],
                    required=True,
                ),
                th.Property(
                    "ssl_server_certificate",
                    th.StringType,
                ),
            ),
        ),
        th.Property(
            "connection_parameters",
            th.ArrayType(
                th.ObjectType(
                    th.Property(
                        "key",
                        th.StringType,
                        required=True,
                    ),
                    th.Property(
                        "value",
                        th.StringType,
                        required=True,
                    ),
                )
            ),
            required=False,
        ),
        th.Property(
            "stream_maps",
            th.ObjectType(),
        ),
        th.Property(
            "stream_map_config",
            th.ObjectType(),
        ),
    ).to_dict()


if __name__ == "__main__":
    TapDB2.cli()
