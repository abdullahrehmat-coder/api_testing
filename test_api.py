import requests
import pytest
import time
import json
from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path

BASE_URL = "https://japp-api.skyelectric.com/api/graphql"
TOKEN = "eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTkzODc0MTgsImxhbmd1YWdlIjoiZW4iLCJyb2xlIjoiTk9DIiwic3ViIjoiNDZjMWI1NzItZjk2Yi00ZDBmLWJkZmQtNmM2NzkyNjM0ZjE2IiwidHoiOjAsInV0IjowfQ.AdSdKO7w4PPQECvfhbQmZ1TqEBR6G92VdbGBzgCGh1aMQjZY3hGQRRupGvlEBu4PtkzysSgZcgAypldy5RkL-i9RACttZJlmG71peII2eNAUTRpotMC6qSyEbecvC0ELETPN0EiiMjdfMSI5KZuCncAEQipF3XOHLA5u1r7t3P3Jbmx7"
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

SCHEMA = {
    "batteryToLoad": "float",
    "gridConsumed": "float",
    "gridToBattery": "float",
    "gridToLoad": "float",
    "outagesServed": "string",
    "pvExported": "float",
    "pvProduced": "float",
    "pvToBattery": "float",
    "pvToLoad": "float",
    "savings": "string",
    "solarSelfConsumed": "float",
    "storedEnergy": "float",
    "treesPlanted": "int"
}

RESPONSE_TIME_THRESHOLD = 5.0

# Global test results storage
test_results = {
    "tests": [],
    "summary": {},
    "response_data": None,
    "response_time": 0,
    "http_status": 0,
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}


def run_graphql(query, variables):
    """Execute GraphQL query and return response with timing"""
    start_time = time.time()
    response = requests.post(
        BASE_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=10
    )
    response_time = time.time() - start_time
    return response, response_time


def validate_data_type(field_name: str, value: Any, expected_type: str) -> tuple:
    """Validate if a value matches the expected type"""
    if value is None:
        return False, f"{field_name} is None"
    
    if expected_type == "float":
        if not isinstance(value, (int, float)):
            return False, f"Expected float, got {type(value).__name__}"
        try:
            float(value)
            return True, "Valid float"
        except (ValueError, TypeError):
            return False, "Cannot convert to float"
    
    elif expected_type == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            return False, f"Expected int, got {type(value).__name__}"
        return True, "Valid integer"
    
    elif expected_type == "string":
        if not isinstance(value, str):
            return False, f"Expected string, got {type(value).__name__}"
        if len(value.strip()) == 0:
            return False, "Empty string"
        return True, "Valid string"
    
    return False, f"Unknown type: {expected_type}"


def log_test_result(test_name: str, passed: bool, message: str, details: dict = None):
    """Log test result to global storage"""
    result = {
        "name": test_name,
        "passed": passed,
        "message": message,
        "details": details or {}
    }
    test_results["tests"].append(result)


# ============= PYTEST TESTS =============

def test_01_http_status():
    """Test HTTP response code is 200"""
    response, response_time = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    test_results["http_status"] = response.status_code
    test_results["response_time"] = response_time
    
    passed = response.status_code == 200
    log_test_result(
        "HTTP Status Code",
        passed,
        f"HTTP {response.status_code}" if passed else f"Expected 200, got {response.status_code}",
        {"expected": 200, "actual": response.status_code}
    )
    assert passed, f"Expected HTTP 200, got {response.status_code}"


def test_02_no_graphql_errors():
    """Test GraphQL response contains no errors"""
    response, _ = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    result = response.json()
    
    has_errors = "errors" in result and result["errors"] is not None
    passed = not has_errors
    
    log_test_result(
        "GraphQL Errors",
        passed,
        "No errors" if passed else f"Errors found: {result.get('errors')}",
        {"errors": result.get("errors")}
    )
    assert passed, f"GraphQL errors: {result.get('errors')}"


def test_03_data_presence():
    """Test response contains data"""
    response, _ = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    result = response.json()
    
    has_data = "data" in result and result["data"] is not None
    has_stats = has_data and "systemEnergyStatsSummaryV2" in result["data"]
    passed = has_data and has_stats
    
    log_test_result(
        "Data Presence",
        passed,
        "Data present with systemEnergyStatsSummaryV2" if passed else "Missing data or stats",
        {"has_data": has_data, "has_stats": has_stats}
    )
    assert passed, "Response missing data or systemEnergyStatsSummaryV2"


def test_04_schema_validation():
    """Test all fields match expected data types"""
    response, _ = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    result = response.json()
    stats = result["data"]["systemEnergyStatsSummaryV2"]
    test_results["response_data"] = stats
    
    errors = []
    field_validations = {}
    
    for field_name in SCHEMA.keys():
        if field_name not in stats:
            errors.append(f"Missing field: {field_name}")
            field_validations[field_name] = {"valid": False, "reason": "Missing"}
        else:
            is_valid, msg = validate_data_type(field_name, stats[field_name], SCHEMA[field_name])
            field_validations[field_name] = {
                "valid": is_valid,
                "reason": msg,
                "value": str(stats[field_name]),
                "expected_type": SCHEMA[field_name],
                "actual_type": type(stats[field_name]).__name__
            }
            if not is_valid:
                errors.append(f"{field_name}: {msg}")
    
    passed = len(errors) == 0
    log_test_result(
        "Schema Validation",
        passed,
        "All fields valid" if passed else f"Validation errors: {len(errors)}",
        {"field_validations": field_validations, "errors": errors}
    )
    assert passed, f"Schema validation failed: {errors}"


def test_05_response_time():
    """Test API response time is within threshold"""
    response, response_time = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    
    passed = response.status_code == 200 and response_time < RESPONSE_TIME_THRESHOLD
    log_test_result(
        "Response Time",
        passed,
        f"Response time: {response_time:.3f}s" if passed else f"Time {response_time:.3f}s exceeds {RESPONSE_TIME_THRESHOLD}s",
        {"response_time": round(response_time, 3), "threshold": RESPONSE_TIME_THRESHOLD}
    )
    assert passed, f"Response time {response_time:.2f}s exceeds threshold {RESPONSE_TIME_THRESHOLD}s"


def test_06_numeric_values_range():
    """Test numeric values are >= 0"""
    response, _ = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    result = response.json()
    stats = result["data"]["systemEnergyStatsSummaryV2"]
    
    float_fields = [k for k, v in SCHEMA.items() if v == "float"]
    errors = []
    validations = {}
    
    for field in float_fields:
        value = stats[field]
        is_valid = value >= 0
        validations[field] = {"value": value, "valid": is_valid}
        if not is_valid:
            errors.append(f"{field}: {value} (negative)")
    
    passed = len(errors) == 0
    log_test_result(
        "Numeric Range Validation",
        passed,
        "All numeric values >= 0" if passed else f"Negative values found: {len(errors)}",
        {"validations": validations, "errors": errors}
    )
    assert passed, f"Negative values found: {errors}"


def test_07_string_formats():
    """Test string fields format validation"""
    response, _ = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    result = response.json()
    stats = result["data"]["systemEnergyStatsSummaryV2"]
    
    validations = {}
    errors = []
    
    # Validate savings
    savings = stats["savings"]
    savings_numeric = savings.replace("Rs.", "").replace(",", "").strip()
    try:
        float(savings_numeric)
        validations["savings"] = {"value": savings, "valid": True, "reason": "Valid format"}
    except ValueError:
        validations["savings"] = {"value": savings, "valid": False, "reason": "Cannot extract numeric value"}
        errors.append("Savings format invalid")
    
    # Validate outagesServed
    outages = stats["outagesServed"]
    outages_valid = len(outages.strip()) > 0
    validations["outagesServed"] = {"value": outages, "valid": outages_valid}
    if not outages_valid:
        errors.append("Outages string is empty")
    
    passed = len(errors) == 0
    log_test_result(
        "String Format Validation",
        passed,
        "All strings properly formatted" if passed else f"Format errors: {len(errors)}",
        {"validations": validations, "errors": errors}
    )
    assert passed, f"String validation errors: {errors}"


def test_08_integer_field():
    """Test integer field (treesPlanted)"""
    response, _ = run_graphql(GRAPHQL_QUERY_ENERGY, TEST_VARIABLES_GRAPHQL)
    result = response.json()
    stats = result["data"]["systemEnergyStatsSummaryV2"]
    
    trees = stats["treesPlanted"]
    is_int = isinstance(trees, int) and not isinstance(trees, bool)
    is_positive = trees >= 0
    
    passed = is_int and is_positive
    log_test_result(
        "Integer Field Validation",
        passed,
        f"treesPlanted: {trees} (valid)" if passed else f"Invalid: {type(trees).__name__}",
        {"value": trees, "type": type(trees).__name__, "is_valid_int": is_int, "is_positive": is_positive}
    )
    assert passed, f"treesPlanted validation failed"


def generate_html_report():
    """Generate fancy HTML report"""
    passed_count = sum(1 for t in test_results["tests"] if t["passed"])
    total_count = len(test_results["tests"])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Test Report</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            
            .header p {{
                font-size: 1.1em;
                opacity: 0.9;
            }}
            
            .summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 30px 40px;
                background: #f8f9fa;
                border-bottom: 2px solid #e9ecef;
            }}
            
            .summary-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            
            .summary-card h3 {{
                color: #667eea;
                font-size: 0.9em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }}
            
            .summary-card .value {{
                font-size: 2em;
                font-weight: bold;
                color: #333;
            }}
            
            .summary-card.success .value {{
                color: #28a745;
            }}
            
            .summary-card.info .value {{
                color: #667eea;
            }}
            
            .content {{
                padding: 40px;
            }}
            
            .test-item {{
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }}
            
            .test-item:hover {{
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                border-color: #667eea;
            }}
            
            .test-item.passed {{
                border-left: 5px solid #28a745;
            }}
            
            .test-item.failed {{
                border-left: 5px solid #dc3545;
            }}
            
            .test-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            
            .test-name {{
                font-size: 1.2em;
                font-weight: 600;
                color: #333;
            }}
            
            .test-status {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }}
            
            .test-status.pass {{
                background: #d4edda;
                color: #155724;
            }}
            
            .test-status.fail {{
                background: #f8d7da;
                color: #721c24;
            }}
            
            .test-message {{
                color: #666;
                margin-bottom: 15px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
                font-size: 0.95em;
            }}
            
            .test-details {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 0.85em;
                overflow-x: auto;
            }}
            
            .test-details pre {{
                margin: 0;
                color: #333;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 0.9em;
            }}
            
            .data-table th {{
                background: #667eea;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            
            .data-table td {{
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }}
            
            .data-table tr:hover {{
                background: #f8f9fa;
            }}
            
            .data-table .valid {{
                color: #28a745;
                font-weight: 600;
            }}
            
            .data-table .invalid {{
                color: #dc3545;
                font-weight: 600;
            }}
            
            .footer {{
                background: #f8f9fa;
                padding: 20px 40px;
                border-top: 2px solid #e9ecef;
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }}
            
            .timestamp {{
                margin-top: 10px;
                color: #999;
            }}
            
            .progress-bar {{
                width: 100%;
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
                overflow: hidden;
                margin-top: 10px;
            }}
            
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #28a745, #20c997);
                transition: width 0.3s ease;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="logo.png" alt="Logo" style="max-width: 120px; margin-bottom: 20px;">
                <h1>Skyelectric QA Test Report</h1>
                <p>API Testing</p>
            </div>
            
            <div class="summary">
                <div class="summary-card success">
                    <h3>Tests Passed</h3>
                    <div class="value">{passed_count}/{total_count}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {(passed_count/total_count)*100}%"></div>
                    </div>
                </div>
                <div class="summary-card info">
                    <h3>Response Time</h3>
                    <div class="value">{test_results["response_time"]:.3f}s</div>
                </div>
                <div class="summary-card info">
                    <h3>HTTP Status</h3>
                    <div class="value">{test_results["http_status"]}</div>
                </div>
                <div class="summary-card info">
                    <h3>Test Date</h3>
                    <div class="value" style="font-size: 0.9em;">{test_results["timestamp"]}</div>
                </div>
            </div>
            
            <div class="content">
                <h2 style="margin-bottom: 30px; color: #333;">Test Results</h2>
    """
    
    for test in test_results["tests"]:
        status_class = "pass" if test["passed"] else "fail"
        status_text = "✓ PASSED" if test["passed"] else "✗ FAILED"
        
        html += f"""
                <div class="test-item {'passed' if test['passed'] else 'failed'}">
                    <div class="test-header">
                        <span class="test-name">{test['name']}</span>
                        <span class="test-status {status_class}">{status_text}</span>
                    </div>
                    <div class="test-message">{test['message']}</div>
        """
        
        if test['details']:
            details_json = json.dumps(test['details'], indent=2)
            html += f"""
                    <div class="test-details">
                        <pre>{details_json}</pre>
                    </div>
            """
        
        html += """
                </div>
        """
    
    # Add response data table
    if test_results["response_data"]:
        html += """
                <h2 style="margin-top: 40px; margin-bottom: 20px; color: #333;">Response Data Validation</h2>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Field Name</th>
                            <th>Value</th>
                            <th>Expected Type</th>
                            <th>Actual Type</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        schema_validation = test_results["tests"][3]["details"].get("field_validations", {})
        for field_name, validation in schema_validation.items():
            status = '<span class="valid">✓ Valid</span>' if validation["valid"] else '<span class="invalid">✗ Invalid</span>'
            html += f"""
                        <tr>
                            <td><strong>{field_name}</strong></td>
                            <td>{validation.get('value', 'N/A')}</td>
                            <td>{validation.get('expected_type', 'N/A')}</td>
                            <td>{validation.get('actual_type', 'N/A')}</td>
                            <td>{status}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
        """
    
    html += f"""
            </div>
            
            <div class="footer">
                <p>Generated by GraphQL API Test Suite</p>
                <div class="timestamp">{test_results['timestamp']}</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


@pytest.fixture(scope="session", autouse=True)
def generate_report(request):
    """Generate report after all tests complete"""
    yield
    
    html_content = generate_html_report()
    report_path = Path("api_test_report.html")
    report_path.write_text(html_content)
    print(f"\n✓ HTML Report generated: {report_path.absolute()}")
    
    # Also generate PDF
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(Path("api_test_report.pdf"))
        print(f"✓ PDF Report generated: {Path('api_test_report.pdf').absolute()}")
    except ImportError:
        print("⚠ WeasyPrint not installed. Run: pip install weasyprint")

def generate_pdf_report():
    """Generate PDF report from HTML"""
    from weasyprint import HTML
    from pathlib import Path
    
    html_content = generate_html_report()
    html_path = Path("api_test_report.html")
    html_path.write_text(html_content)
    
    # Convert to PDF
    HTML(string=html_content).write_pdf(Path("api_test_report.pdf"))
    print(f"\n✓ PDF Report generated: {Path('api_test_report.pdf').absolute()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])