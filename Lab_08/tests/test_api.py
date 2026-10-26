"""Integration tests for FastAPI REST API endpoints (Lab 08, Variant 15)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_researcher_lifecycle_and_crud(async_client: AsyncClient):
    """Test full CRUD lifecycle for researcher entity."""
    # 1. Create researcher
    payload = {"name": "Dr. Oleksandr Frankov", "department": "Quantum Physics"}
    res = await async_client.post("/researchers", json=payload)
    assert res.status_code == 201
    data = res.json()
    researcher_id = data["id"]
    assert data["name"] == "Dr. Oleksandr Frankov"
    assert data["department"] == "Quantum Physics"
    assert "created_at" in data

    # 2. Get researcher by ID
    res_get = await async_client.get(f"/researchers/{researcher_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == researcher_id

    # 3. List researchers
    res_list = await async_client.get("/researchers?limit=10&skip=0")
    assert res_list.status_code == 200
    assert any(r["id"] == researcher_id for r in res_list.json())

    # 4. Non-existent researcher
    res_not_found = await async_client.get("/researchers/99999")
    assert res_not_found.status_code == 404

    # 5. Delete researcher
    res_del = await async_client.delete(f"/researchers/{researcher_id}")
    assert res_del.status_code == 204

    # 6. Verify deleted
    res_after_del = await async_client.get(f"/researchers/{researcher_id}")
    assert res_after_del.status_code == 404

    # 7. Delete non-existent
    res_del_nf = await async_client.delete("/researchers/99999")
    assert res_del_nf.status_code == 404


@pytest.mark.asyncio
async def test_experiment_crud_validation_and_cascade(async_client: AsyncClient):
    """Test experiment creation, validation, update, and cascade deletion."""
    # Create researcher first
    r_res = await async_client.post(
        "/researchers",
        json={"name": "Prof. Ivan Petrenko", "department": "Applied Physics"},
    )
    r_id = r_res.json()["id"]

    # 1. Valid experiment creation
    exp_payload = {
        "title": "Superconductivity Phase Transition",
        "parameter": "Critical Temperature",
        "result": -196.15,
        "date": "2026-03-15",
        "notes": "Liquid nitrogen cooling cycle",
        "researcher_id": r_id,
    }
    create_res = await async_client.post("/experiments", json=exp_payload)
    assert create_res.status_code == 201
    exp_data = create_res.json()
    exp_id = exp_data["id"]
    assert exp_data["title"] == exp_payload["title"]
    assert exp_data["result"] == -196.15

    # 2. Physical bounds validation failure (< -273.15 C)
    invalid_exp_payload = {
        "title": "Sub-absolute zero test",
        "parameter": "Temperature",
        "result": -300.0,
        "date": "2026-03-16",
        "researcher_id": r_id,
    }
    bad_res = await async_client.post("/experiments", json=invalid_exp_payload)
    assert bad_res.status_code == 422

    # 3. Non-existent researcher foreign key failure
    fk_fail_payload = {
        "title": "Invalid Researcher Experiment",
        "parameter": "Pressure",
        "result": 101.3,
        "date": "2026-03-17",
        "researcher_id": 99999,
    }
    fk_res = await async_client.post("/experiments", json=fk_fail_payload)
    assert fk_res.status_code == 404

    # 4. Partial update (PATCH)
    patch_res = await async_client.patch(
        f"/experiments/{exp_id}",
        json={"result": -195.8, "notes": "Refined sensor measurement"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["result"] == -195.8
    assert patch_res.json()["notes"] == "Refined sensor measurement"

    # 5. Patch non-existent
    bad_patch = await async_client.patch("/experiments/99999", json={"result": 10.0})
    assert bad_patch.status_code == 404

    # 6. Delete experiment
    del_res = await async_client.delete(f"/experiments/{exp_id}")
    assert del_res.status_code == 204

    # 7. Delete non-existent experiment
    bad_del = await async_client.delete("/experiments/99999")
    assert bad_del.status_code == 404


@pytest.mark.asyncio
async def test_experiment_filtering_sorting_and_statistics(async_client: AsyncClient):
    """Test filtering by result range, researcher, sorting by date, and SQL aggregates."""
    # Create two researchers
    r1 = (await async_client.post("/researchers", json={"name": "Alice Smith", "department": "Optics"})).json()
    r2 = (await async_client.post("/researchers", json={"name": "Bob Jones", "department": "Optics"})).json()

    # Add experiments
    data_points = [
        {"title": "Laser Wavelength A", "parameter": "Wavelength", "result": 450.0, "date": "2026-01-10", "researcher_id": r1["id"]},
        {"title": "Laser Wavelength B", "parameter": "Wavelength", "result": 532.0, "date": "2026-02-15", "researcher_id": r1["id"]},
        {"title": "Laser Wavelength C", "parameter": "Wavelength", "result": 650.0, "date": "2026-03-20", "researcher_id": r2["id"]},
        {"title": "Thermal Output", "parameter": "Power", "result": 12.5, "date": "2026-02-01", "researcher_id": r2["id"]},
    ]
    for dp in data_points:
        await async_client.post("/experiments", json=dp)

    # 1. Range filtering (min_result=500.0, max_result=700.0)
    range_res = await async_client.get("/experiments?min_result=500.0&max_result=700.0")
    assert range_res.status_code == 200
    range_items = range_res.json()
    assert len(range_items) == 2
    assert all(500.0 <= item["result"] <= 700.0 for item in range_items)

    # 2. Filter by parameter
    param_res = await async_client.get("/experiments?parameter=Power")
    assert param_res.status_code == 200
    assert len(param_res.json()) == 1
    assert param_res.json()[0]["parameter"] == "Power"

    # 3. Filter by researcher
    r1_exp_res = await async_client.get(f"/researchers/{r1['id']}/experiments")
    assert r1_exp_res.status_code == 200
    assert len(r1_exp_res.json()) == 2

    # 4. Sorting by date (asc and desc)
    asc_res = await async_client.get("/experiments?parameter=Wavelength&sort_by_date=asc")
    assert asc_res.status_code == 200
    asc_dates = [x["date"] for x in asc_res.json()]
    assert asc_dates == sorted(asc_dates)

    desc_res = await async_client.get("/experiments?parameter=Wavelength&sort_by_date=desc")
    assert desc_res.status_code == 200
    desc_dates = [x["date"] for x in desc_res.json()]
    assert desc_dates == sorted(desc_dates, reverse=True)

    # 5. Global & parameter statistics
    stat_res = await async_client.get("/experiments/statistics?parameter=Wavelength")
    assert stat_res.status_code == 200
    stats = stat_res.json()
    assert stats["count"] == 3
    assert stats["min"] == 450.0
    assert stats["max"] == 650.0
    assert stats["average"] == round((450.0 + 532.0 + 650.0) / 3, 2)

    # 6. Researcher statistics
    r1_stats = await async_client.get(f"/researchers/{r1['id']}/statistics")
    assert r1_stats.status_code == 200
    r1_data = r1_stats.json()
    assert r1_data["researcher_id"] == r1["id"]
    assert r1_data["count"] == 2
    assert r1_data["min"] == 450.0
    assert r1_data["max"] == 532.0

    # 7. Non-existent researcher experiments & statistics 404
    assert (await async_client.get("/researchers/99999/experiments")).status_code == 404
    assert (await async_client.get("/researchers/99999/statistics")).status_code == 404


@pytest.mark.asyncio
async def test_batch_statistics_endpoint(async_client: AsyncClient):
    """Test batch statistics endpoint with concurrent execution."""
    # Create researchers with experiments
    r1 = (await async_client.post("/researchers", json={"name": "Res A", "department": "Dep A"})).json()
    r2 = (await async_client.post("/researchers", json={"name": "Res B", "department": "Dep B"})).json()

    await async_client.post("/experiments", json={"title": "E1", "parameter": "P", "result": 10.0, "date": "2026-01-01", "researcher_id": r1["id"]})
    await async_client.post("/experiments", json={"title": "E2", "parameter": "P", "result": 20.0, "date": "2026-01-02", "researcher_id": r2["id"]})

    batch_req = {
        "researcher_ids": [r1["id"], r2["id"], 99999],
        "max_concurrency": 2,
        "timeout_seconds": 3.0,
    }
    batch_res = await async_client.post("/researchers/batch-statistics", json=batch_req)
    assert batch_res.status_code == 200
    res_data = batch_res.json()
    assert res_data["total_queries"] == 3
    assert res_data["successful_queries"] == 2
    assert res_data["failed_queries"] == 1
    assert len(res_data["results"]) == 2
