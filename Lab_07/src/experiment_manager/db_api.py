"""Raw Python DB-API (sqlite3) module with parameterized queries and transactions."""

import sqlite3
from typing import Any


def db_api_search_by_researcher(conn: sqlite3.Connection, researcher_name: str) -> list[dict[str, Any]]:
    """Parameterized query searching experiments by researcher name using SQL JOIN."""
    query = """
        SELECT e.id, e.title, r.name AS researcher, r.department, e.parameter, e.result, e.date, e.notes
        FROM experiments e
        JOIN researchers r ON e.researcher_id = r.id
        WHERE r.name = ?
        ORDER BY e.date ASC;
    """
    cursor = conn.cursor()
    cursor.execute(query, (researcher_name.strip(),))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def db_api_search_by_range(
    conn: sqlite3.Connection,
    min_val: float,
    max_val: float,
    parameter: str | None = None,
    order_by_date: bool = True,
) -> list[dict[str, Any]]:
    """Parameterized query filtering experiments within numerical range."""
    params: list[Any] = [float(min_val), float(max_val)]
    query = """
        SELECT e.id, e.title, e.parameter, e.result, e.date, e.notes, e.researcher_id
        FROM experiments e
        WHERE e.result >= ? AND e.result <= ?
    """
    if parameter is not None:
        query += " AND e.parameter = ?"
        params.append(parameter.strip().lower())

    if order_by_date:
        query += " ORDER BY e.date ASC;"
    else:
        query += " ORDER BY e.result ASC;"

    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def db_api_get_statistics(conn: sqlite3.Connection, parameter: str | None = None) -> dict[str, float]:
    """Execute SQL aggregate functions COUNT, AVG, MIN, MAX using parameterized queries."""
    params: tuple[Any, ...] = ()
    query = """
        SELECT
            COUNT(*) AS count,
            COALESCE(AVG(result), 0.0) AS avg,
            COALESCE(MIN(result), 0.0) AS min,
            COALESCE(MAX(result), 0.0) AS max
        FROM experiments
    """
    if parameter is not None:
        query += " WHERE parameter = ?"
        params = (parameter.strip().lower(),)

    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row is None:
        return {"count": 0.0, "average": 0.0, "min": 0.0, "max": 0.0}

    return {
        "count": float(row["count"]),
        "average": float(row["avg"]),
        "min": float(row["min"]),
        "max": float(row["max"]),
    }


def db_api_batch_insert(conn: sqlite3.Connection, records: list[dict[str, Any]]) -> int:
    """Execute raw DB-API transaction inserting batch of experiments with ACID rollback on error.

    If any measurement contains an invalid or negative result outside physical bounds,
    the entire transaction is rolled back.
    """
    query = """
        INSERT INTO experiments (title, researcher_id, parameter, result, date, notes)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    cursor = conn.cursor()
    inserted_count = 0
    try:
        for r in records:
            result_val = float(r["result"])
            # Validate invariant: negative absolute temperature check (< -273.15)
            if r.get("parameter", "").lower() == "temperature" and result_val < -273.15:
                raise ValueError(f"Physical constraint violation: Temperature {result_val} < -273.15 C")

            cursor.execute(
                query,
                (
                    r["title"],
                    r["researcher_id"],
                    r["parameter"].lower(),
                    result_val,
                    r["date"],
                    r.get("notes"),
                ),
            )
            inserted_count += 1
        conn.commit()
        return inserted_count
    except Exception:
        conn.rollback()
        raise
