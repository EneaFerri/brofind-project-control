"""Ora corrente in UTC.

SQLite non conserva il fuso orario: i timestamp sono salvati come UTC naive,
come in precedenza con datetime.utcnow() (deprecato da Python 3.12).
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
