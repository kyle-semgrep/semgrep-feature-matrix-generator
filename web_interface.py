#!/usr/bin/env python3
"""
Web interface for the Requirements Matrix Generator.
This provides a simple browser-based UI for generating compatibility matrices.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for, abort
from werkzeug.utils import secure_filename

# Import competitive analysis engine
try:
    from competitive_analysis import CompetitiveAnalysisEngine, ComparisonResult
    COMPETITIVE_ANALYSIS_AVAILABLE = True
except ImportError:
    COMPETITIVE_ANALYSIS_AVAILABLE = False
    print("⚠️ Competitive analysis not available - competitive_analysis.py not found")

app = Flask(__name__)

# Load language data from JSON
LANGUAGES_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'languages.json')
SCMS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scms.json')

TEMPLATE_FILE = 'web_interface_template.html'  # New static template file

def load_languages():
    with open(LANGUAGES_JSON) as f:
        return json.load(f)

def get_language_info(language_name, languages):
    for lang in languages:
        if lang['language'].lower() == language_name.lower():
            return lang
    return None

def load_scms():
    with open(SCMS_JSON) as f:
        return json.load(f)

def get_scm_info(scm_name, scms):
    for scm in scms:
        if scm['scm'].lower() == scm_name.lower():
            return scm
    return None

def calculate_roi_analysis(roi_data):
    """Calculate ROI comparing other scanners vs Semgrep with AI Assistant"""
    dev_count = roi_data['developer_count']
    hourly_cost = roi_data['hourly_cost']
    triage_time = roi_data['triage_time']
    
    # Other scanners calculations
    other_findings_total = dev_count * roi_data['other_findings_per_dev']
    other_fp_rate = roi_data['other_false_positive_rate'] / 100
    other_fps_total = other_findings_total * other_fp_rate
    other_triage_time_total = other_findings_total * triage_time
    other_triage_cost = other_triage_time_total * hourly_cost
    other_fp_cost = other_fps_total * triage_time * hourly_cost
    
    # Semgrep calculations
    semgrep_findings_total = dev_count * roi_data['semgrep_findings_per_dev']
    semgrep_fp_rate = roi_data['semgrep_false_positive_rate'] / 100
    semgrep_fps_total = semgrep_findings_total * semgrep_fp_rate
    semgrep_autotriage_rate = roi_data['semgrep_autotriage_rate'] / 100
    
    # Auto-triage reduces manual review of false positives
    semgrep_fps_autotriaged = semgrep_fps_total * semgrep_autotriage_rate
    semgrep_fps_manual = semgrep_fps_total - semgrep_fps_autotriaged
    
    # Total findings that need manual review (true positives + manual false positives)
    semgrep_findings_reviewed = (semgrep_findings_total - semgrep_fps_total) + semgrep_fps_manual
    semgrep_triage_time_total = semgrep_findings_reviewed * triage_time
    semgrep_triage_cost = semgrep_triage_time_total * hourly_cost
    semgrep_fp_cost = semgrep_fps_manual * triage_time * hourly_cost
    
    # Savings calculation
    savings = other_fp_cost - semgrep_fp_cost
    
    return {
        'inputs': {
            'developer_count': dev_count,
            'hourly_cost': hourly_cost,
            'triage_time': triage_time,
            'other_findings_per_dev': roi_data['other_findings_per_dev'],
            'other_false_positive_rate': roi_data['other_false_positive_rate'],
            'semgrep_findings_per_dev': roi_data['semgrep_findings_per_dev'],
            'semgrep_false_positive_rate': roi_data['semgrep_false_positive_rate'],
            'semgrep_autotriage_rate': roi_data['semgrep_autotriage_rate']
        },
        'other_scanners': {
            'findings_total': other_findings_total,
            'findings_reviewed': other_findings_total,
            'false_positives_total': other_fps_total,
            'false_positives_reviewed': other_fps_total,
            'triage_time_hours': other_triage_time_total,
            'triage_cost': other_triage_cost,
            'false_positive_cost': other_fp_cost
        },
        'semgrep': {
            'findings_total': semgrep_findings_total,
            'findings_reviewed': semgrep_findings_reviewed,
            'false_positives_total': semgrep_fps_total,
            'false_positives_reviewed': semgrep_fps_manual,
            'false_positives_autotriaged': semgrep_fps_autotriaged,
            'triage_time_hours': semgrep_triage_time_total,
            'triage_cost': semgrep_triage_cost,
            'false_positive_cost': semgrep_fp_cost
        },
        'savings': {
            'false_positive_cost_avoided': savings,
            'time_saved_hours': (other_fps_total - semgrep_fps_manual) * triage_time
        }
    }

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Semgrep Requirements Matrix Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
            background-color: #f8f9fa;
        }
        h1 {
            color: #0974d7;
            border-bottom: 2px solid #0974d7;
            padding-bottom: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], textarea, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .inline-fields {
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
        }
        .field-half {
            flex: 1;
        }
        .field-half select {
            width: 100%;
        }
        button {
            background-color: #0974d7;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0757a0;
        }
        .result {
            margin-top: 30px;
            padding: 25px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .download-links {
            margin-top: 20px;
        }
        .download-links a {
            display: inline-block;
            margin-right: 15px;
            background-color: #4CAF50;
            color: white;
            padding: 8px 12px;
            text-decoration: none;
            border-radius: 4px;
        }
        .download-links a:hover {
            background-color: #45a049;
        }
        .error {
            color: red;
            font-weight: bold;
        }
        .supported-list {
            columns: 4;
            margin-bottom: 20px;
        }
        .table-container {
            width: 100%;
            overflow-x: auto;
            margin-bottom: 25px;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        .matrix-table { 
            border-collapse: collapse; 
            width: 100%; 
            background: white;
            font-size: 0.75em;
        }
        .matrix-table th, .matrix-table td { 
            border: 1px solid #e0e0e0; 
            padding: 10px 6px; 
            text-align: left;
            line-height: 1.4;
            vertical-align: top;
        }
        .matrix-table th { 
            background: linear-gradient(135deg, #0974d7, #0757a0);
            color: white;
            font-weight: 600;
            font-size: 0.8em;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 10;
            padding: 12px 6px;
        }
        .lang-col { min-width: 80px; max-width: 80px; }
        .maturity-col { min-width: 45px; max-width: 45px; text-align: center; }
        .dataflow-col { min-width: 60px; max-width: 60px; }
        .rules-col { min-width: 40px; max-width: 40px; text-align: center; }
        .yn-col { min-width: 35px; max-width: 35px; text-align: center; }
        .list-col { min-width: 120px; max-width: 180px; }
        .maturity-badge {
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.65em;
            font-weight: bold;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .maturity-ga { background: #28a745; color: white; }
        .maturity-beta { background: #ffc107; color: #333; }
        .maturity-experimental { background: #dc3545; color: white; }
        .yes { color: #28a745; font-weight: bold; }
        .no { color: #6c757d; }
        .feature-list {
            word-wrap: break-word;
            font-size: 0.85em;
            line-height: 1.4;
            font-weight: 500;
        }
        .ga { background-color: #e6ffe6; } /* Light green */
        .beta { background-color: #fff2e6; } /* Light orange */
        .experimental { background-color: #ffe6e6; } /* Light red */
        .maturity-legend {
            margin-bottom: 15px;
            font-size: 0.8em;
        }
        .maturity-legend span {
            padding: 2px 8px;
            margin-right: 10px;
            border-radius: 3px;
        }
        .collapsible {
            background-color: #f2f2f2;
            color: #444;
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            margin-bottom: 10px;
        }
        .active, .collapsible:hover {
            background-color: #e6e6e6;
        }
        .content {
            padding: 0 18px;
            display: none;
            overflow: hidden;
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>
    <div class="container">
    <h1><img src="https://upload.wikimedia.org/wikipedia/commons/8/8e/Semgrep_logo.svg" alt="Semgrep" style="height: 32px; vertical-align: middle; margin-right: 10px;">Requirements Matrix Generator</h1>
    <div style="margin-bottom: 18px; font-size: 1.1em;">
      <a href="https://semgrep.dev/docs/semgrep/languages/" target="_blank" rel="noopener noreferrer" style="margin-right: 18px; color: #0974d7; font-weight: bold; text-decoration: underline;">Supported Languages</a>
      <a href="https://semgrep.dev/docs/integrations/scm/" target="_blank" rel="noopener noreferrer" style="color: #0974d7; font-weight: bold; text-decoration: underline;">SCM Integrations</a>
    </div>
    
    <div class="alert-info">
      <strong>Data Source Transparency:</strong>
      Language and SCM support information is sourced directly from the official Semgrep documentation.
      See <a href="https://semgrep.dev/docs/semgrep/languages/" target="_blank" rel="noopener noreferrer">Supported Languages</a> and
      <a href="https://semgrep.dev/docs/integrations/scm/" target="_blank" rel="noopener noreferrer">SCM Integrations</a>.
    </div>
    
    <div class="form-group">
        <p>This tool helps Sales generate custom compatibility
        matrices based on customer requirements.</p>
    </div>
    
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    
    <form method="post" action="/">
        <div class="form-group">
            <label for="customer_name">Customer Name:</label>
            <input type="text" id="customer_name" name="customer_name" required>
        </div>
        
        <div class="form-group">
            <label for="languages">Languages (comma-separated):</label>
            <input type="text" id="languages" name="languages" placeholder="e.g., python, java, javascript" required>
            
            <button type="button" class="collapsible">View Supported Languages</button>
            <div class="content">
                <div class="maturity-legend">
                    <p><strong>Maturity Levels:</strong>
                    <span class="maturity-badge maturity-ga">GA</span>
                    <span class="maturity-badge maturity-beta">Beta</span>
                    <span class="maturity-badge maturity-experimental">Exp</span>
                    </p>
                </div>
                
                <div class="table-container">
                    <table class="matrix-table">
                        <tr>
                            <th class="lang-col">Lang</th>
                            <th class="maturity-col">Mat</th>
                            <th class="dataflow-col">Dataflow</th>
                            <th class="rules-col">Rules</th>
                            <th class="yn-col">Reach</th>
                            <th class="yn-col">Lic</th>
                            <th class="yn-col">Mal</th>
                            <th class="list-col">Pkg Mgrs</th>
                            <th class="list-col">Lockfiles</th>
                            <th class="yn-col">No Lock</th>
                        </tr>
                        {% for lang in all_languages %}
                        {% if lang.get('semgrep_docs') %}
                        <tr class="{{ lang['maturity']|lower }}">
                            <td class="lang-col"><strong>{{ lang.semgrep_docs.language }}</strong></td>
                            <td class="maturity-col"><span class="maturity-badge maturity-{{ lang.semgrep_docs.maturity|lower }}">{{ lang.semgrep_docs.maturity }}</span></td>
                            <td class="dataflow-col">{{ lang.semgrep_docs.dataflow or '-' }}</td>
                            <td class="rules-col">{{ lang.semgrep_docs.pro_rules if lang.semgrep_docs.pro_rules else '-' }}</td>
                            <td class="yn-col {{ 'yes' if lang.semgrep_docs.reachability else 'no' }}">{{ '✅' if lang.semgrep_docs.reachability else '❌' }}</td>
                            <td class="yn-col {{ 'yes' if lang.semgrep_docs.open_source_licenses else 'no' }}">{{ '✅' if lang.semgrep_docs.open_source_licenses else '❌' }}</td>
                            <td class="yn-col {{ 'yes' if lang.semgrep_docs.malicious_dependencies else 'no' }}">{{ '✅' if lang.semgrep_docs.malicious_dependencies else '❌' }}</td>
                            <td class="list-col feature-list">{{ ', '.join(lang.semgrep_docs.package_managers) if lang.semgrep_docs.package_managers else '-' }}</td>
                            <td class="list-col feature-list">{{ ', '.join(lang.semgrep_docs.lockfiles) if lang.semgrep_docs.lockfiles else '-' }}</td>
                            <td class="yn-col {{ 'yes' if lang.semgrep_docs.scan_without_lockfiles else 'no' }}">{{ '✅' if lang.semgrep_docs.scan_without_lockfiles else '❌' }}</td>
                        </tr>
                        {% endif %}
                        {% endfor %}
                    </table>
                </div>
            </div>
        </div>
        
        <div class="form-group">
            <label>Source Code Manager & Plan:</label>
            <div class="inline-fields">
                <div class="field-half">
                    <select id="scm" name="scm" required onchange="updatePlans()">
                        <option value="">Select SCM...</option>
                        <option value="GitHub">GitHub</option>
                        <option value="GitLab">GitLab</option>
                        <option value="Bitbucket">Bitbucket</option>
                        <option value="Azure DevOps">Azure DevOps</option>
                    </select>
                </div>
                <div class="field-half">
                    <select id="plan" name="plan" required>
                        <option value="">Select SCM first...</option>
                    </select>
                </div>
            </div>
            
            <button type="button" class="collapsible">View Supported SCMs</button>
            <div class="content">
                <table class="language-table">
                    <tr>
                        <th>SCM</th>
                        <th>Available Plans</th>
                    </tr>
                    <tr>
                        <td>GitHub</td>
                        <td>GitHub Free, GitHub Pro, GitHub Team, GitHub Enterprise Cloud, GitHub Enterprise Server</td>
                    </tr>
                    <tr>
                        <td>GitLab</td>
                        <td>GitLab Free, GitLab Premium, GitLab Ultimate, GitLab Dedicated / Dedicated for Government, GitLab Self-Managed Free, GitLab Self-Managed Premium, GitLab Self-Managed Ultimate</td>
                    </tr>
                    <tr>
                        <td>Bitbucket</td>
                        <td>Bitbucket Cloud Free, Bitbucket Cloud Standard, Bitbucket Cloud Premium, Bitbucket Data Center</td>
                    </tr>
                    <tr>
                        <td>Azure DevOps</td>
                        <td>Azure DevOps Cloud, Azure DevOps Server</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" id="include_competitive" name="include_competitive" onchange="toggleCompetitiveOptions()">
                Include Competitive Intelligence Analysis
            </label>
            <small style="color: #666; display: block; margin-top: 5px;">
                Compare Semgrep's capabilities against selected competitors using the same languages specified above.
            </small>
        </div>
        
        <div id="competitive-options" style="display: none; margin-top: 15px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #f8f9fa;">
            <div class="form-group">
                <label for="competitors">Select Competitors for Analysis:</label>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px;">
                    {% if competitive_available %}
                    {% for competitor in available_competitors %}
                    <label style="display: flex; align-items: center; font-weight: normal;">
                        <input type="checkbox" name="competitors" value="{{ competitor }}" style="margin-right: 8px;">
                        {{ competitor }}
                    </label>
                    {% endfor %}
                    {% else %}
                    <p style="color: #dc3545; margin: 0;">Competitive analysis engine not available.</p>
                    {% endif %}
                </div>
            </div>
            
            <div class="form-group">
                <label for="analysis_focus">Analysis Focus:</label>
                <select id="analysis_focus" name="analysis_focus">
                    <option value="all">All Capabilities (SAST, SCA, Secrets)</option>
                    <option value="sast">SAST Cross-file Dataflow Analysis</option>
                    <option value="sca">SCA Reachability Analysis</option>
                    <option value="secrets">Secrets Validation</option>
                </select>
            </div>
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" id="include_roi" name="include_roi" onchange="toggleROIOptions()">
                Include ROI Analysis
            </label>
            <small style="color: #666; display: block; margin-top: 5px;">
                Calculate return on investment comparing traditional scanners vs Semgrep with AI Assistant.
            </small>
        </div>
        
        <div id="roi-options" style="display: none; margin-top: 15px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #f8f9fa;">
            <h4 style="margin-top: 0; color: #0974d7;">ROI Calculator Inputs</h4>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h5 style="margin-bottom: 10px; color: #495057;">Team & Cost Parameters</h5>
                    <div class="form-group">
                        <label for="developer_count">Developer Count:</label>
                        <input type="number" id="developer_count" name="developer_count" value="50" min="1">
                    </div>
                    <div class="form-group">
                        <label for="hourly_cost">Developer Staff Cost / Hour ($):</label>
                        <input type="number" id="hourly_cost" name="hourly_cost" value="100" min="1">
                    </div>
                    <div class="form-group">
                        <label for="triage_time">Triage Time / Finding (Hours):</label>
                        <input type="number" id="triage_time" name="triage_time" value="0.5" step="0.1" min="0.1">
                    </div>
                </div>
                
                <div>
                    <h5 style="margin-bottom: 10px; color: #495057;">Scanner Performance</h5>
                    <div class="form-group">
                        <label for="other_findings_per_dev">Other Scanners - Findings/Dev/Year:</label>
                        <input type="number" id="other_findings_per_dev" name="other_findings_per_dev" value="24.0" step="0.1" min="0">
                    </div>
                    <div class="form-group">
                        <label for="other_false_positive_rate">Other Scanners - False Positive % (0-100):</label>
                        <input type="number" id="other_false_positive_rate" name="other_false_positive_rate" value="50" min="0" max="100">
                    </div>
                    <div class="form-group">
                        <label for="semgrep_findings_per_dev">Semgrep - Findings/Dev/Year:</label>
                        <input type="number" id="semgrep_findings_per_dev" name="semgrep_findings_per_dev" value="13.2" step="0.1" min="0">
                    </div>
                    <div class="form-group">
                        <label for="semgrep_false_positive_rate">Semgrep - False Positive % (0-100):</label>
                        <input type="number" id="semgrep_false_positive_rate" name="semgrep_false_positive_rate" value="25" min="0" max="100">
                    </div>
                    <div class="form-group">
                        <label for="semgrep_autotriage_rate">Semgrep - Auto-triage % (0-100):</label>
                        <input type="number" id="semgrep_autotriage_rate" name="semgrep_autotriage_rate" value="80" min="0" max="100">
                        <small style="color: #666; font-size: 0.8em;">Percentage of false positives automatically triaged by AI Assistant</small>
                    </div>
                </div>
            </div>
        </div>
        
        <button type="submit">Generate Matrix</button>
    </form>
    
    {% if result %}
    <div class="result">
        <h2>Matrix Generated!</h2>
        <p>Customer: {{ customer_name }}</p>
        <p>Generated on: {{ generated_at }}</p>
        
        <div class="download-links">
            <a href="{{ url_for('download_file', filename='html', customer_name=customer_name) }}">Download HTML Report</a>
            <a href="{{ url_for('download_file', filename='csv', customer_name=customer_name) }}">Download CSV Report</a>
        </div>
        
        <iframe src="{{ url_for('preview_html', customer_name=customer_name) }}" width="100%" height="800px" style="border: 1px solid #ddd; margin-top: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"></iframe>
    </div>
    {% endif %}
    
    <script>
        var coll = document.getElementsByClassName("collapsible");
        for (var i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.display === "block") {
                    content.style.display = "none";
                } else {
                    content.style.display = "block";
                }
            });
        }
        
        function updatePlans() {
            const scm = document.getElementById('scm').value;
            const planSelect = document.getElementById('plan');
            
            // Clear current options
            planSelect.innerHTML = '<option value="">Select plan...</option>';
            
            const plans = {
                'GitHub': ['GitHub Free', 'GitHub Pro', 'GitHub Team', 'GitHub Enterprise Cloud', 'GitHub Enterprise Server'],
                'GitLab': ['GitLab Free', 'GitLab Premium', 'GitLab Ultimate', 'GitLab Dedicated', 'GitLab Self-Managed Free', 'GitLab Self-Managed Premium', 'GitLab Self-Managed Ultimate'],
                'Bitbucket': ['Bitbucket Cloud Free', 'Bitbucket Cloud Standard', 'Bitbucket Cloud Premium', 'Bitbucket Data Center'],
                'Azure DevOps': ['Azure DevOps Cloud', 'Azure DevOps Server']
            };
            
            if (plans[scm]) {
                plans[scm].forEach(plan => {
                    const option = document.createElement('option');
                    option.value = plan;
                    option.textContent = plan;
                    planSelect.appendChild(option);
                });
            }
        }
        
        function toggleCompetitiveOptions() {
            const checkbox = document.getElementById('include_competitive');
            const options = document.getElementById('competitive-options');
            
            if (checkbox.checked) {
                options.style.display = 'block';
            } else {
                options.style.display = 'none';
            }
        }
        
        function toggleROIOptions() {
            const checkbox = document.getElementById('include_roi');
            const options = document.getElementById('roi-options');
            
            if (checkbox.checked) {
                options.style.display = 'block';
            } else {
                options.style.display = 'none';
            }
        }
    </script>
    </div>
</body>
</html>
"""

# Save matrix as HTML and CSV using the JSON data
import csv

def save_matrix_as_csv(matrix, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Semgrep Compatibility Matrix for " + matrix["customer_name"]])
        writer.writerow(["Generated on", matrix["generated_at"]])
        writer.writerow([])
        writer.writerow(["LANGUAGE SUPPORT"])
        writer.writerow([
            "Language", "Maturity", "Dataflow Analysis", "# Pro Rules", "Reachability Analysis", "Open Source License Detection", "Malicious Dependency Detection", "Supported Package Managers", "Supported Lockfiles", "Scan Without Lockfiles"
        ])
        for lang in matrix["languages"]:
            docs = lang.get("semgrep_docs", {})
            writer.writerow([
                lang.get("language", ""),
                lang.get("maturity", ""),
                docs.get("dataflow", ""),
                docs.get("pro_rules", ""),
                "Yes" if docs.get("reachability") else "No",
                "Yes" if docs.get("open_source_licenses") else "No",
                "Yes" if docs.get("malicious_dependencies") else "No",
                ", ".join(docs.get("package_managers", [])),
                ", ".join(docs.get("lockfiles", [])),
                "Yes" if docs.get("scan_without_lockfiles") else "No"
            ])
        writer.writerow([])
        writer.writerow(["SOURCE CODE MANAGER SUPPORT"])
        writer.writerow(["SCM", "Plan", "Unsupported Features"])
        for scm in matrix["scms"]:
            unsupported = scm.get("unsupported_features", "")
            if isinstance(unsupported, list):
                unsupported = ", ".join(unsupported)
            elif isinstance(unsupported, str):
                # Split on newlines or multiple spaces, filter out empty
                unsupported = ", ".join([s.strip() for s in unsupported.replace('\r', '').replace('\n', '\n').split('\n') if s.strip()])
            writer.writerow([
                scm["scm"],
                scm["plan"],
                unsupported
            ])
        
        # Add competitive analysis section if available
        if matrix.get("competitive_analysis"):
            writer.writerow([])
            writer.writerow(["COMPETITIVE INTELLIGENCE ANALYSIS"])
            writer.writerow(["Analysis Focus", matrix.get("analysis_focus", "all").replace("_", " ").title()])
            writer.writerow([])
            
            for analysis in matrix["competitive_analysis"]:
                writer.writerow([f"SEMGREP vs {analysis['competitor_name']}"])
                writer.writerow(["Overall Assessment", analysis["overall_assessment"].replace("_", " ").title()])
                writer.writerow([])
                
                writer.writerow(["CAPABILITY COMPARISONS"])
                writer.writerow(["Capability", "Semgrep Status", "Competitor Status", "Result", "Notes"])
                for cap in analysis["capability_comparisons"]:
                    writer.writerow([
                        cap["capability"],
                        cap["semgrep_status"],
                        cap["competitor_status"],
                        cap["result"].replace("_", " ").title(),
                        cap["notes"]
                    ])
                writer.writerow([])
                
                writer.writerow(["LANGUAGE SUPPORT COMPARISON"])
                writer.writerow(["Language", "Semgrep Support", "Competitor Support", "Advantage"])
                for lang in analysis["language_comparisons"]:
                    advantage = lang["result"].replace("_", " ").title()
                    writer.writerow([
                        lang["language"],
                        lang["semgrep_support"],
                        lang["competitor_support"],
                        advantage
                    ])
                writer.writerow([])
                
                writer.writerow(["SALES TALKING POINTS"])
                for i, point in enumerate(analysis["sales_talking_points"], 1):
                    writer.writerow([f"{i}.", point])
                writer.writerow([])
        
        # Add ROI analysis section if available
        if matrix.get("roi_analysis"):
            roi = matrix["roi_analysis"]
            writer.writerow([])
            writer.writerow(["ROI ANALYSIS"])
            writer.writerow(["Comparison: Other Scanners vs Semgrep Code w/ AI Assistant"])
            writer.writerow([])
            
            writer.writerow(["ROI INPUTS"])
            writer.writerow(["Parameter", "Other Scanners", "Semgrep Code w/ AI Assistant"])
            writer.writerow(["Developer count", roi["inputs"]["developer_count"], roi["inputs"]["developer_count"]])
            writer.writerow(["Developer Staff Cost / Hour", f"${roi['inputs']['hourly_cost']}", f"${roi['inputs']['hourly_cost']}"])
            writer.writerow(["Findings / Dev / Year", roi["inputs"]["other_findings_per_dev"], roi["inputs"]["semgrep_findings_per_dev"]])
            writer.writerow(["Findings, Total", f"{roi['other_scanners']['findings_total']:,.0f}", f"{roi['semgrep']['findings_total']:,.0f}"])
            writer.writerow(["Findings, False Positive %", f"{roi['inputs']['other_false_positive_rate']}%", f"{roi['inputs']['semgrep_false_positive_rate']}%"])
            writer.writerow(["Findings, False Positive %, Autotriaged", "", f"{roi['inputs']['semgrep_autotriage_rate']}%"])
            writer.writerow(["Triage Time / Finding (Hours)", roi["inputs"]["triage_time"], roi["inputs"]["triage_time"]])
            writer.writerow([])
            
            writer.writerow(["PROGRAM ACTIVITY"])
            writer.writerow(["Metric", "Other Scanners", "Semgrep Code w/ AI Assistant"])
            writer.writerow(["Findings, Total Reviewed", f"{roi['other_scanners']['findings_reviewed']:,.0f}", f"{roi['semgrep']['findings_reviewed']:,.0f}"])
            writer.writerow(["Findings, False Positive, Reviewed", f"{roi['other_scanners']['false_positives_reviewed']:,.0f}", f"{roi['semgrep']['false_positives_reviewed']:,.0f}"])
            writer.writerow(["Time, Total Triage", f"{roi['other_scanners']['triage_time_hours']:,.1f} hours", f"{roi['semgrep']['triage_time_hours']:,.1f} hours"])
            writer.writerow([])
            
            writer.writerow(["PROGRAM COST"])
            writer.writerow(["Cost Category", "Other Scanners", "Semgrep Code w/ AI Assistant"])
            writer.writerow(["Cost, Triage Total", f"${roi['other_scanners']['triage_cost']:,.0f}", f"${roi['semgrep']['triage_cost']:,.0f}"])
            writer.writerow(["Cost, Wasted on False Positives", f"${roi['other_scanners']['false_positive_cost']:,.0f}", f"${roi['semgrep']['false_positive_cost']:,.0f}"])
            writer.writerow(["Savings through avoiding FPs", "$0", f"${roi['savings']['false_positive_cost_avoided']:,.0f}"])
            writer.writerow([])
    
    print(f"Matrix saved to {output_file}")

def save_matrix_as_html(matrix, output_file):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Semgrep Compatibility Matrix - {matrix['customer_name']}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 15px;
                background-color: #f8f9fa;
                color: #333;
                font-size: 14px;
            }}
            .container {{
                max-width: 100%;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1, h2 {{ 
                color: #0974d7; 
                margin-top: 0;
            }}
            h1 {{
                border-bottom: 3px solid #0974d7;
                padding-bottom: 10px;
                font-size: 1.8em;
            }}
            h2 {{
                margin-top: 30px;
                margin-bottom: 15px;
                font-size: 1.3em;
            }}
            .info {{
                background: #e8f4fd;
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 25px;
                border-left: 4px solid #0974d7;
                font-size: 0.9em;
            }}
            .table-container {{
                width: 100%;
                overflow-x: auto;
                margin-bottom: 25px;
                border-radius: 6px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            }}
            table {{ 
                border-collapse: collapse; 
                width: 100%; 
                background: white;
                font-size: 0.75em;
            }}
            th, td {{ 
                border: 1px solid #e0e0e0; 
                padding: 10px 6px; 
                text-align: left;
                line-height: 1.4;
                vertical-align: top;
            }}
            th {{ 
                background: linear-gradient(135deg, #0974d7, #0757a0);
                color: white;
                font-weight: 600;
                font-size: 0.8em;
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 10;
                padding: 12px 6px;
            }}
            .lang-col {{ min-width: 80px; max-width: 80px; }}
            .maturity-col {{ min-width: 45px; max-width: 45px; text-align: center; }}
            .dataflow-col {{ min-width: 60px; max-width: 60px; }}
            .rules-col {{ min-width: 40px; max-width: 40px; text-align: center; }}
            .yn-col {{ min-width: 35px; max-width: 35px; text-align: center; }}
            .list-col {{ min-width: 120px; max-width: 180px; }}
            
            .ga {{ 
                background-color: #e8f5e8; 
                border-left: 3px solid #28a745;
            }}
            .beta {{ 
                background-color: #fff8e1; 
                border-left: 3px solid #ffc107;
            }}
            .experimental {{ 
                background-color: #ffeaea; 
                border-left: 3px solid #dc3545;
            }}
            .maturity-badge {{
                padding: 2px 4px;
                border-radius: 3px;
                font-size: 0.65em;
                font-weight: bold;
                text-transform: uppercase;
                white-space: nowrap;
            }}
            .maturity-ga {{ background: #28a745; color: white; }}
            .maturity-beta {{ background: #ffc107; color: #333; }}
            .maturity-experimental {{ background: #dc3545; color: white; }}
            .yes {{ color: #28a745; font-weight: bold; }}
            .no {{ color: #6c757d; }}
            .feature-list {{
                word-wrap: break-word;
                font-size: 0.85em;
                line-height: 1.4;
                font-weight: 500;
            }}
            
            /* Mobile responsive - stack info vertically */
            @media (max-width: 768px) {{
                .container {{ padding: 10px; }}
                h1 {{ font-size: 1.5em; }}
                h2 {{ font-size: 1.2em; }}
                
                .desktop-table {{ display: none; }}
                .mobile-cards {{ display: block; }}
                
                .lang-card {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    margin-bottom: 15px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .lang-card h3 {{
                    margin: 0 0 10px 0;
                    color: #0974d7;
                }}
                .lang-detail {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 5px;
                    font-size: 0.9em;
                }}
                .lang-detail strong {{
                    color: #333;
                }}
            }}
            
            @media (min-width: 769px) {{
                .mobile-cards {{ display: none; }}
                .desktop-table {{ display: block; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔒 Semgrep Compatibility Matrix</h1>
            <div class="info">
                <p><strong>Customer:</strong> {matrix['customer_name']}</p>
                <p><strong>Generated on:</strong> {matrix['generated_at']}</p>
            </div>
            
            <h2>📚 Language Support</h2>
            
            <!-- Desktop Table -->
            <div class="table-container desktop-table">
                <table>
                    <tr>
                        <th class="lang-col">Lang</th>
                        <th class="maturity-col">Mat</th>
                        <th class="dataflow-col">Dataflow</th>
                        <th class="rules-col">Rules</th>
                        <th class="yn-col">Reach</th>
                        <th class="yn-col">Lic</th>
                        <th class="yn-col">Mal</th>
                        <th class="list-col">Pkg Mgrs</th>
                        <th class="list-col">Lockfiles</th>
                        <th class="yn-col">No Lock</th>
                    </tr>"""
    
    for lang in matrix["languages"]:
        docs = lang.get("semgrep_docs", {})
        maturity = lang.get('maturity', '').lower()
        maturity_class = f"maturity-{maturity}" if maturity in ['ga', 'beta', 'experimental'] else ""
        row_class = maturity
        
        html += f"""
                    <tr class="{row_class}">
                        <td class="lang-col"><strong>{lang.get('language', '')}</strong></td>
                        <td class="maturity-col"><span class="maturity-badge {maturity_class}">{lang.get('maturity', '')}</span></td>
                        <td class="dataflow-col">{docs.get('dataflow', '-')}</td>
                        <td class="rules-col">{docs.get('pro_rules', 0) if docs.get('pro_rules') else '-'}</td>
                        <td class="yn-col {'yes' if docs.get('reachability') else 'no'}">{'✅' if docs.get('reachability') else '❌'}</td>
                        <td class="yn-col {'yes' if docs.get('open_source_licenses') else 'no'}">{'✅' if docs.get('open_source_licenses') else '❌'}</td>
                        <td class="yn-col {'yes' if docs.get('malicious_dependencies') else 'no'}">{'✅' if docs.get('malicious_dependencies') else '❌'}</td>
                        <td class="list-col feature-list">{', '.join(docs.get('package_managers', [])) or '-'}</td>
                        <td class="list-col feature-list">{', '.join(docs.get('lockfiles', [])) or '-'}</td>
                        <td class="yn-col {'yes' if docs.get('scan_without_lockfiles') else 'no'}">{'✅' if docs.get('scan_without_lockfiles') else '❌'}</td>
                    </tr>"""
    
    html += """
                </table>
            </div>
            
            <!-- Mobile Cards -->
            <div class="mobile-cards">"""
    
    for lang in matrix["languages"]:
        docs = lang.get("semgrep_docs", {})
        maturity = lang.get('maturity', '')
        maturity_class = f"maturity-{maturity.lower()}" if maturity.lower() in ['ga', 'beta', 'experimental'] else ""
        
        html += f"""
                <div class="lang-card">
                    <h3>{lang.get('language', '')} <span class="maturity-badge {maturity_class}">{maturity}</span></h3>
                    <div class="lang-detail"><strong>Dataflow:</strong> <span>{docs.get('dataflow', '-')}</span></div>
                    <div class="lang-detail"><strong>Pro Rules:</strong> <span>{docs.get('pro_rules', 0) if docs.get('pro_rules') else '-'}</span></div>
                    <div class="lang-detail"><strong>Reachability:</strong> <span class="{'yes' if docs.get('reachability') else 'no'}">{'✅ Yes' if docs.get('reachability') else '❌ No'}</span></div>
                    <div class="lang-detail"><strong>License Detection:</strong> <span class="{'yes' if docs.get('open_source_licenses') else 'no'}">{'✅ Yes' if docs.get('open_source_licenses') else '❌ No'}</span></div>
                    <div class="lang-detail"><strong>Malicious Deps:</strong> <span class="{'yes' if docs.get('malicious_dependencies') else 'no'}">{'✅ Yes' if docs.get('malicious_dependencies') else '❌ No'}</span></div>
                    <div class="lang-detail"><strong>Package Managers:</strong> <span>{', '.join(docs.get('package_managers', [])) or '-'}</span></div>
                    <div class="lang-detail"><strong>Lockfiles:</strong> <span>{', '.join(docs.get('lockfiles', [])) or '-'}</span></div>
                    <div class="lang-detail"><strong>Scan w/o Lock:</strong> <span class="{'yes' if docs.get('scan_without_lockfiles') else 'no'}">{'✅ Yes' if docs.get('scan_without_lockfiles') else '❌ No'}</span></div>
                </div>"""
    
    html += """
            </div>
            
            <h2>🔗 Source Code Manager Support</h2>
            <div class="table-container">
                <table>
                    <tr>
                        <th style="min-width: 100px;">SCM</th>
                        <th style="min-width: 150px;">Plan</th>
                        <th>Unsupported Features</th>
                    </tr>"""
    
    for scm in matrix["scms"]:
        unsupported = scm.get('unsupported_features', '')
        if isinstance(unsupported, list):
            unsupported = ', '.join(unsupported) if unsupported else 'All features supported ✅'
        elif isinstance(unsupported, str):
            unsupported = ', '.join([s.strip() for s in unsupported.replace('\r', '').replace('\n', '\n').split('\n') if s.strip()]) if unsupported.strip() else 'All features supported ✅'
        else:
            unsupported = 'All features supported ✅'
            
        html += f"""
                    <tr>
                        <td><strong>{scm['scm']}</strong></td>
                        <td>{scm['plan']}</td>
                        <td class="feature-list">{unsupported}</td>
                    </tr>"""
    
    html += """
                </table>
            </div>
            
            <div class="info" style="margin-top: 30px;">
                <p><strong>Legend:</strong>
                <span class="maturity-badge maturity-ga">GA</span> Generally Available &nbsp;
                <span class="maturity-badge maturity-beta">Beta</span> Beta Release &nbsp;
                <span class="maturity-badge maturity-experimental">Exp</span> Experimental
                </p>
            </div>"""
    
    # Add competitive analysis section if available
    if matrix.get("competitive_analysis"):
        html += """
            <h2>🥊 Competitive Intelligence Analysis</h2>
            <div class="info">
                <p><strong>Analysis Focus:</strong> """ + (matrix.get("analysis_focus", "all").replace("_", " ").title()) + """</p>
                <p>Comparing Semgrep's capabilities against selected competitors for the languages specified above.</p>
            </div>"""
        
        for analysis in matrix["competitive_analysis"]:
            competitor_name = analysis["competitor_name"]
            overall = analysis["overall_assessment"]
            
            # Determine overall assessment display
            if overall == "semgrep_advantage":
                overall_badge = '<span style="background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; font-weight: bold;">✅ Semgrep Advantage</span>'
            elif overall == "competitor_advantage":
                overall_badge = '<span style="background: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; font-weight: bold;">⚠️ Competitor Advantage</span>'
            else:
                overall_badge = '<span style="background: #e2e3e5; color: #383d41; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; font-weight: bold;">🔄 Equivalent</span>'
            
            html += f"""
            <div style="margin: 20px 0; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background: white;">
                <h3 style="margin-top: 0; color: #0974d7; display: flex; justify-content: space-between; align-items: center;">
                    <span>Semgrep vs {competitor_name}</span>
                    {overall_badge}
                </h3>
                
                <h4>🔍 Key Capability Comparisons</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">"""
            
            for cap in analysis["capability_comparisons"]:
                if cap["result"] == "semgrep_advantage":
                    icon = "✅"
                    bg_color = "#f8fff9"
                    border_color = "#28a745"
                elif cap["result"] == "competitor_advantage":
                    icon = "⚠️"
                    bg_color = "#fff8f8"
                    border_color = "#dc3545"
                else:
                    icon = "🔄"
                    bg_color = "#f8f9fa"
                    border_color = "#6c757d"
                
                html += f"""
                    <div style="padding: 10px; border-left: 4px solid {border_color}; background: {bg_color}; border-radius: 4px;">
                        <strong>{icon} {cap["capability"]}</strong><br>
                        <small style="color: #666;">{cap["notes"]}</small>
                    </div>"""
            
            html += """
                </div>
                
                <h4>🎯 Sales Talking Points</h4>
                <div style="background: #e8f4fd; padding: 15px; border-radius: 6px;">
                    <ul style="margin: 0; padding-left: 20px;">"""
            
            for point in analysis["sales_talking_points"]:
                html += f"<li>{point}</li>"
            
            html += """
                    </ul>
                </div>
                
                <h4>🌐 Language Support Comparison</h4>
                <div class="table-container">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.85em;">
                        <tr style="background: #f8f9fa;">
                            <th style="border: 1px solid #e0e0e0; padding: 8px; text-align: left;">Language</th>
                            <th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center;">Semgrep</th>
                            <th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center;">""" + competitor_name + """</th>
                            <th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center;">Advantage</th>
                        </tr>"""
            
            for lang in analysis["language_comparisons"]:
                if lang["result"] == "semgrep_advantage":
                    advantage_text = "🟢 Semgrep"
                elif lang["result"] == "competitor_advantage":
                    advantage_text = "🔴 " + competitor_name
                else:
                    advantage_text = "🟡 Equivalent"
                
                html += f"""
                        <tr>
                            <td style="border: 1px solid #e0e0e0; padding: 8px;"><strong>{lang["language"]}</strong></td>
                            <td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center;">{lang["semgrep_support"]}</td>
                            <td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center;">{lang["competitor_support"]}</td>
                            <td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; font-size: 0.8em;">{advantage_text}</td>
                        </tr>"""
            
            html += """
                    </table>
                </div>
                <h4>📚 Data Sources</h4>
                <div style="font-size: 0.8em; color: #666;">"""
            for source in analysis["data_sources"]:
                html += f'<p>📄 <a href="{source["url"]}" target="_blank">{source["title"]}</a> - {source["description"]}</p>'
            html += """
                    <p><em>💡 All competitive intelligence sourced from public information and official documentation.</em></p>
                </div>"""
            
            html += "</div>"  # Close competitor analysis div
    
    # Add ROI analysis section if available
    if matrix.get("roi_analysis"):
        roi = matrix["roi_analysis"]
        html += """
            <h2>💰 ROI Analysis</h2>
            <div class="info">
                <p><strong>Comparison:</strong> Other Scanners vs Semgrep Code w/ AI Assistant</p>
                <p>This analysis demonstrates the cost savings achieved through Semgrep's lower false positive rates and AI-powered auto-triage capabilities.</p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <!-- ROI Inputs -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;">
                    <h3 style="margin-top: 0; color: #0974d7;">💼 ROI Inputs</h3>
                    <div class="table-container">
                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                            <tr style="background: #e9ecef;">
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Parameter</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Other Scanners</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Semgrep</th>
                            </tr>"""
        
        html += f"""
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Developer count</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['inputs']['developer_count']}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['inputs']['developer_count']}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Developer Staff Cost / Hour</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">${roi['inputs']['hourly_cost']}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">${roi['inputs']['hourly_cost']}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Findings / Dev / Year</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['inputs']['other_findings_per_dev']}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #28a745; font-weight: bold;">{roi['inputs']['semgrep_findings_per_dev']}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Findings, Total</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['other_scanners']['findings_total']:,.0f}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #28a745; font-weight: bold;">{roi['semgrep']['findings_total']:,.0f}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Findings, False Positive %</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['inputs']['other_false_positive_rate']}%</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #28a745; font-weight: bold;">{roi['inputs']['semgrep_false_positive_rate']}%</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Findings, False Positive %, Autotriaged</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #6c757d;">-</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #28a745; font-weight: bold;">{roi['inputs']['semgrep_autotriage_rate']}%</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Triage Time / Finding (Hours)</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['inputs']['triage_time']}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['inputs']['triage_time']}</td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <!-- Program Activity -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;">
                    <h3 style="margin-top: 0; color: #0974d7;">📊 Program Activity</h3>
                    <div class="table-container">
                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                            <tr style="background: #e9ecef;">
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Metric</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Other Scanners</th>
                                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Semgrep</th>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Findings, Total Reviewed</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['other_scanners']['findings_reviewed']:,.0f}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['semgrep']['findings_reviewed']:,.0f}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Findings, False Positive, Reviewed</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['other_scanners']['false_positives_reviewed']:,.0f}</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['semgrep']['false_positives_reviewed']:,.0f}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>Time, Total Triage</strong></td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['other_scanners']['triage_time_hours']:,.1f} hours</td>
                                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{roi['semgrep']['triage_time_hours']:,.1f} hours</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Program Cost - Full Width -->
            <div style="background: linear-gradient(135deg, #e8f5e8, #d4edda); padding: 25px; border-radius: 8px; border: 1px solid #28a745; margin-bottom: 30px;">
                <h3 style="margin-top: 0; color: #155724; text-align: center;">💵 Program Cost Analysis</h3>
                <div class="table-container">
                    <table style="width: 100%; border-collapse: collapse; font-size: 1em;">
                        <tr style="background: rgba(40, 167, 69, 0.1);">
                            <th style="border: 1px solid #28a745; padding: 12px; text-align: left;">Cost Category</th>
                            <th style="border: 1px solid #28a745; padding: 12px; text-align: center;">Other Scanners</th>
                            <th style="border: 1px solid #28a745; padding: 12px; text-align: center;">Semgrep Code w/ AI Assistant</th>
                        </tr>
                        <tr>
                            <td style="border: 1px solid #28a745; padding: 12px;"><strong>Cost, Triage Total</strong></td>
                            <td style="border: 1px solid #28a745; padding: 12px; text-align: center;">${roi['other_scanners']['triage_cost']:,.0f}</td>
                            <td style="border: 1px solid #28a745; padding: 12px; text-align: center; color: #28a745; font-weight: bold;">${roi['semgrep']['triage_cost']:,.0f}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid #28a745; padding: 12px;"><strong>Cost, Wasted on False Positives</strong></td>
                            <td style="border: 1px solid #28a745; padding: 12px; text-align: center;">${roi['other_scanners']['false_positive_cost']:,.0f}</td>
                            <td style="border: 1px solid #28a745; padding: 12px; text-align: center; color: #28a745; font-weight: bold;">${roi['semgrep']['false_positive_cost']:,.0f}</td>
                        </tr>
                        <tr style="background: rgba(40, 167, 69, 0.2);">
                            <td style="border: 1px solid #28a745; padding: 12px;"><strong>💰 Savings through avoiding FPs</strong></td>
                            <td style="border: 1px solid #28a745; padding: 12px; text-align: center;">$0</td>
                            <td style="border: 1px solid #28a745; padding: 12px; text-align: center; color: #155724; font-weight: bold; font-size: 1.2em;">${roi['savings']['false_positive_cost_avoided']:,.0f}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="text-align: center; margin-top: 20px; padding: 15px; background: rgba(255, 255, 255, 0.8); border-radius: 6px;">
                    <p style="margin: 0; font-size: 1.1em; color: #155724;">
                        <strong>🎯 Key Insight:</strong> Semgrep saves <strong>${roi['savings']['false_positive_cost_avoided']:,.0f}</strong> annually through reduced false positives and AI-powered auto-triage, 
                        equivalent to <strong>{roi['savings']['time_saved_hours']:,.0f} developer hours</strong> of productive work time.
                    </p>
                </div>
            </div>"""
    
    html += """
        </div>
    </body>
    </html>
    """
    with open(output_file, 'w') as f:
        f.write(html)
    print(f"Matrix saved to {output_file}")

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    customer_name = ""
    generated_at = ""
    all_languages = load_languages()
    all_scms = load_scms()
    
    # Load available competitors
    available_competitors = []
    if COMPETITIVE_ANALYSIS_AVAILABLE:
        try:
            engine = CompetitiveAnalysisEngine()
            available_competitors = engine.get_available_competitors()
        except Exception as e:
            print(f"Error loading competitors: {e}")
            available_competitors = []
    
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        languages_input = request.form.get('languages', '').strip()
        scm = request.form.get('scm', '').strip()
        plan = request.form.get('plan', '').strip()
        
        # Competitive intelligence options
        include_competitive = request.form.get('include_competitive') == 'on'
        selected_competitors = request.form.getlist('competitors') if include_competitive else []
        analysis_focus = request.form.get('analysis_focus', 'all') if include_competitive else 'all'
        
        # ROI analysis options
        include_roi = request.form.get('include_roi') == 'on'
        roi_data = {}
        if include_roi:
            def safe_float(value_str, default_val):
                """Safely convert string to float, preventing NaN injection"""
                if value_str is None:
                    return default_val
                value_str = str(value_str).strip().lower()
                if value_str in ['nan', 'inf', '-inf', 'infinity', '-infinity']:
                    return default_val
                try:
                    result = float(value_str)
                    if str(result).lower() in ['nan', 'inf', '-inf']:
                        return default_val
                    return result
                except (ValueError, TypeError):
                    return default_val
            
            def safe_int(value_str, default_val):
                """Safely convert string to int"""
                if value_str is None:
                    return default_val
                try:
                    return int(float(str(value_str).strip()))
                except (ValueError, TypeError):
                    return default_val
            
            roi_data = {
                'developer_count': safe_int(request.form.get('developer_count'), 50),
                'hourly_cost': safe_float(request.form.get('hourly_cost'), 100.0),
                'triage_time': safe_float(request.form.get('triage_time'), 0.5),
                'other_findings_per_dev': safe_float(request.form.get('other_findings_per_dev'), 24.0),
                'other_false_positive_rate': safe_float(request.form.get('other_false_positive_rate'), 50.0),
                'semgrep_findings_per_dev': safe_float(request.form.get('semgrep_findings_per_dev'), 13.2),
                'semgrep_false_positive_rate': safe_float(request.form.get('semgrep_false_positive_rate'), 25.0),
                'semgrep_autotriage_rate': safe_float(request.form.get('semgrep_autotriage_rate'), 80.0)
            }
        
        if not customer_name or not languages_input or not scm or not plan:
            error = "All fields are required."
        elif include_competitive and not selected_competitors:
            error = "Please select at least one competitor for analysis."
        else:
            languages = [lang.strip() for lang in languages_input.split(",") if lang.strip()]
            # Create scm_plan_pairs in the expected format
            scm_plan_pairs = [{"scm": scm, "plan": plan}]
            # Build the matrix from the JSON data
            selected_languages = []
            for lang_name in languages:
                lang_info = get_language_info(lang_name, all_languages)
                if lang_info:
                    selected_languages.append(lang_info)
                else:
                    selected_languages.append({
                        "language": lang_name,
                        "maturity": "N/A",
                        "milan_comments": "Not currently supported by Semgrep."
                    })
            selected_scms = []
            for pair in scm_plan_pairs:
                scm_name = pair.get('scm')
                plan = pair.get('plan')
                scm_info = next((s for s in all_scms if s['scm'] == scm_name), None)
                if scm_info and plan in scm_info['plans']:
                    unsupported = scm_info['unsupported_features_by_plan'].get(plan, "")
                    selected_scms.append({
                        "scm": scm_name,
                        "plan": plan,
                        "unsupported_features": unsupported
                    })
                else:
                    selected_scms.append({
                        "scm": scm_name,
                        "plan": plan,
                        "unsupported_features": "Not currently supported by Semgrep."
                    })
            # Generate competitive analysis if requested
            competitive_analysis = None
            if include_competitive and selected_competitors and COMPETITIVE_ANALYSIS_AVAILABLE:
                try:
                    engine = CompetitiveAnalysisEngine()
                    competitive_analysis = []
                    for competitor in selected_competitors:
                        analysis = engine.analyze_competitor(competitor, languages)
                        competitive_analysis.append({
                            'competitor_name': analysis.competitor_name,
                            'overall_assessment': analysis.overall_assessment.value,
                            'capability_comparisons': [
                                {
                                    'capability': cap.capability,
                                    'semgrep_status': cap.semgrep_status,
                                    'competitor_status': cap.competitor_status,
                                    'result': cap.result.value,
                                    'notes': cap.notes,
                                    'importance': cap.importance
                                }
                                for cap in analysis.capability_comparisons
                            ],
                            'language_comparisons': [
                                {
                                    'language': lang.language,
                                    'semgrep_support': lang.semgrep_support,
                                    'competitor_support': lang.competitor_support,
                                    'result': lang.result.value
                                }
                                for lang in analysis.language_comparisons
                            ],
                            'sales_talking_points': analysis.sales_talking_points,
                            'data_sources': engine.get_competitor_summary(competitor).get('data_sources', [])
                        })
                except Exception as e:
                    print(f"Error generating competitive analysis: {e}")
                    competitive_analysis = None
            
            # Generate ROI analysis if requested
            roi_analysis = None
            if include_roi and roi_data:
                try:
                    roi_analysis = calculate_roi_analysis(roi_data)
                except Exception as e:
                    print(f"Error generating ROI analysis: {e}")
                    roi_analysis = None
            
            matrix = {
                "generated_at": datetime.now().isoformat(),
                "customer_name": customer_name,
                "languages": selected_languages,
                "scms": selected_scms,
                "competitive_analysis": competitive_analysis,
                "analysis_focus": analysis_focus if include_competitive else None,
                "roi_analysis": roi_analysis
            }
            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            safe_customer_name = secure_filename(customer_name) or "unknown"
            html_file = os.path.join(output_dir, f"{safe_customer_name}_matrix.html")
            csv_file = os.path.join(output_dir, f"{safe_customer_name}_matrix.csv")
            save_matrix_as_html(matrix, html_file)
            save_matrix_as_csv(matrix, csv_file)
            result = True
    
    # Build the languages table for the form
    languages_table = ""
    for lang in all_languages:
        if lang.get('semgrep_docs'):
            docs = lang.get('semgrep_docs', {})
            maturity = docs.get('maturity', '').lower()
            maturity_class = f"maturity-{maturity}" if maturity in ['ga', 'beta', 'experimental'] else ""
            row_class = maturity
            
            languages_table += f"""
                        <tr class="{row_class}">
                            <td class="lang-col"><strong>{docs.get('language', '')}</strong></td>
                            <td class="maturity-col"><span class="maturity-badge {maturity_class}">{docs.get('maturity', '')}</span></td>
                            <td class="dataflow-col">{docs.get('dataflow', '-') if docs.get('dataflow') else '-'}</td>
                            <td class="rules-col">{docs.get('pro_rules', 0) if docs.get('pro_rules') else '-'}</td>
                            <td class="yn-col {'yes' if docs.get('reachability') else 'no'}">{'✅' if docs.get('reachability') else '❌'}</td>
                            <td class="yn-col {'yes' if docs.get('open_source_licenses') else 'no'}">{'✅' if docs.get('open_source_licenses') else '❌'}</td>
                            <td class="yn-col {'yes' if docs.get('malicious_dependencies') else 'no'}">{'✅' if docs.get('malicious_dependencies') else '❌'}</td>
                            <td class="list-col feature-list">{', '.join(docs.get('package_managers', [])) if docs.get('package_managers') else '-'}</td>
                            <td class="list-col feature-list">{', '.join(docs.get('lockfiles', [])) if docs.get('lockfiles') else '-'}</td>
                            <td class="yn-col {'yes' if docs.get('scan_without_lockfiles') else 'no'}">{'✅' if docs.get('scan_without_lockfiles') else '❌'}</td>
                        </tr>"""
    
    # Show error if present
    error_html = f'<div class="error">{error}</div>' if error else ''
    
    # Show result section if matrix was generated
    result_html = ""
    if result:
        result_html = f"""
    <div class="result">
        <h2>Matrix Generated!</h2>
        <p>Customer: {customer_name}</p>
        <p>Generated on: {generated_at}</p>
        
        <div class="download-links">
            <a href="/download/html?customer_name={customer_name}">Download HTML Report</a>
            <a href="/download/csv?customer_name={customer_name}">Download CSV Report</a>
        </div>
        
        <iframe src="/preview?customer_name={customer_name}" width="100%" height="800px" style="border: 1px solid #ddd; margin-top: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"></iframe>
    </div>"""
    
    # Generate the complete HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Requirements Matrix Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
            background-color: #f8f9fa;
        }}
        h1 {{
            color: #0974d7;
            border-bottom: 2px solid #0974d7;
            padding-bottom: 10px;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }}
        input[type="text"], textarea, select {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
            font-size: 14px;
        }}
        .inline-fields {{
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
        }}
        .field-half {{
            flex: 1;
        }}
        .field-half select {{
            width: 100%;
        }}
        .alert-info {{
            background: #e8f4fd;
            color: #0974d7;
            border-left: 5px solid #0974d7;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 1.05em;
        }}
        button {{
            background-color: #0974d7;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #0757a0;
        }}
        .result {{
            margin-top: 30px;
            padding: 25px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .download-links {{
            margin-top: 20px;
        }}
        .download-links a {{
            display: inline-block;
            margin-right: 15px;
            background-color: #4CAF50;
            color: white;
            padding: 8px 12px;
            text-decoration: none;
            border-radius: 4px;
        }}
        .download-links a:hover {{
            background-color: #45a049;
        }}
        .error {{
            color: red;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .table-container {{
            width: 100%;
            overflow-x: auto;
            margin-bottom: 25px;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }}
        .matrix-table {{ 
            border-collapse: collapse; 
            width: 100%; 
            background: white;
            font-size: 0.75em;
        }}
        .matrix-table th, .matrix-table td {{ 
            border: 1px solid #e0e0e0; 
            padding: 10px 6px; 
            text-align: left;
            line-height: 1.4;
            vertical-align: top;
        }}
        .matrix-table th {{ 
            background: linear-gradient(135deg, #0974d7, #0757a0);
            color: white;
            font-weight: 600;
            font-size: 0.8em;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 10;
            padding: 12px 6px;
        }}
        .lang-col {{ min-width: 80px; max-width: 80px; }}
        .maturity-col {{ min-width: 45px; max-width: 45px; text-align: center; }}
        .dataflow-col {{ min-width: 60px; max-width: 60px; }}
        .rules-col {{ min-width: 40px; max-width: 40px; text-align: center; }}
        .yn-col {{ min-width: 35px; max-width: 35px; text-align: center; }}
        .list-col {{ min-width: 120px; max-width: 180px; }}
        .maturity-badge {{
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.65em;
            font-weight: bold;
            text-transform: uppercase;
            white-space: nowrap;
        }}
        .maturity-ga {{ background: #28a745; color: white; }}
        .maturity-beta {{ background: #ffc107; color: #333; }}
        .maturity-experimental {{ background: #fd7e14; color: white; }}
        .feature-list {{ font-size: 0.95em; color: #333; }}
        .collapsible {{
            background-color: #f1f1f1;
            color: #444;
            cursor: pointer;
            padding: 10px 18px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 1.1em;
            border-radius: 6px;
            margin-bottom: 8px;
        }}
        .active, .collapsible:hover {{
            background-color: #e2e6ea;
        }}
        .content {{
            padding: 0 18px;
            display: none;
            overflow: hidden;
            background-color: #f9f9f9;
            border-radius: 0 0 6px 6px;
            margin-bottom: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
    <h1><img src="https://upload.wikimedia.org/wikipedia/commons/8/8e/Semgrep_logo.svg" alt="Semgrep" style="height: 32px; vertical-align: middle; margin-right: 10px;">Requirements Matrix Generator</h1>

    <div class="alert-info">
      <strong>Data Source Transparency:</strong>
      Language and SCM support information is sourced directly from the official Semgrep documentation.
      See <a href="https://semgrep.dev/docs/semgrep/languages/" target="_blank" rel="noopener noreferrer">Supported Languages</a> and
      <a href="https://semgrep.dev/docs/integrations/scm/" target="_blank" rel="noopener noreferrer">SCM Integrations</a>.
    </div>

    <div class="form-group">
        <p>This tool helps Sales generate custom compatibility
        matrices based on customer requirements.</p>
    </div>

    {error_html}

    <form method="post" action="/">
        <div class="form-group">
            <label for="customer_name">Customer Name:</label>
            <input type="text" id="customer_name" name="customer_name" required>
        </div>
        
        <div class="form-group">
            <label for="languages">Languages (comma-separated):</label>
            <input type="text" id="languages" name="languages" placeholder="e.g., python, java, javascript" required>
            
            <button type="button" class="collapsible">View Supported Languages</button>
            <div class="content">
                <div class="table-container">
                    <table class="matrix-table">
                        <tr>
                            <th class="lang-col">Lang</th>
                            <th class="maturity-col">Mat</th>
                            <th class="dataflow-col">Dataflow</th>
                            <th class="rules-col">Rules</th>
                            <th class="yn-col">Reach</th>
                            <th class="yn-col">Lic</th>
                            <th class="yn-col">Mal</th>
                            <th class="list-col">Pkg Mgrs</th>
                            <th class="list-col">Lockfiles</th>
                            <th class="yn-col">No Lock</th>
                        </tr>
                        {languages_table}
                    </table>
                </div>
            </div>
        </div>
        
        <div class="form-group">
            <label>Source Code Manager & Plan:</label>
            <div class="inline-fields">
                <div class="field-half">
                    <select id="scm" name="scm" required onchange="updatePlans()">
                        <option value="">Select SCM...</option>
                        <option value="GitHub">GitHub</option>
                        <option value="GitLab">GitLab</option>
                        <option value="Bitbucket">Bitbucket</option>
                        <option value="Azure DevOps">Azure DevOps</option>
                    </select>
                </div>
                <div class="field-half">
                    <select id="plan" name="plan" required>
                        <option value="">Select SCM first...</option>
                    </select>
                </div>
            </div>
            
            <button type="button" class="collapsible">View Supported SCMs</button>
            <div class="content">
                <table class="language-table">
                    <tr>
                        <th>SCM</th>
                        <th>Available Plans</th>
                    </tr>
                    <tr>
                        <td>GitHub</td>
                        <td>GitHub Free, GitHub Pro, GitHub Team, GitHub Enterprise Cloud, GitHub Enterprise Server</td>
                    </tr>
                    <tr>
                        <td>GitLab</td>
                        <td>GitLab Free, GitLab Premium, GitLab Ultimate, GitLab Dedicated / Dedicated for Government, GitLab Self-Managed Free, GitLab Self-Managed Premium, GitLab Self-Managed Ultimate</td>
                    </tr>
                    <tr>
                        <td>Bitbucket</td>
                        <td>Bitbucket Cloud Free, Bitbucket Cloud Standard, Bitbucket Cloud Premium, Bitbucket Data Center</td>
                    </tr>
                    <tr>
                        <td>Azure DevOps</td>
                        <td>Azure DevOps Cloud, Azure DevOps Server</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" id="include_competitive" name="include_competitive" onchange="toggleCompetitiveOptions()">
                Include Competitive Intelligence Analysis
            </label>
            <small style="color: #666; display: block; margin-top: 5px;">
                Compare Semgrep's capabilities against selected competitors using the same languages specified above.
            </small>
        </div>
        
        <div id="competitive-options" style="display: none; margin-top: 15px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #f8f9fa;">
            <div class="form-group">
                <label for="competitors">Select Competitors for Analysis:</label>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px;">
                    {', '.join([f'<label style="display: flex; align-items: center; font-weight: normal;"><input type="checkbox" name="competitors" value="{comp}" style="margin-right: 8px;">{comp}</label>' for comp in available_competitors]) if available_competitors else '<p style="color: #dc3545; margin: 0;">Competitive analysis engine not available.</p>'}
                </div>
            </div>
            
            <div class="form-group">
                <label for="analysis_focus">Analysis Focus:</label>
                <select id="analysis_focus" name="analysis_focus">
                    <option value="all">All Capabilities (SAST, SCA, Secrets)</option>
                    <option value="sast">SAST Cross-file Dataflow Analysis</option>
                    <option value="sca">SCA Reachability Analysis</option>
                    <option value="secrets">Secrets Validation</option>
                </select>
            </div>
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" id="include_roi" name="include_roi" onchange="toggleROIOptions()">
                Include ROI Analysis
            </label>
            <small style="color: #666; display: block; margin-top: 5px;">
                Calculate return on investment comparing traditional scanners vs Semgrep with AI Assistant.
            </small>
        </div>
        
        <div id="roi-options" style="display: none; margin-top: 15px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #f8f9fa;">
            <h4 style="margin-top: 0; color: #0974d7;">ROI Calculator Inputs</h4>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h5 style="margin-bottom: 10px; color: #495057;">Team & Cost Parameters</h5>
                    <div class="form-group">
                        <label for="developer_count">Developer Count:</label>
                        <input type="number" id="developer_count" name="developer_count" value="50" min="1">
                    </div>
                    <div class="form-group">
                        <label for="hourly_cost">Developer Staff Cost / Hour ($):</label>
                        <input type="number" id="hourly_cost" name="hourly_cost" value="100" min="1">
                    </div>
                    <div class="form-group">
                        <label for="triage_time">Triage Time / Finding (Hours):</label>
                        <input type="number" id="triage_time" name="triage_time" value="0.5" step="0.1" min="0.1">
                    </div>
                </div>
                
                <div>
                    <h5 style="margin-bottom: 10px; color: #495057;">Scanner Performance</h5>
                    <div class="form-group">
                        <label for="other_findings_per_dev">Other Scanners - Findings/Dev/Year:</label>
                        <input type="number" id="other_findings_per_dev" name="other_findings_per_dev" value="24.0" step="0.1" min="0">
                    </div>
                    <div class="form-group">
                        <label for="other_false_positive_rate">Other Scanners - False Positive % (0-100):</label>
                        <input type="number" id="other_false_positive_rate" name="other_false_positive_rate" value="50" min="0" max="100">
                    </div>
                    <div class="form-group">
                        <label for="semgrep_findings_per_dev">Semgrep - Findings/Dev/Year:</label>
                        <input type="number" id="semgrep_findings_per_dev" name="semgrep_findings_per_dev" value="13.2" step="0.1" min="0">
                    </div>
                    <div class="form-group">
                        <label for="semgrep_false_positive_rate">Semgrep - False Positive % (0-100):</label>
                        <input type="number" id="semgrep_false_positive_rate" name="semgrep_false_positive_rate" value="25" min="0" max="100">
                    </div>
                    <div class="form-group">
                        <label for="semgrep_autotriage_rate">Semgrep - Auto-triage % (0-100):</label>
                        <input type="number" id="semgrep_autotriage_rate" name="semgrep_autotriage_rate" value="80" min="0" max="100">
                        <small style="color: #666; font-size: 0.8em;">Percentage of false positives automatically triaged by AI Assistant</small>
                    </div>
                </div>
            </div>
        </div>
        
        <button type="submit">Generate Matrix</button>
    </form>
    
    {result_html}
    
    <script>
        var coll = document.getElementsByClassName("collapsible");
        for (var i = 0; i < coll.length; i++) {{
            coll[i].addEventListener("click", function() {{
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.display === "block") {{
                    content.style.display = "none";
                }} else {{
                    content.style.display = "block";
                }}
            }});
        }}
        
        var scmPlans = {{
            "GitHub": ["GitHub Free", "GitHub Pro", "GitHub Team", "GitHub Enterprise Cloud", "GitHub Enterprise Server"],
            "GitLab": ["GitLab Free", "GitLab Premium", "GitLab Ultimate", "GitLab Dedicated / Dedicated for Government", "GitLab Self-Managed Free", "GitLab Self-Managed Premium", "GitLab Self-Managed Ultimate"],
            "Bitbucket": ["Bitbucket Cloud Free", "Bitbucket Cloud Standard", "Bitbucket Cloud Premium", "Bitbucket Data Center"],
            "Azure DevOps": ["Azure DevOps Cloud", "Azure DevOps Server"]
        }};
        
        function updatePlans() {{
            var scmSelect = document.getElementById("scm");
            var planSelect = document.getElementById("plan");
            var selectedScm = scmSelect.value;
            
            // Clear existing options
            planSelect.innerHTML = "";
            
            if (selectedScm && scmPlans[selectedScm]) {{
                var plans = scmPlans[selectedScm];
                for (var i = 0; i < plans.length; i++) {{
                    var option = document.createElement("option");
                    option.value = plans[i];
                    option.text = plans[i];
                    planSelect.appendChild(option);
                }}
            }} else {{
                var option = document.createElement("option");
                option.value = "";
                option.text = "Select SCM first...";
                planSelect.appendChild(option);
            }}
        }}
        
        function toggleCompetitiveOptions() {{
            var checkbox = document.getElementById('include_competitive');
            var options = document.getElementById('competitive-options');
            
            if (checkbox.checked) {{
                options.style.display = 'block';
            }} else {{
                options.style.display = 'none';
            }}
        }}
        
        function toggleROIOptions() {{
            var checkbox = document.getElementById('include_roi');
            var options = document.getElementById('roi-options');
            
            if (checkbox.checked) {{
                options.style.display = 'block';
            }} else {{
                options.style.display = 'none';
            }}
        }}
    </script>
    </div>
</body>
</html>"""
    
    from flask import Response
    return Response(html, mimetype='text/html')

@app.route('/download/<filename>')
def download_file(filename):
    customer_name = request.args.get('customer_name', 'unknown')
    safe_customer_name = secure_filename(customer_name) or "unknown"
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    if filename == 'html':
        file_path = os.path.join(output_dir, f"{safe_customer_name}_matrix.html")
    elif filename == 'csv':
        file_path = os.path.join(output_dir, f"{safe_customer_name}_matrix.csv")
    else:
        return redirect(url_for('index'))
    if not os.path.exists(file_path):
        abort(404)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path)
    )

@app.route('/preview')
def preview_html():
    customer_name = request.args.get('customer_name', 'unknown')
    safe_customer_name = secure_filename(customer_name) or "unknown"
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    html_file = os.path.join(output_dir, f"{safe_customer_name}_matrix.html")
    if os.path.exists(html_file):
        with open(html_file, 'r') as f:
            return f.read()
    else:
        return '<html><body><h1>Preview not available</h1><p>File not found.</p></body></html>'

if __name__ == '__main__':
    try:
        import flask
    except ImportError:
        print("Flask is not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    print("\n=== Requirements Matrix Generator Web Interface ===")
    print("Starting web server at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    # Only enable debug if FLASK_DEBUG=1 in the environment
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000) 