from __future__ import annotations

import json
from pathlib import Path
from typing import List

from jinja2 import Environment, BaseLoader

from chatbot_tester.evaluator.domain import EvaluationResult
from .base import Reporter


# A simple embedded HTML template using CDN for Chart.js
# This avoids external file dependencies for the basic reporter.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Evaluation Report - {{ experiment.dataset.dataset_id }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; margin: 2rem; background-color: #f9f9f9; }
        .container { max-width: 1200px; margin: auto; background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 2rem; }
        th, td { padding: 0.75rem; border: 1px solid #ddd; text-align: left; }
        th { background-color: #f4f4f4; }
        .metric-card { display: inline-block; width: 45%; margin: 1%; vertical-align: top; }
        .error-section { color: #d9534f; }
        .details-box { background: #eee; padding: 1rem; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>

<div class="container">
    <h1>Evaluation Report</h1>

    <section>
        <h2>Metadata</h2>
        <table>
            <tr><th>Dataset ID</th><td>{{ experiment.dataset.dataset_id }}</td></tr>
            <tr><th>Version</th><td>{{ experiment.dataset.version }}</td></tr>
            <tr><th>Backend</th><td>{{ experiment.run_config.backend }}</td></tr>
            <tr><th>Model</th><td>{{ experiment.run_config.get("model", "N/A") }}</td></tr>
        </table>
    </section>

    <section>
        <h2>Overall Metrics</h2>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Mean Score</th>
                    <th>Std Dev</th>
                    <th>Sample Count</th>
                </tr>
            </thead>
            <tbody>
                {% for s in summaries %}
                <tr>
                    <td>{{ s.metric }}</td>
                    <td>{{ "%.4f"|format(s.mean) }}</td>
                    <td>{{ "%.4f"|format(s.std) }}</td>
                    <td>{{ s.sample_count }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>

    <section>
        <h2>Visualization</h2>
        <div style="width: 100%; max-width: 800px; margin: auto;">
            <canvas id="metricsChart"></canvas>
        </div>
    </section>

    {% if error_cases %}
    <section class="error-section">
        <h2>Error Cases ({{ error_cases|length }})</h2>
        <table>
            <thead>
                <tr>
                    <th>Sample ID</th>
                    <th>Status</th>
                    <th>Error Message</th>
                </tr>
            </thead>
            <tbody>
                {% for e in error_cases %}
                <tr>
                    <td>{{ e.sample_id }}</td>
                    <td>{{ e.status }}</td>
                    <td>{{ e.message }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
    {% endif %}

    <section>
        <h2>Detailed Breakdown</h2>
        {% for metric in metrics_list %}
        <h3>{{ metric }}</h3>
        <table>
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th>Bucket</th>
                    <th>Mean</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
                {% for b in breakdowns if b.metric == metric %}
                <tr>
                    <td>{{ b.dimension }}</td>
                    <td>{{ b.bucket }}</td>
                    <td>{{ "%.4f"|format(b.mean) }}</td>
                    <td>{{ b.sample_count }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endfor %}
    </section>

</div>

<script>
    const ctx = document.getElementById('metricsChart').getContext('2d');
    const labels = {{ summaries | map(attribute='metric') | list | tojson }};
    const means = {{ summaries | map(attribute='mean') | list | tojson }};

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mean Score',
                data: means,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1.0
                }
            }
        }
    });
</script>

</body>
</html>
"""


class HtmlReporter(Reporter):
    """
    Generates a standalone HTML report with tables and Chart.js visualization.
    """

    def write(self, result: EvaluationResult, output_dir: Path) -> List[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data for template
        metrics_list = sorted({s.metric for s in result.report.summaries})

        env = Environment(loader=BaseLoader())
        template = env.from_string(HTML_TEMPLATE)

        html_content = template.render(
            experiment=result.report.experiment,
            summaries=result.report.summaries,
            breakdowns=result.report.breakdowns,
            error_cases=result.report.error_cases,
            metrics_list=metrics_list
        )

        output_file = output_dir / "report.html"
        output_file.write_text(html_content, encoding="utf-8")

        return [output_file]
