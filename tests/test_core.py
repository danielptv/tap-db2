"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from singer_sdk.testing import get_tap_test_class

from tap_db2.tap import TapDB2

TEST_CONFIG = {
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "host": "localhost",
    "port": "50000",
    "database": "testdb",
    "user": "db2inst1",
    "password": "password",
}


TestTapDB2 = get_tap_test_class(
    tap_class=TapDB2, config=TEST_CONFIG, catalog="tests/data/catalog.json", include_stream_tests=True
)
