import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.numbering import next_number

URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(not URL, reason="needs PostgreSQL (TEST_DATABASE_URL): row locks do not exist in SQLite")
def test_first_numbers_of_a_series_are_unique_under_parallel_requests():
    """Eight people save their first document of a new series at the same moment: nobody gets an error or a duplicate."""
    eng = create_engine(URL)
    Session = sessionmaker(eng)
    prefix = "CC" + os.urandom(2).hex()[:2].upper()

    def one(_):
        with Session() as s:
            n = next_number(s, prefix)
            s.commit()
            return n

    with ThreadPoolExecutor(8) as ex:
        got = list(ex.map(one, range(8)))
    assert sorted(got) == [f"{prefix}-{i:06d}" for i in range(1, 9)]
