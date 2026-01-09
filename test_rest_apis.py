import requests
import pytest

BASE_URL = "https://japp-api.skyelectric.com/api/graphql"
TOKEN = "eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTkzMjI3NDUsImxhbmd1YWdlIjoiZW4iLCJyb2xlIjoiTk9DIiwic3ViIjoiNDZjMWI1NzItZjk2Yi00ZDBmLWJkZmQtNmM2NzkyNjM0ZjE2IiwidHoiOjAsInV0IjowfQ.AYRJZmKoHAUKCYmMBGkIlTT1vgFX6ir3okPkaApGkZcWLdCbKuRozdNWDi7SzKjqn1omMRKafX-SgKaPyGZ-nZMzAX0QeMgDV_hIxf92epOLIY0QYAlMxpEZNp9pfhAukylStcKB9XfdlvyrvJLweGCFM_ktA1iksn1z7vtvAOEogAe2"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

GRAPHQL_QUERY_ENERGY = """
query GetSystemEnergyStatsSummary($systemId: ID!, $start: Long!, $end: Long!) {
  systemEnergyStatsSummaryV2(
    systemId: $systemId,
    startTimestamp: $start,
    endTimestamp: $end
  ) {
    batteryToLoad
    gridConsumed
    gridToBattery
    gridToLoad
    outagesServed
    pvExported
    pvProduced
    pvToBattery
    pvToLoad
    savings
    solarSelfConsumed
    storedEnergy
    treesPlanted
  }
}
"""

TEST_VARIABLES_GRAPHQL = {
    "systemId": "85a3a52f-7ed6-41f1-ad2e-850442a1f172",
        "start": 1767266485000,
        "end": 1767871285000
}


def run_graphql(query, variables):
    response = requests.post(
        BASE_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS
    )
    # Don't raise HTTP error yet; handle manually
    return response


def test_graphql_energy_stats():
    """Test GraphQL systemEnergyStatsSummaryV2"""
    response = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    
    if response.status_code != 200:
        pytest.fail(f"HTTP Error {response.status_code}: {response.text}")

    result = response.json()
    if "errors" in result:
        pytest.fail(f"GraphQL errors: {result['errors']}")

    stats = result["data"]["systemEnergyStatsSummaryV2"]

    # Parse savings to numeric
    savings_value = stats["savings"].replace("Rs.", "").replace(",", "").strip()

    assert isinstance(stats["batteryToLoad"], (int, float))
    assert isinstance(stats["pvToLoad"], (int, float))
    assert isinstance(stats["pvProduced"], (int, float))
    assert float(savings_value) >= 0

    print("\n--- GraphQL Energy Stats ---")
    print(f"Battery to Load: {stats['batteryToLoad']}")
    print(f"Grid Consumed  : {stats['gridConsumed']}")
    print(f"Grid to Battery: {stats['gridToBattery']}")
    print(f"Grid to Load   : {stats['gridToLoad']}")
    print(f"Outages Served : {stats['outagesServed']}")
    print(f"PV Exported    : {stats['pvExported']}")
    print(f"PV Produced    : {stats['pvProduced']}")
    print(f"PV to Battery  : {stats['pvToBattery']}")
    print(f"PV to Load     : {stats['pvToLoad']}")
    print(f"Savings        : Rs. {stats['savings']}")
