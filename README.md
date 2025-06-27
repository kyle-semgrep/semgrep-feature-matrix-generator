# Semgrep Feature Matrix Generator

A web-based tool for generating custom Semgrep compatibility matrices for sales presentations and customer requirements analysis.

## Overview

This tool helps sales teams quickly generate professional-looking feature compatibility matrices that show which Semgrep features are supported for different programming languages and source code management (SCM) platforms. The matrices are tailored to specific customer requirements and can be exported as HTML or CSV files.

## Features

- **Interactive Web Interface**: User-friendly browser-based interface
- **Language Support Matrix**: Shows programming language support with maturity levels, dataflow analysis, rule counts, and more
- **SCM Compatibility**: Displays supported features for different SCM platforms and plans  
- **Professional Output**: Generates clean, branded HTML and CSV reports
- **Responsive Design**: Works on desktop and mobile devices
- **Reference Tables**: Built-in reference showing all supported languages and SCMs

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd semgrep-feature-matrix-generator
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the web interface**:
   ```bash
   python web_interface.py
   ```

4. **Open your browser** and navigate to: http://127.0.0.1:5000

## Usage

### Web Interface (Recommended)

1. **Launch the application**: Run `python web_interface.py`
2. **Open the web interface**: Navigate to http://127.0.0.1:5000 in your browser
3. **Fill out the form**:
   - Enter customer name
   - Specify required programming languages (comma-separated)
   - Select SCM and plan from the dropdowns
4. **Generate matrix**: Click "Generate Matrix"
5. **Download results**: Use the download links for HTML or CSV formats

### Command Line Interface

For bulk processing or automation:

```bash
python generate.py --customer "Customer Name" --languages "python,java,javascript" --scm "GitHub" --plan "Enterprise"
```

## File Structure

```
semgrep-feature-matrix-generator/
├── web_interface.py          # Main Flask web application
├── generate.py               # Command-line interface
├── languages.json            # Language support database
├── scms.json                # SCM platform database
├── requirements.txt          # Python dependencies
├── output/                  # Generated matrices (gitignored)
├── templates/               # HTML templates
└── data/                    # Source data files
```

## Configuration

### Updating Language Data

To refresh the language support data from Semgrep's official documentation:

```bash
python enrich_languages_with_semgrep_docs.py
```

### Updating SCM Data

To refresh the SCM support data:

```bash
python enrich_scms_with_semgrep_docs.py
```

## Output Formats

### HTML Report
- Professional, branded design with Semgrep logo
- Responsive layout that works on all devices
- Color-coded maturity levels (GA, Beta, Experimental)
- Easy-to-read tables with proper formatting

### CSV Report
- Machine-readable format for further analysis
- All data included: languages, SCMs, and features
- Compatible with Excel and other spreadsheet applications

## Development

### Adding New Languages

Edit `languages.json` to add new programming languages:

```json
{
  "language": "New Language",
  "maturity": "GA",
  "semgrep_docs": {
    "language": "New Language",
    "maturity": "GA",
    "dataflow": "Full",
    "pro_rules": 150,
    "reachability": true,
    // ... other fields
  }
}
```

### Adding New SCMs

Edit `scms.json` to add new source code management platforms:

```json
{
  "scm": "New SCM",
  "plan": "Enterprise Plan",
  "unsupported_features": ["Feature 1", "Feature 2"]
}
```

## Security

This tool has been scanned with Semgrep for security vulnerabilities and follows security best practices:
- No hardcoded credentials or API keys
- Input validation and sanitization
- Secure file handling
- No execution of user-provided code

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test them
4. Run security scans: The code is automatically scanned for security issues
5. Submit a pull request

## Requirements

- Python 3.7+
- Flask 2.0+
- See `requirements.txt` for full dependency list

## License

This project is open source. Please refer to the LICENSE file for details.

## Support

For questions or issues:
1. Check the existing GitHub issues
2. Create a new issue with detailed information
3. Include steps to reproduce any bugs

## Changelog

### v1.0.0
- Initial release with web interface
- Support for 40+ programming languages
- Support for GitHub, GitLab, Bitbucket, and Azure DevOps
- HTML and CSV export functionality
- Responsive design with Semgrep branding 