"""Test Configuration."""
import datetime

import sqlalchemy
from faker import Faker
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, text

pytest_plugins = ("singer_sdk.testing.pytest_plugin",)

TEST_SQLALCHEMY_URL = "ibm_db_sa://db2inst1:password@localhost:50000/testdb;"

TABLE_NAME = "TEST_TABLE"


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    engine = sqlalchemy.create_engine(TEST_SQLALCHEMY_URL)
    fake = Faker()

    date1 = datetime.date(2022, 11, 1)
    date2 = datetime.date(2022, 11, 30)
    metadata_obj = MetaData()
    test_table = Table(
        TABLE_NAME,
        metadata_obj,
        Column("id", Integer, primary_key=True),
        Column("updated_at", DateTime(), nullable=False),
        Column("name", String(30)),
    )
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
        metadata_obj.create_all(conn)
        for _ in range(1000):
            insert = test_table.insert().values(updated_at=fake.date_between(date1, date2), name=fake.name())
            conn.execute(insert)
        conn.commit()
