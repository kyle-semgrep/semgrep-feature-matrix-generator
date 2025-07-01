#!/usr/bin/env python3
"""
Enrich Competitors with Latest Data

This script automatically updates competitor data by checking their websites
and documentation for changes. It provides detailed reporting of all changes
found to help track competitive intelligence updates.
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import Dict, List, Any, Tuple
import time
from bs4 import BeautifulSoup
import difflib

# Rate limiting to be respectful to competitor websites
REQUEST_DELAY = 2  # seconds between requests

def load_competitor_data(filename: str) -> Dict[str, Any]:
    """Load competitor data from JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

def save_competitor_data(filename: str, data: Dict[str, Any]) -> None:
    """Save competitor data to JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

def check_website_changes(competitor_name: str, website_url: str) -> Dict[str, Any]:
    """Check competitor website for significant changes."""
    changes = {
        "new_features": [],
        "language_updates": [],
        "pricing_changes": [],
        "product_updates": [],
        "errors": []
    }
    
    try:
        print(f"Checking {competitor_name} website: {website_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FeatureMatrixBot/1.0)'
        }
        
        response = requests.get(website_url, headers=headers, timeout=10)
        time.sleep(REQUEST_DELAY)
        
        if response.status_code != 200:
            changes["errors"].append(f"HTTP {response.status_code} when accessing {website_url}")
            return changes
            
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text().lower()
        
        # Check for new language support mentions
        languages = [
            'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'kotlin',
            'swift', 'c#', 'c++', 'ruby', 'php', 'scala', 'dart', 'groovy'
        ]
        
        for lang in languages:
            if f"new {lang}" in text_content or f"{lang} support" in text_content:
                if "added" in text_content or "now supports" in text_content:
                    changes["language_updates"].append(f"Potential new {lang} support mentioned")
        
        # Check for feature announcements
        feature_keywords = [
            'reachability analysis', 'cross-file analysis', 'dataflow analysis',
            'secret validation', 'sca', 'sast', 'advanced security'
        ]
        
        for keyword in feature_keywords:
            if keyword in text_content and ("new" in text_content or "enhanced" in text_content):
                changes["new_features"].append(f"New/enhanced {keyword} mentioned")
        
        # Check for pricing mentions
        if "pricing" in text_content and ("update" in text_content or "new" in text_content):
            changes["pricing_changes"].append("Pricing updates mentioned on website")
            
    except Exception as e:
        changes["errors"].append(f"Error checking website: {str(e)}")
    
    return changes

def update_competitor_languages(competitor_data: Dict[str, Any], changes: Dict[str, Any]) -> bool:
    """Update language support based on findings."""
    updated = False
    
    # This is a simplified update mechanism - in a real implementation,
    # you'd want more sophisticated parsing of competitor documentation
    for update in changes.get("language_updates", []):
        print(f"  Language update detected: {update}")
        # Here you would implement logic to actually update the language lists
        # based on more detailed analysis
        updated = True
    
    return updated

def generate_change_report(all_changes: Dict[str, Dict[str, Any]]) -> str:
    """Generate a detailed report of all changes found."""
    report = []
    report.append("# Competitive Intelligence Update Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    
    total_changes = 0
    
    for competitor, changes in all_changes.items():
        has_changes = any(changes.get(key, []) for key in ['new_features', 'language_updates', 'pricing_changes', 'product_updates'])
        
        if has_changes or changes.get('errors'):
            report.append(f"## {competitor}")
            report.append("")
            
            for category, items in changes.items():
                if items and category != 'errors':
                    report.append(f"### {category.replace('_', ' ').title()}")
                    for item in items:
                        report.append(f"- {item}")
                        total_changes += 1
                    report.append("")
            
            if changes.get('errors'):
                report.append("### Errors")
                for error in changes['errors']:
                    report.append(f"- ⚠️ {error}")
                report.append("")
        else:
            report.append(f"## {competitor}")
            report.append("No significant changes detected.")
            report.append("")
    
    # Summary
    summary = [
        f"## Summary",
        f"- **Total Changes Detected**: {total_changes}",
        f"- **Competitors Checked**: {len(all_changes)}",
        f"- **Timestamp**: {datetime.now().isoformat()}",
        ""
    ]
    
    return "\n".join(summary + report)

def check_semgrep_capabilities() -> Dict[str, Any]:
    """Check current Semgrep capabilities for comparison."""
    # This would normally fetch from Semgrep's APIs or documentation
    # For now, return a baseline based on known capabilities
    return {
        "sast": {
            "cross_file_dataflow_analysis": True,
            "languages_supported": [
                "Python", "JavaScript", "TypeScript", "Java", "Go", "Ruby", 
                "PHP", "C#", "Kotlin", "Scala", "Swift", "Dart", "Rust"
            ]
        },
        "sca": {
            "reachability_analysis": False,  # Semgrep's primary differentiator need
            "languages_supported": [
                "JavaScript", "TypeScript", "Python", "Java", "Go", "Ruby", "PHP"
            ]
        },
        "secrets": {
            "validation": True,
            "detection_types": ["API keys", "Database credentials", "Cloud tokens", "Custom patterns"]
        }
    }

def main():
    """Main function to update all competitor data."""
    print("🔍 Starting Competitive Intelligence Data Update...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Load competitor files
    competitor_files = [
        "competitors/checkmarx.json",
        "competitors/veracode.json", 
        "competitors/snyk.json",
        "competitors/github-advanced-security.json",
        "competitors/sonarqube.json",
        "competitors/endor-labs.json"
    ]
    
    all_changes = {}
    
    for filename in competitor_files:
        if not os.path.exists(filename):
            print(f"⚠️ Competitor file not found: {filename}")
            continue
            
        competitor_data = load_competitor_data(filename)
        if not competitor_data:
            continue
            
        competitor_name = competitor_data.get("competitor_name", "Unknown")
        website = competitor_data.get("website", "")
        
        print(f"📊 Updating {competitor_name}...")
        
        # Check for changes
        changes = check_website_changes(competitor_name, website)
        all_changes[competitor_name] = changes
        
        # Update data if changes found
        data_updated = update_competitor_languages(competitor_data, changes)
        
        # Update timestamp
        competitor_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # Save updated data
        if data_updated:
            save_competitor_data(filename, competitor_data)
            print(f"  ✅ Updated {competitor_name} data")
        else:
            print(f"  📋 No data changes for {competitor_name}")
    
    # Generate and save report
    report = generate_change_report(all_changes)
    
    report_filename = f"competitive_intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    try:
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved: {report_filename}")
    except Exception as e:
        print(f"❌ Error saving report: {e}")
    
    print("=" * 60)
    print("✅ Competitive Intelligence Update Complete!")
    
    # Print summary
    total_changes = sum(len(changes.get('new_features', [])) + len(changes.get('language_updates', [])) + 
                       len(changes.get('pricing_changes', [])) + len(changes.get('product_updates', []))
                       for changes in all_changes.values())
    
    print(f"📈 Summary: {total_changes} total changes detected across {len(all_changes)} competitors")
    
    if total_changes > 0:
        print(f"📊 Detailed report available in: {report_filename}")

if __name__ == "__main__":
    main() 