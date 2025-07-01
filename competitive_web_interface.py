#!/usr/bin/env python3
"""
Enhanced Web Interface with Competitive Intelligence

This provides a browser-based UI for generating compatibility matrices
and competitive analysis between Semgrep and competitors.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# Import the competitive analysis engine
from competitive_analysis import CompetitiveAnalysisEngine, ComparisonResult

app = Flask(__name__)

# Enhanced HTML template with competitive intelligence features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Semgrep Feature Matrix & Competitive Intelligence</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
            background-color: #f8f9fa;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 {
            color: #0974d7;
            border-bottom: 2px solid #0974d7;
            padding-bottom: 10px;
            margin: 0 0 20px 0;
        }
        .tab-container {
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 20px;
        }
        .tab {
            display: inline-block;
            padding: 12px 24px;
            margin-right: 10px;
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .tab:hover {
            background: #e9ecef;
        }
        .tab.active {
            background: white;
            border-bottom: 2px solid white;
            margin-bottom: -2px;
            color: #0974d7;
            font-weight: 600;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
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
        button {
            background-color: #0974d7;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        button:hover {
            background-color: #0757a0;
        }
        .competitive-section {
            margin-top: 20px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background: #f8f9fa;
        }
        .competitor-card {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .competitor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .competitor-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #0974d7;
        }
        .advantage-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .semgrep-advantage { background: #d4edda; color: #155724; }
        .competitor-advantage { background: #f8d7da; color: #721c24; }
        .equivalent { background: #e2e3e5; color: #383d41; }
        .capability-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .capability-item {
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid;
        }
        .capability-item.advantage { border-left-color: #28a745; background: #f8fff9; }
        .capability-item.disadvantage { border-left-color: #dc3545; background: #fff8f8; }
        .capability-item.neutral { border-left-color: #6c757d; background: #f8f9fa; }
        .talking-points {
            background: #e8f4fd;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        }
        .talking-points h4 {
            margin-top: 0;
            color: #0974d7;
        }
        .talking-points ul {
            margin: 0;
            padding-left: 20px;
        }
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 0.9em;
        }
        .comparison-table th,
        .comparison-table td {
            border: 1px solid #e0e0e0;
            padding: 8px;
            text-align: left;
        }
        .comparison-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .sources {
            margin-top: 15px;
            font-size: 0.8em;
            color: #6c757d;
        }
        .sources a {
            color: #0974d7;
            text-decoration: none;
        }
        .sources a:hover {
            text-decoration: underline;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .success {
            color: #155724;
            background: #d4edda;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }
        .info-section {
            background: #e8f4fd;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        /* Responsive design */
        @media (max-width: 768px) {
            .tab-container {
                overflow-x: auto;
                white-space: nowrap;
            }
            .capability-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/8e/Semgrep_logo.svg" 
                 alt="Semgrep" style="height: 32px; vertical-align: middle; margin-right: 10px;">
            Feature Matrix & Competitive Intelligence
        </h1>
        
        <div class="info-section">
            <p><strong>🎯 Purpose:</strong> Generate competitive analysis comparing Semgrep's capabilities against major competitors, 
            focusing on SAST cross-file dataflow analysis, SCA reachability, and secrets validation.</p>
            <p><strong>📊 Features:</strong> Side-by-side comparisons, sales talking points, and sourced competitive intelligence.</p>
        </div>
        
        <div class="tab-container">
            <div class="tab active" onclick="switchTab('competitive-analysis')">Competitive Analysis</div>
            <div class="tab" onclick="switchTab('feature-matrix')">Feature Matrix Generator</div>
        </div>
        
        <!-- Competitive Analysis Tab -->
        <div id="competitive-analysis" class="tab-content active">
            <form id="competitive-form" onsubmit="generateCompetitiveAnalysis(event)">
                <div class="form-group">
                    <label for="competitor">Select Competitor:</label>
                    <select id="competitor" name="competitor" required>
                        <option value="">Choose a competitor...</option>
                        {% for competitor in competitors %}
                        <option value="{{ competitor }}">{{ competitor }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="focus_languages">Focus Languages (optional):</label>
                    <input type="text" id="focus_languages" name="focus_languages" 
                           placeholder="e.g., python, java, javascript - leave blank for all languages">
                </div>
                
                <button type="submit">Generate Competitive Analysis</button>
            </form>
            
            <div id="competitive-results" style="display: none;">
                <!-- Competitive analysis results will be populated here -->
            </div>
        </div>
        
        <!-- Feature Matrix Tab -->
        <div id="feature-matrix" class="tab-content">
            <div class="info-section">
                <p><strong>📋 Note:</strong> The full Feature Matrix Generator is available in the main web interface. 
                This is a simplified view focusing on competitive analysis capabilities.</p>
            </div>
            
            <p>For the complete Feature Matrix Generator, please use the main web interface.</p>
            <p><strong>Current focus:</strong> Competitive intelligence and analysis capabilities.</p>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
        
        function generateCompetitiveAnalysis(event) {
            event.preventDefault();
            
            const competitor = document.getElementById('competitor').value;
            const focusLanguages = document.getElementById('focus_languages').value;
            
            if (!competitor) {
                alert('Please select a competitor');
                return;
            }
            
            // Show loading state
            const resultsDiv = document.getElementById('competitive-results');
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = '<div class="loading">🔍 Generating competitive analysis...</div>';
            
            // Make API call to generate analysis
            fetch('/api/competitive-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    competitor: competitor,
                    focus_languages: focusLanguages ? focusLanguages.split(',').map(s => s.trim()) : null
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">❌ ${data.error}</div>`;
                } else {
                    displayCompetitiveResults(data);
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = `<div class="error">❌ Error generating analysis: ${error.message}</div>`;
            });
        }
        
        function displayCompetitiveResults(analysis) {
            const resultsDiv = document.getElementById('competitive-results');
            
            let html = `
                <div class="competitive-section">
                    <h2>🥊 Competitive Analysis: Semgrep vs ${analysis.competitor_name}</h2>
                    
                    <div class="competitor-card">
                        <div class="competitor-header">
                            <div class="competitor-name">${analysis.competitor_name}</div>
                            <div class="advantage-badge ${getAdvantageClass(analysis.overall_assessment)}">
                                ${getAdvantageText(analysis.overall_assessment)}
                            </div>
                        </div>
                        
                        <h3>🔍 Key Capabilities Comparison</h3>
                        <div class="capability-grid">
            `;
            
            analysis.capability_comparisons.forEach(cap => {
                const capClass = getCapabilityClass(cap.result);
                const icon = getCapabilityIcon(cap.result);
                html += `
                    <div class="capability-item ${capClass}">
                        <strong>${icon} ${cap.capability}</strong><br>
                        <small>${cap.notes}</small>
                    </div>
                `;
            });
            
            html += `
                        </div>
                        
                        <div class="talking-points">
                            <h4>🎯 Sales Talking Points</h4>
                            <ul>
            `;
            
            analysis.sales_talking_points.forEach(point => {
                html += `<li>${point}</li>`;
            });
            
            html += `
                            </ul>
                        </div>
                        
                        <h3>🌐 Language Support Comparison</h3>
                        <table class="comparison-table">
                            <thead>
                                <tr>
                                    <th>Language</th>
                                    <th>Semgrep</th>
                                    <th>${analysis.competitor_name}</th>
                                    <th>Advantage</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            analysis.language_comparisons.forEach(lang => {
                const advantageIcon = getAdvantageIcon(lang.result);
                html += `
                    <tr>
                        <td><strong>${lang.language}</strong></td>
                        <td>${lang.semgrep_support}</td>
                        <td>${lang.competitor_support}</td>
                        <td class="${getAdvantageClass(lang.result)}">${advantageIcon} ${getAdvantageText(lang.result)}</td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                        
                        <div class="sources">
                            <h4>📚 Data Sources & Citations:</h4>
            `;
            
            if (analysis.data_sources && analysis.data_sources.length > 0) {
                analysis.data_sources.forEach(source => {
                    html += `<p>📄 <a href="${source.url}" target="_blank">${source.title}</a> - ${source.description}</p>`;
                });
            } else {
                html += `<p>📄 Data compiled from public competitor documentation and websites</p>`;
            }
            
            html += `
                            <p><em>💡 All competitive intelligence sourced from public information and official documentation.</em></p>
                        </div>
                    </div>
                </div>
            `;
            
            resultsDiv.innerHTML = html;
        }
        
        function getAdvantageClass(result) {
            switch (result) {
                case 'semgrep_advantage': return 'semgrep-advantage';
                case 'competitor_advantage': return 'competitor-advantage';
                case 'equivalent': return 'equivalent';
                default: return 'equivalent';
            }
        }
        
        function getAdvantageText(result) {
            switch (result) {
                case 'semgrep_advantage': return 'Semgrep Advantage';
                case 'competitor_advantage': return 'Competitor Advantage';
                case 'equivalent': return 'Equivalent';
                default: return 'Equivalent';
            }
        }
        
        function getAdvantageIcon(result) {
            switch (result) {
                case 'semgrep_advantage': return '🟢';
                case 'competitor_advantage': return '🔴';
                case 'equivalent': return '🟡';
                default: return '🟡';
            }
        }
        
        function getCapabilityClass(result) {
            switch (result) {
                case 'semgrep_advantage': return 'advantage';
                case 'competitor_advantage': return 'disadvantage';
                case 'equivalent': return 'neutral';
                default: return 'neutral';
            }
        }
        
        function getCapabilityIcon(result) {
            switch (result) {
                case 'semgrep_advantage': return '✅';
                case 'competitor_advantage': return '⚠️';
                case 'equivalent': return '🔄';
                default: return '🔄';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with competitive analysis."""
    try:
        # Initialize competitive analysis engine
        engine = CompetitiveAnalysisEngine()
        competitors = engine.get_available_competitors()
        
        return render_template_string(HTML_TEMPLATE, competitors=competitors)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, 
                                    error=f"Error loading data: {str(e)}",
                                    competitors=[])

@app.route('/api/competitive-analysis', methods=['POST'])
def api_competitive_analysis():
    """API endpoint for generating competitive analysis."""
    try:
        data = request.get_json()
        competitor = data.get('competitor')
        focus_languages = data.get('focus_languages')
        
        if not competitor:
            return jsonify({'error': 'Competitor is required'}), 400
        
        # Initialize analysis engine
        engine = CompetitiveAnalysisEngine()
        
        # Generate analysis
        analysis = engine.analyze_competitor(competitor, focus_languages)
        
        # Convert dataclass to dict for JSON serialization
        result = {
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
                    'semgrep_features': lang.semgrep_features,
                    'competitor_features': lang.competitor_features,
                    'result': lang.result.value
                }
                for lang in analysis.language_comparisons
            ],
            'scm_comparison': analysis.scm_comparison,
            'strengths_vs_semgrep': analysis.strengths_vs_semgrep,
            'weaknesses_vs_semgrep': analysis.weaknesses_vs_semgrep,
            'key_differentiators': analysis.key_differentiators,
            'sales_talking_points': analysis.sales_talking_points
        }
        
        # Add data sources
        competitor_summary = engine.get_competitor_summary(competitor)
        result['data_sources'] = competitor_summary.get('data_sources', [])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Competitive Intelligence Platform...")
    print("=" * 60)
    print("📊 Features:")
    print("   ✅ Competitive Analysis Engine")
    print("   ✅ SAST Cross-file Dataflow Comparison")
    print("   ✅ SCA Reachability Analysis Comparison")
    print("   ✅ Secrets Validation Comparison")
    print("   ✅ Sales Talking Points Generation")
    print("   ✅ Source Citations & Documentation")
    print("")
    print("🌐 Access the interface at: http://127.0.0.1:5001")
    print("")
    print("📋 Available Competitors:")
    
    try:
        engine = CompetitiveAnalysisEngine()
        for i, competitor in enumerate(engine.get_available_competitors(), 1):
            print(f"   {i}. {competitor}")
    except Exception as e:
        print(f"   ⚠️ Error loading competitors: {e}")
    
    print("")
    print("🎯 Focus Areas:")
    print("   • Cross-file dataflow analysis for SAST")
    print("   • Reachability analysis for SCA")
    print("   • Secrets validation capabilities")
    print("   • Comprehensive language and SCM support")
    print("")
    print("Ready for competitive analysis! 🥊")
    print("=" * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5001) 