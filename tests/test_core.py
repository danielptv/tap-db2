"""Tests standard tap features using the built-in SDK tests library."""

import datetime

import pytest
import sqlalchemy
from faker import Faker
from singer_sdk.testing import SuiteConfig, get_tap_test_class
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, text

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

TEST_SQLALCHEMY_URL = "ibm_db_sa://db2inst1:password@localhost:50000/testdb;"

TABLE_NAME = "TEST_TABLE"


def setup_test_table(table_name, sqlalchemy_url):
    """setup any state specific to the execution of the given module."""
    engine = sqlalchemy.create_engine(sqlalchemy_url)
    fake = Faker()

    date1 = datetime.date(2022, 11, 1)
    date2 = datetime.date(2022, 11, 30)
    metadata_obj = MetaData()
    test_table = Table(
        table_name,
        metadata_obj,
        Column("id", Integer, primary_key=True),
        Column("updated_at", DateTime(), nullable=False),
        Column("name", String(30)),
    )
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        metadata_obj.create_all(conn)
        for _ in range(1000):
            insert = test_table.insert().values(updated_at=fake.date_between(date1, date2), name=fake.name())
            conn.execute(insert)
        conn.commit()


# Run standard built-in tap tests from the SDK:
TapDB2Test = get_tap_test_class(tap_class=TapDB2, config=TEST_CONFIG, suite_config=TEST_SUITE_CONFIG)


class TestTapDB2(TapDB2Test):
    table_name = TABLE_NAME
    sqlalchemy_url = TEST_SQLALCHEMY_URL

    @pytest.fixture(scope="class")
    def resource(self):
        setup_test_table(self.table_name, self.sqlalchemy_url)
        # yield
