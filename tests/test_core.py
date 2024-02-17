"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from singer_sdk.testing import get_tap_test_class

from tap_db2.tap import TapDB2

TEST_CONFIG = {
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "host": "localhost",
    "port": 50000,
    "database": "testdb",
    "user": "db2inst1",
    "password": "password",
}

TEST_CONFIG_QUERY_PARTITIONING = {
    **TEST_CONFIG,
    "query_partitioning": {
        "db2inst1-test_table": {"primary_key": "id", "partition_size": 5}
    },
}

TestTapDB2 = get_tap_test_class(
    tap_class=TapDB2, config=TEST_CONFIG, catalog="tests/data/catalog.json"
)
TestTapDB2WithQueryPartitioning = get_tap_test_class(
    tap_class=TapDB2,
    config=TEST_CONFIG_QUERY_PARTITIONING,
    catalog="tests/data/catalog.json",
)
