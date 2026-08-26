#!/usr/bin/env python3
"""
Generate HTML report from k6 test results
"""

import json
import sys
from datetime import datetime


def generate_report(json_file, output_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SentinelLayer Performance Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .metric {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 4px; }}
        .metric-name {{ font-weight: bold; color: #555; }}
        .metric-value {{ float: right; color: #4CAF50; font-size: 1.2em; }}
        .metric-value.fail {{ color: #f44336; }}
        .summary {{ background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .summary span {{ display: inline-block; margin-right: 20px; }}
        .green {{ color: #4CAF50; }}
        .red {{ color: #f44336; }}
        .orange {{ color: #ff9800; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 SentinelLayer Performance Test Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <span>📊 <strong>Test Duration:</strong> {data.get('metrics', {}).get('iteration_duration', {}).get('value', 'N/A')}</span>
            <span>📈 <strong>Total Requests:</strong> {data.get('metrics', {}).get('http_reqs', {}).get('value', 'N/A')}</span>
            <span>✅ <strong>Success Rate:</strong> {data.get('metrics', {}).get('http_req_failed', {}).get('value', 'N/A')}</span>
        </div>

        <h2>📊 Key Metrics</h2>
"""

    metrics = data.get('metrics', {})
    for key, value in metrics.items():
        if 'duration' in key or 'time' in key:
            html += f"""
        <div class="metric">
            <span class="metric-name">{key}</span>
            <span class="metric-value">{value.get('value', 'N/A')}</span>
        </div>
"""

    html += """
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Report generated: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_report.py <input.json> <output.html>")
        sys.exit(1)

    generate_report(sys.argv[1], sys.argv[2])
