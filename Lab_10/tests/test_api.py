"""Integration tests for all REST API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from experiment_registry.models import Experiment, Researcher


@pytest.mark.asyncio
async def test_researchers_crud(client: AsyncClient) -> None:
    """Test full CRUD cycle for researchers."""
    # 1. Create researcher
    payload = {"name": "Ірина Коваленко", "department": "Нанотехнології"}
    res = await client.post("/researchers", json=payload)
    assert res.status_code == 201
    created = res.json()
    r_id = created["id"]
    assert created["name"] == payload["name"]

    # 2. Get researcher by id
    res_get = await client.get(f"/researchers/{r_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == r_id

    # 3. List researchers
    res_list = await client.get("/researchers")
    assert res_list.status_code == 200
    assert any(r["id"] == r_id for r in res_list.json())

    # 4. Delete researcher
    res_del = await client.delete(f"/researchers/{r_id}")
    assert res_del.status_code == 204

    # 5. Verify deleted returns 404
    res_after = await client.get(f"/researchers/{r_id}")
    assert res_after.status_code == 404


@pytest.mark.asyncio
async def test_experiments_crud_and_validation(client: AsyncClient, sample_researcher: Researcher) -> None:
    """Test experiments CRUD operations and physical boundaries validation."""
    # 1. Valid creation
    payload = {
        "title": "Вимірювання тиску у вакуумі",
        "parameter": "Тиск (кПа)",
        "result": 101.325,
        "date": "2026-04-10",
        "researcher_id": sample_researcher.id,
        "notes": "Стандартний атмосферний замір",
    }
    res = await client.post("/experiments", json=payload)
    assert res.status_code == 201
    data = res.json()
    exp_id = data["id"]
    assert data["result"] == 101.325

    # 2. Get by ID
    res_get = await client.get(f"/experiments/{exp_id}")
    assert res_get.status_code == 200

    # 3. Validation: Temperature below absolute zero (-273.15) should fail with 422
    invalid_temp = {
        "title": "Кріогенний тест",
        "parameter": "Температура (°C)",
        "result": -300.0,
        "date": "2026-04-11",
        "researcher_id": sample_researcher.id,
    }
    res_inv = await client.post("/experiments", json=invalid_temp)
    assert res_inv.status_code == 422

    # 4. Validation: Non-existent researcher ID should fail with 400
    non_existent_researcher = {
        "title": "Тест без автора",
        "parameter": "Напруга (В)",
        "result": 220.0,
        "date": "2026-04-11",
        "researcher_id": 999999,
    }
    res_no_author = await client.post("/experiments", json=non_existent_researcher)
    assert res_no_author.status_code == 400

    # 5. Delete experiment
    res_del = await client.delete(f"/experiments/{exp_id}")
    assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_statistics_endpoints(
    client: AsyncClient,
    sample_researcher: Researcher,
    sample_experiments: list[Experiment],
) -> None:
    """Test global and researcher-specific statistics endpoints."""
    # 1. Global statistics
    res_stats = await client.get("/experiments/statistics")
    assert res_stats.status_code == 200
    data = res_stats.json()
    assert data["count"] == 3
    assert data["min"] == 100.5
    assert data["max"] == 200.0
    assert data["mean"] > 0

    # 2. Filter statistics by parameter
    res_param = await client.get("/experiments/statistics?parameter=Температура")
    assert res_param.status_code == 200
    temp_data = res_param.json()
    assert temp_data["count"] == 2

    # 3. Researcher statistics
    res_r_stats = await client.get(f"/researchers/{sample_researcher.id}/statistics")
    assert res_r_stats.status_code == 200
    r_data = res_r_stats.json()
    assert r_data["researcher_id"] == sample_researcher.id
    assert r_data["statistics"]["count"] == 3


@pytest.mark.asyncio
async def test_filtering_and_sorting(
    client: AsyncClient,
    sample_experiments: list[Experiment],
) -> None:
    """Test range filtering and date sorting on /experiments."""
    # Filter by result range
    res = await client.get("/experiments?min_result=120.0&max_result=250.0")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    assert all(120.0 <= item["result"] <= 250.0 for item in items)

    # Sort ascending
    res_asc = await client.get("/experiments?sort_by_date=asc")
    assert res_asc.status_code == 200
    dates_asc = [item["date"] for item in res_asc.json()]
    assert dates_asc == sorted(dates_asc)


@pytest.mark.asyncio
async def test_api_404_handlers(client: AsyncClient) -> None:
    """Verify consistent 404 handling for non-existent entities."""
    assert (await client.get("/researchers/999999")).status_code == 404
    assert (await client.delete("/researchers/999999")).status_code == 404
    assert (await client.get("/researchers/999999/experiments")).status_code == 404
    assert (await client.get("/researchers/999999/statistics")).status_code == 404
    assert (await client.get("/experiments/999999")).status_code == 404
    assert (await client.delete("/experiments/999999")).status_code == 404


@pytest.mark.asyncio
async def test_researcher_experiments_list(
    client: AsyncClient, sample_researcher: Researcher, sample_experiments: list[Experiment]
) -> None:
    """Verify listing experiments of a researcher."""
    res = await client.get(f"/researchers/{sample_researcher.id}/experiments")
    assert res.status_code == 200
    assert len(res.json()) == 3
