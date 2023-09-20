"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from singer_sdk.testing import SuiteConfig, get_tap_test_class

from tap_db2.tap import TapDB2

TEST_CONFIG = {
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "host": "0.0.0.0",
    "port": "50000",
    "database": "testdb",
    "user": "db2inst1",
    "password": "password",
}

# TODO: No records found for stream 'DB2INST1-TEST_TABLE'
TEST_SUITE_CONFIG = SuiteConfig(ignore_no_records_for_streams=["DB2INST1-TEST_TABLE"])

# Run standard built-in tap tests from the SDK:
TestTapDB2 = get_tap_test_class(tap_class=TapDB2, config=TEST_CONFIG, suite_config=TEST_SUITE_CONFIG)
