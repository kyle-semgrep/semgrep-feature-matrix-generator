#!/usr/bin/env python3
"""
Semgrep Requirements Matrix Generator

This tool helps Semgrep Solutions Engineers quickly generate custom compatibility
matrices based on customer requirements. It pulls data from multiple sources and
creates formatted reports showing how well Semgrep meets specific needs.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "pandas"])
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd

# Constants
SEMGREP_DOCS_URL = "https://semgrep.dev/docs/supported-languages"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE_EXPIRY_HOURS = 24  # Refresh cached data after this many hours

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Data models
class Language:
    def __init__(self, name: str, maturity: str, features: List[str], package_managers: List[Dict[str, str]]):
        self.name = name
        self.maturity = maturity  # GA, Beta, Experimental, Community
        self.features = features
        self.package_managers = package_managers
        
class SCM:
    def __init__(self, name: str, supported: bool, features: List[str], notes: str = ""):
        self.name = name
        self.supported = supported
        self.features = features
        self.notes = notes

def fetch_language_data() -> Dict[str, Any]:
    """
    Fetch language support data from Semgrep docs or cached data.
    """
    cache_file = os.path.join(DATA_DIR, "language_cache.json")
    
    # Check if we have recent cached data
    if os.path.exists(cache_file):
        try:
            file_age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))).total_seconds() / 3600
            if file_age_hours < CACHE_EXPIRY_HOURS:
                with open(cache_file, 'r') as f:
                    print(f"Using cached language data ({file_age_hours:.1f} hours old)")
                    return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error reading cache file: {e}. Regenerating data.")
            # Continue with regenerating the data
    
    print(f"Fetching latest language data from {SEMGREP_DOCS_URL}")
    
    # In a real implementation, this would parse the HTML from the docs
    # For now, we'll create comprehensive data based on the current documentation
    languages_data = {}
    
    # Define all language data
    language_definitions = {
        "python": Language(
            name="Python",
            maturity="GA",
            features=["Cross-file dataflow analysis", "Framework-specific control flow analysis", "300+ Pro rules", "Reachability analysis"],
            package_managers=[
                {"name": "pip", "lockfiles": ["*requirement*.txt", "*requirement*.pip"]},
                {"name": "Pipenv", "lockfiles": ["Pipfile.lock"]},
                {"name": "Poetry", "lockfiles": ["poetry.lock"]},
                {"name": "uv", "lockfiles": ["uv.lock"]}
            ]
        ),
        "javascript": Language(
            name="JavaScript",
            maturity="GA",
            features=["Cross-file dataflow analysis", "Framework-specific control flow analysis", "70+ Pro rules", "Reachability analysis", "Can detect malicious dependencies"],
            package_managers=[
                {"name": "npm", "lockfiles": ["package-lock.json"]},
                {"name": "Yarn", "lockfiles": ["yarn.lock"]},
                {"name": "pnpm", "lockfiles": ["pnpm-lock.yaml"]}
            ]
        ),
        "typescript": Language(
            name="TypeScript",
            maturity="GA",
            features=["Cross-file dataflow analysis", "Framework-specific control flow analysis", "70+ Pro rules", "Reachability analysis", "Can detect malicious dependencies"],
            package_managers=[
                {"name": "npm", "lockfiles": ["package-lock.json"]},
                {"name": "Yarn", "lockfiles": ["yarn.lock"]},
                {"name": "pnpm", "lockfiles": ["pnpm-lock.yaml"]}
            ]
        ),
        "java": Language(
            name="Java",
            maturity="GA",
            features=["Cross-file dataflow analysis", "Framework-specific control flow analysis", "160+ Pro rules", "Reachability analysis"],
            package_managers=[
                {"name": "Gradle", "lockfiles": ["gradle.lockfile"]},
                {"name": "Maven", "lockfiles": ["Maven-generated dependency tree"]}
            ]
        ),
        "go": Language(
            name="Go",
            maturity="GA",
            features=["Cross-file dataflow analysis", "60+ Pro rules", "Reachability analysis", "Can detect malicious dependencies"],
            package_managers=[
                {"name": "Go modules (go mod)", "lockfiles": ["go.mod"]}
            ]
        ),
        "csharp": Language(
            name="C#",
            maturity="GA",
            features=["Cross-file dataflow analysis", "Supports up to C# 13", "40+ Pro rules", "Reachability analysis", "Can detect malicious dependencies"],
            package_managers=[
                {"name": "NuGet", "lockfiles": ["packages.lock.json"]}
            ]
        ),
        "c": Language(
            name="C",
            maturity="GA",
            features=["Cross-file dataflow analysis", "150+ Pro rules"],
            package_managers=[]
        ),
        "cpp": Language(
            name="C++",
            maturity="GA",
            features=["Cross-file dataflow analysis", "150+ Pro rules"],
            package_managers=[]
        ),
        "kotlin": Language(
            name="Kotlin",
            maturity="GA",
            features=["Cross-file dataflow analysis", "60+ Pro rules", "Reachability analysis"],
            package_managers=[
                {"name": "Gradle", "lockfiles": ["gradle.lockfile"]},
                {"name": "Maven", "lockfiles": ["Maven-generated dependency tree"]}
            ]
        ),
        "ruby": Language(
            name="Ruby",
            maturity="GA",
            features=["Cross-function dataflow analysis", "20+ Pro rules", "Reachability analysis", "Can detect malicious dependencies"],
            package_managers=[
                {"name": "RubyGems", "lockfiles": ["Gemfile.lock"]}
            ]
        ),
        "rust": Language(
            name="Rust",
            maturity="GA",
            features=["Cross-function dataflow analysis", "40+ Pro rules", "Can detect open source licenses", "Can detect malicious dependencies"],
            package_managers=[
                {"name": "Cargo", "lockfiles": ["cargo.lock"]}
            ]
        ),
        "jsx": Language(
            name="JSX",
            maturity="GA",
            features=["Cross-function dataflow analysis", "70+ Pro rules", "Reachability analysis"],
            package_managers=[
                {"name": "npm", "lockfiles": ["package-lock.json"]},
                {"name": "Yarn", "lockfiles": ["yarn.lock"]},
                {"name": "pnpm", "lockfiles": ["pnpm-lock.yaml"]}
            ]
        ),
        "php": Language(
            name="PHP",
            maturity="GA",
            features=["Cross-function dataflow analysis", "20+ Pro rules", "Reachability analysis (Beta)"],
            package_managers=[
                {"name": "Composer", "lockfiles": ["composer.lock"]}
            ]
        ),
        "scala": Language(
            name="Scala",
            maturity="GA",
            features=["Cross-function dataflow analysis", "Community rules", "Reachability analysis"],
            package_managers=[
                {"name": "Maven", "lockfiles": ["Maven-generated dependency tree"]}
            ]
        ),
        "swift": Language(
            name="Swift",
            maturity="GA",
            features=["Cross-function dataflow analysis", "50+ Pro rules", "Reachability analysis"],
            package_managers=[
                {"name": "SwiftPM", "lockfiles": ["Package.resolved"]}
            ]
        ),
        "terraform": Language(
            name="Terraform",
            maturity="GA",
            features=["Cross-function dataflow analysis", "Community rules"],
            package_managers=[]
        ),
        "generic": Language(
            name="Generic",
            maturity="GA",
            features=["Language-agnostic pattern matching"],
            package_managers=[]
        ),
        "json": Language(
            name="JSON",
            maturity="GA",
            features=["Structured data analysis"],
            package_managers=[]
        ),
        "apex": Language(
            name="APEX",
            maturity="Beta",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "elixir": Language(
            name="Elixir",
            maturity="Beta",
            features=["Basic pattern matching"],
            package_managers=[
                {"name": "Hex", "lockfiles": ["mix.lock"]}
            ]
        ),
        "bash": Language(
            name="Bash",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "cairo": Language(
            name="Cairo",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "circom": Language(
            name="Circom",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "clojure": Language(
            name="Clojure",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "dart": Language(
            name="Dart",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[
                {"name": "Pub", "lockfiles": ["pubspec.lock"]}
            ]
        ),
        "dockerfile": Language(
            name="Dockerfile",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "hack": Language(
            name="Hack",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "html": Language(
            name="HTML",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "jsonnet": Language(
            name="Jsonnet",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "julia": Language(
            name="Julia",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "lisp": Language(
            name="Lisp",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "lua": Language(
            name="Lua",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "move_on_aptos": Language(
            name="Move on Aptos",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "move_on_sui": Language(
            name="Move on Sui",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "ocaml": Language(
            name="OCaml",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "r": Language(
            name="R",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "scheme": Language(
            name="Scheme",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "solidity": Language(
            name="Solidity",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "yaml": Language(
            name="YAML",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        ),
        "xml": Language(
            name="XML",
            maturity="Experimental",
            features=["Basic pattern matching"],
            package_managers=[]
        )
    }
    
    # Convert Language objects to dictionaries for JSON serialization
    for key, lang in language_definitions.items():
        languages_data[key] = {
            "name": lang.name,
            "maturity": lang.maturity,
            "features": lang.features,
            "package_managers": lang.package_managers
        }
    
    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(languages_data, f)
    
    return languages_data

def fetch_scm_data() -> Dict[str, Any]:
    """
    Fetch SCM support data from internal sources or manual input.
    """
    cache_file = os.path.join(DATA_DIR, "scm_cache.json")
    
    # Check if we have recent cached data
    if os.path.exists(cache_file):
        try:
            file_age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))).total_seconds() / 3600
            if file_age_hours < CACHE_EXPIRY_HOURS:
                with open(cache_file, 'r') as f:
                    print(f"Using cached SCM data ({file_age_hours:.1f} hours old)")
                    return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error reading cache file: {e}. Regenerating data.")
            # Continue with regenerating the data
    
    print("Fetching latest SCM data")
    
    # In a real implementation, this would connect to the Google Doc API
    # For now, we'll create sample data
    scm_definitions = {
        "github": SCM(
            name="GitHub",
            supported=True,
            features=["PR comments", "PR status checks", "CI integration"],
            notes="Full support for GitHub Cloud and Enterprise"
        ),
        "gitlab": SCM(
            name="GitLab",
            supported=True,
            features=["MR comments", "MR status checks", "CI integration"],
            notes="Supports both GitLab Cloud and self-hosted"
        ),
        "bitbucket": SCM(
            name="Bitbucket",
            supported=True,
            features=["PR comments", "PR status checks", "CI integration"],
            notes="Supports both Bitbucket Cloud and Server"
        ),
        "azure_devops": SCM(
            name="Azure DevOps",
            supported=True,
            features=["PR comments", "PR status checks"],
            notes="Limited support for Azure DevOps Server"
        )
    }
    
    # Convert SCM objects to dictionaries for JSON serialization
    scms_data = {}
    for key, scm in scm_definitions.items():
        scms_data[key] = {
            "name": scm.name,
            "supported": scm.supported,
            "features": scm.features,
            "notes": scm.notes
        }
    
    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(scms_data, f)
    
    return scms_data

def generate_matrix(customer_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a compatibility matrix based on customer requirements.
    """
    languages = fetch_language_data()
    scms = fetch_scm_data()
    
    matrix = {
        "generated_at": datetime.now().isoformat(),
        "customer_name": customer_requirements.get("customer_name", "Unnamed Customer"),
        "languages": {},
        "scms": {}
    }
    
    # Process language requirements
    for lang_name in customer_requirements.get("languages", []):
        lang_name = lang_name.lower()
        if lang_name in languages:
            lang = languages[lang_name]
            matrix["languages"][lang_name] = {
                "name": lang["name"],
                "maturity": lang["maturity"],
                "features": lang["features"],
                "package_managers": lang["package_managers"],
                "supported": True
            }
        else:
            matrix["languages"][lang_name] = {
                "name": lang_name,
                "supported": False,
                "notes": "Not currently supported by Semgrep"
            }
    
    # Process SCM requirements
    for scm_name in customer_requirements.get("scms", []):
        scm_name = scm_name.lower()
        if scm_name in scms:
            scm = scms[scm_name]
            matrix["scms"][scm_name] = {
                "name": scm["name"],
                "supported": scm["supported"],
                "features": scm["features"],
                "notes": scm["notes"]
            }
        else:
            matrix["scms"][scm_name] = {
                "name": scm_name,
                "supported": False,
                "notes": "Not currently supported by Semgrep"
            }
    
    return matrix

def save_matrix_as_csv(matrix: Dict[str, Any], output_file: str) -> None:
    """
    Save the compatibility matrix as a CSV file.
    """
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(["Semgrep Compatibility Matrix for " + matrix["customer_name"]])
        writer.writerow(["Generated on", matrix["generated_at"]])
        writer.writerow([])
        
        # Write language support
        writer.writerow(["LANGUAGE SUPPORT"])
        writer.writerow(["Language", "Supported", "Maturity", "Features", "Package Managers"])
        
        for lang_name, lang_data in matrix["languages"].items():
            if lang_data["supported"]:
                writer.writerow([
                    lang_data["name"],
                    "Yes",
                    lang_data["maturity"],
                    ", ".join(lang_data["features"]),
                    ", ".join([pm["name"] for pm in lang_data["package_managers"]])
                ])
            else:
                writer.writerow([
                    lang_data["name"],
                    "No",
                    "N/A",
                    "N/A",
                    "N/A"
                ])
        
        writer.writerow([])
        
        # Write SCM support
        writer.writerow(["SOURCE CODE MANAGER SUPPORT"])
        writer.writerow(["SCM", "Supported", "Features", "Notes"])
        
        for scm_name, scm_data in matrix["scms"].items():
            if scm_data["supported"]:
                writer.writerow([
                    scm_data["name"],
                    "Yes",
                    ", ".join(scm_data["features"]),
                    scm_data["notes"]
                ])
            else:
                writer.writerow([
                    scm_data["name"],
                    "No",
                    "N/A",
                    scm_data["notes"]
                ])
    
    print(f"Matrix saved to {output_file}")

def save_matrix_as_html(matrix: Dict[str, Any], output_file: str) -> None:
    """
    Save the compatibility matrix as an HTML file.
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Semgrep Compatibility Matrix - {matrix["customer_name"]}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .supported {{ color: green; font-weight: bold; }}
            .not-supported {{ color: red; }}
            .header-row {{ background-color: #0974d7; color: white; }}
            .ga {{ background-color: #e6ffe6; }} /* Light green */
            .beta {{ background-color: #fff2e6; }} /* Light orange */
            .experimental {{ background-color: #ffe6e6; }} /* Light red */
        </style>
    </head>
    <body>
        <h1>Semgrep Compatibility Matrix</h1>
        <div style="margin-bottom: 18px; font-size: 1.1em;">
          <a href=\"https://semgrep.dev/docs/semgrep/languages/\" target=\"_blank\" rel=\"noopener noreferrer\" style=\"margin-right: 18px; color: #0974d7; font-weight: bold; text-decoration: underline;\">Supported Languages</a>
          <a href=\"https://semgrep.dev/docs/integrations/scm/\" target=\"_blank\" rel=\"noopener noreferrer\" style=\"color: #0974d7; font-weight: bold; text-decoration: underline;\">SCM Integrations</a>
        </div>
        <p>Customer: {matrix["customer_name"]}</p>
        <p>Generated on: {matrix["generated_at"]}</p>
        
        <h2>Language Support</h2>
        <table>
            <tr class="header-row">
                <th>Language</th>
                <th>Supported</th>
                <th>Maturity</th>
                <th>Features</th>
                <th>Package Managers</th>
            </tr>
    """
    
    for lang_name, lang_data in matrix["languages"].items():
        maturity_class = ""
        if lang_data["supported"]:
            if lang_data["maturity"] == "GA":
                maturity_class = "ga"
            elif lang_data["maturity"] == "Beta":
                maturity_class = "beta"
            elif lang_data["maturity"] == "Experimental":
                maturity_class = "experimental"
                
            html += f"""
            <tr class="{maturity_class}">
                <td>{lang_data["name"]}</td>
                <td class="supported">Yes</td>
                <td>{lang_data["maturity"]}</td>
                <td>{"<br>".join(lang_data["features"])}</td>
                <td>{"<br>".join([f"{pm['name']} ({', '.join(pm['lockfiles'])})" for pm in lang_data["package_managers"]]) if lang_data["package_managers"] else "N/A"}</td>
            </tr>
            """
        else:
            html += f"""
            <tr>
                <td>{lang_data["name"]}</td>
                <td class="not-supported">No</td>
                <td>N/A</td>
                <td>N/A</td>
                <td>N/A</td>
            </tr>
            """
    
    html += """
        </table>
        
        <h2>Source Code Manager Support</h2>
        <table>
            <tr class="header-row">
                <th>SCM</th>
                <th>Supported</th>
                <th>Features</th>
                <th>Notes</th>
            </tr>
    """
    
    for scm_name, scm_data in matrix["scms"].items():
        if scm_data["supported"]:
            html += f"""
            <tr>
                <td>{scm_data["name"]}</td>
                <td class="supported">Yes</td>
                <td>{"<br>".join(scm_data["features"])}</td>
                <td>{scm_data["notes"]}</td>
            </tr>
            """
        else:
            html += f"""
            <tr>
                <td>{scm_data["name"]}</td>
                <td class="not-supported">No</td>
                <td>N/A</td>
                <td>{scm_data["notes"]}</td>
            </tr>
            """
    
    html += """
        </table>
        
        <div style="margin-top: 30px; font-size: 0.8em;">
            <h3>Maturity Level Definitions</h3>
            <p><strong>GA (Generally Available)</strong>: Highest quality support by the Semgrep team. Reported issues are resolved promptly.</p>
            <p><strong>Beta</strong>: Supported by the Semgrep team. Reported issues are fixed after GA languages.</p>
            <p><strong>Experimental</strong>: There are limitations to this language's functionality. Reported issues are tracked and prioritized with best effort.</p>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Matrix saved to {output_file}")

def interactive_input() -> Dict[str, Any]:
    """
    Interactively collect customer requirements.
    """
    print("\n=== Semgrep Requirements Matrix Generator ===\n")
    
    customer_name = input("Customer name: ")
    
    print("\nEnter languages (comma-separated, e.g., 'python, java, javascript'):")
    languages_input = input("> ")
    languages = [lang.strip() for lang in languages_input.split(",") if lang.strip()]
    
    print("\nEnter SCMs (comma-separated, e.g., 'github, gitlab, bitbucket'):")
    scms_input = input("> ")
    scms = [scm.strip() for scm in scms_input.split(",") if scm.strip()]
    
    return {
        "customer_name": customer_name,
        "languages": languages,
        "scms": scms
    }

def main():
    parser = argparse.ArgumentParser(description="Generate a Semgrep compatibility matrix based on customer requirements")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("-c", "--customer", help="Customer name")
    parser.add_argument("-l", "--languages", help="Comma-separated list of languages")
    parser.add_argument("-s", "--scms", help="Comma-separated list of SCMs")
    parser.add_argument("-o", "--output", default="semgrep_matrix", help="Output file name (without extension)")
    parser.add_argument("--csv", action="store_true", help="Generate CSV output")
    parser.add_argument("--html", action="store_true", help="Generate HTML output")
    
    args = parser.parse_args()
    
    # Default to both output formats if none specified
    if not (args.csv or args.html):
        args.csv = True
        args.html = True
    
    # Get customer requirements
    if args.interactive:
        customer_requirements = interactive_input()
    else:
        if not args.customer or not args.languages or not args.scms:
            print("Error: When not in interactive mode, --customer, --languages, and --scms are required")
            parser.print_help()
            sys.exit(1)
        
        customer_requirements = {
            "customer_name": args.customer,
            "languages": [lang.strip() for lang in args.languages.split(",") if lang.strip()],
            "scms": [scm.strip() for scm in args.scms.split(",") if scm.strip()]
        }
    
    # Generate the matrix
    matrix = generate_matrix(customer_requirements)
    
    # Save the matrix in the requested formats
    if args.csv:
        save_matrix_as_csv(matrix, f"{args.output}.csv")
    
    if args.html:
        save_matrix_as_html(matrix, f"{args.output}.html")

if __name__ == "__main__":
    main() 