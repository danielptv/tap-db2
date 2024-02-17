"""Test Configuration."""

import datetime

import sqlalchemy as sa
from faker import Faker

TEST_SQLALCHEMY_URL = "ibm_db_sa://db2inst1:password@localhost:50000/testdb;"

TABLE_NAME = "TEST_TABLE"


def pytest_sessionstart(session):
    """Fill database with data."""
    engine = sa.create_engine(TEST_SQLALCHEMY_URL)
    fake = Faker()

    date1 = datetime.date(2022, 11, 1)
    date2 = datetime.date(2022, 11, 30)
    metadata_obj = sa.MetaData()
    test_table = sa.Table(
        TABLE_NAME,
        metadata_obj,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(30)),
    )
    with engine.connect() as conn:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
        metadata_obj.create_all(conn)
        for _ in range(1000):
            insert = test_table.insert().values(
                updated_at=fake.date_between(date1, date2), name=fake.name()
            )
            conn.execute(insert)
        conn.commit()
