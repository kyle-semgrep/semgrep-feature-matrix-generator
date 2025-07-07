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
                            <th class="maturity-col">Maturity</th>
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
            </div>
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
    
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        languages_input = request.form.get('languages', '').strip()
        scm = request.form.get('scm', '').strip()
        plan = request.form.get('plan', '').strip()
        
        if not customer_name or not languages_input or not scm or not plan:
            error = "All fields are required."
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
            matrix = {
                "generated_at": datetime.now().isoformat(),
                "customer_name": customer_name,
                "languages": selected_languages,
                "scms": selected_scms
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
        .maturity-experimental {{ background: #dc3545; color: white; }}
        .yes {{ color: #28a745; font-weight: bold; }}
        .no {{ color: #6c757d; }}
        .feature-list {{
            word-wrap: break-word;
            font-size: 0.85em;
            line-height: 1.4;
            font-weight: 500;
        }}
        .ga {{ background-color: #e6ffe6; }}
        .beta {{ background-color: #fff2e6; }}
        .experimental {{ background-color: #ffe6e6; }}
        .collapsible {{
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
        }}
        .active, .collapsible:hover {{
            background-color: #e6e6e6;
        }}
        .content {{
            padding: 0 18px;
            display: none;
            overflow: hidden;
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    <div class="container">
    <h1><img src="https://upload.wikimedia.org/wikipedia/commons/8/8e/Semgrep_logo.svg" alt="Semgrep" style="height: 32px; vertical-align: middle; margin-right: 10px;">Requirements Matrix Generator</h1>
    
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
                            <th class="maturity-col">Maturity</th>
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