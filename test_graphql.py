# test_graphql.py

import requests
from config import BASE_URL, HEADERS

def test_system_energy_stats_summary():
    """GraphQL query with variables"""
    url = f"{BASE_URL}/graphql"

    query = """
    query GetSystemEnergyStatsSummary(
      $systemId: ID!,
      $start: Long!,
      $end: Long!
    ) {
      systemEnergyStatsSummaryV2(
        systemId: $systemId,
        startTimestamp: $start,
        endTimestamp: $end
      ) {
        batteryToLoad
        pvToLoad
        pvProduced
        savings
      }
    }
    """

    variables = {
        "systemId": "85a3a52f-7ed6-41f1-ad2e-850442a1f172",
        "start": 1767266485000,
        "end": 1767871285000
    }

    response = requests.post(
        url,
        json={"query": query, "variables": variables},
        headers=HEADERS
    )

    assert response.status_code == 200
    result = response.json()
    assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"

    stats = result["data"]["systemEnergyStatsSummaryV2"]
    for field in ["batteryToLoad", "pvToLoad", "pvProduced", "savings"]:
        assert field in stats
        assert isinstance(stats[field], (int, float))
