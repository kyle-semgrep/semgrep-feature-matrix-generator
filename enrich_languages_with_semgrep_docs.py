import json
import requests
from bs4 import BeautifulSoup
import os
import re
import copy

LANGUAGES_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'languages.json')
SEMGREP_DOCS_URL = 'https://semgrep.dev/docs/supported-languages'

# 1. Load existing languages.json
def load_languages():
    with open(LANGUAGES_JSON) as f:
        return json.load(f)

def save_languages(languages):
    with open(LANGUAGES_JSON, 'w') as f:
        json.dump(languages, f, indent=2)

def compare_languages(old, new):
    def lang_key(lang):
        return lang['language'].replace('/', '').replace(' ', '').lower()
    old_map = {lang_key(l): l for l in old}
    new_map = {lang_key(l): l for l in new}
    added = [l for k, l in new_map.items() if k not in old_map]
    removed = [l for k, l in old_map.items() if k not in new_map]
    changed = []
    for k in old_map:
        if k in new_map:
            old_l = old_map[k]
            new_l = new_map[k]
            diffs = {}
            for field in set(old_l.keys()).union(new_l.keys()):
                if old_l.get(field) != new_l.get(field):
                    diffs[field] = {'before': old_l.get(field), 'after': new_l.get(field)}
            if diffs:
                changed.append({'language': old_l['language'], 'diffs': diffs})
    return added, removed, changed

# 2. Fetch and parse Semgrep docs
def fetch_semgrep_docs():
    resp = requests.get(SEMGREP_DOCS_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Main language table
    table = soup.find('table')
    if not table:
        raise Exception('Could not find language table in docs')
    languages = []
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    for row in table.find_all('tr')[1:]:
        cells = row.find_all(['td', 'th'])
        if not cells or len(cells) < 2:
            continue
        lang_name = cells[0].get_text(strip=True)
        code_features = cells[1].get_text(" ", strip=True)
        maturity = 'GA' if 'Generally available' in code_features else cells[1].get_text(strip=True)
        # Dataflow analysis
        if 'Cross-file dataflow analysis' in code_features:
            dataflow = 'cross-file'
        elif 'Cross-function dataflow analysis' in code_features:
            dataflow = 'cross-function'
        else:
            dataflow = None
        # Number of Pro rules
        pro_rules_match = re.search(r'(\d+)\+ Pro rules', code_features)
        pro_rules = int(pro_rules_match.group(1)) if pro_rules_match else 0
        # Framework-specific control flow analysis
        framework_specific = 'Framework-specific control flow analysis' in code_features
        # SCA features (reachability, license, malicious dep)
        sca_features = cells[2].get_text(" ", strip=True) if len(cells) > 2 else ''
        reachability = 'Reachability analysis' in sca_features
        open_source_licenses = 'open source licenses' in sca_features
        malicious_deps = 'malicious dependencies' in sca_features
        # Save initial
        languages.append({
            'language': lang_name,
            'maturity': maturity,
            'dataflow': dataflow,
            'pro_rules': pro_rules,
            'framework_specific': framework_specific,
            'reachability': reachability,
            'open_source_licenses': open_source_licenses,
            'malicious_dependencies': malicious_deps,
            'package_managers': [],
            'lockfiles': [],
            'scan_without_lockfiles': False
        })
    # Parse package manager support table
    pm_table = None
    for t in soup.find_all('table'):
        if t.find('th') and 'Supported package managers' in t.get_text():
            pm_table = t
            break
    if pm_table:
        # First pass: collect all package managers and lockfiles per language
        language_pm_data = {}
        
        # Track the current primary language for follow-up rows
        current_primary_lang = None
        
        for row in pm_table.find_all('tr')[1:]:
            cells = row.find_all(['td', 'th'])
            if not cells or len(cells) < 2:
                continue
            
            lang_text = cells[0].get_text(strip=True)
            pm_text = cells[1].get_text(separator=' ', strip=True)
            lf_text = cells[2].get_text(separator=' ', strip=True) if len(cells) > 2 else ''
            
            # Determine target languages for this row
            target_languages = []
            
            # Check if this is a follow-up row for package managers
            known_package_managers = ['maven', 'gradle', 'npm', 'yarn', 'pnpm', 'pip', 'pipenv', 'poetry', 'uv', 'composer', 'cargo', 'nuget', 'rubygems', 'swiftpm', 'cocoapods']
            
            if (lang_text.lower() in known_package_managers or 
                any(pm in lang_text.lower() for pm in ['pipenv', 'poetry', 'yarn', 'pnpm', 'cocoapods'])):
                # This is a follow-up row with just package manager info
                if current_primary_lang:
                    # current_primary_lang can be a string or a list
                    if isinstance(current_primary_lang, list):
                        target_languages = current_primary_lang
                    else:
                        target_languages = [current_primary_lang]
                    # For these rows: Cell 0 = package manager name, Cell 1 = lockfile name
                    pm_text = lang_text  # The package manager name is in the "language" column
                    lf_text = cells[1].get_text(separator=' ', strip=True) if len(cells) > 1 else ''
            else:
                # This is a primary language row
                if 'javascript' in lang_text.lower() or 'typescript' in lang_text.lower():
                    # Handle "JavaScript or TypeScript" -> both JS and TS
                    target_languages = ['javascript', 'typescript']
                    current_primary_lang = ['javascript', 'typescript']  # Both for follow-ups
                elif lang_text.lower() == 'maven':
                    # Maven rows apply to Java and Kotlin
                    target_languages = ['java', 'kotlin']
                    current_primary_lang = None  # Maven is for multiple langs
                else:
                    # Regular language row
                    target_languages = [name.strip() for name in lang_text.replace(' or ', ',').replace('/', ',').split(',')]
                    if target_languages:
                        current_primary_lang = target_languages[0].lower()
            
            # Process each target language
            for lang_name in target_languages:
                normalized_lang = lang_name.lower().strip()
                
                # Initialize if not exists
                if normalized_lang not in language_pm_data:
                    language_pm_data[normalized_lang] = {
                        'package_managers': [],
                        'lockfiles': []
                    }
                
                # Add package manager (avoid duplicates)
                if pm_text and pm_text not in language_pm_data[normalized_lang]['package_managers']:
                    language_pm_data[normalized_lang]['package_managers'].append(pm_text)
                
                # Add lockfile (avoid duplicates)
                if lf_text and lf_text not in language_pm_data[normalized_lang]['lockfiles']:
                    language_pm_data[normalized_lang]['lockfiles'].append(lf_text)
        
        # Second pass: match collected data to our languages
        for l in languages:
            normalized_existing = l['language'].lower().strip()
            
            # Look for matches in our collected data
            for lang_key, data in language_pm_data.items():
                # Exact match or close match handling
                if (lang_key == normalized_existing or 
                    lang_key in normalized_existing or 
                    normalized_existing in lang_key):
                    
                    # Special handling for common ambiguous cases
                    if lang_key == 'java' and 'javascript' in normalized_existing:
                        continue  # Skip JavaScript when looking for Java
                    if 'javascript' in lang_key and normalized_existing == 'java':
                        continue  # Skip Java when looking for JavaScript
                    if 'typescript' in lang_key and normalized_existing == 'java':
                        continue  # Skip Java when looking for TypeScript
                    
                    l['package_managers'] = data['package_managers']
                    l['lockfiles'] = data['lockfiles']
                    break
    # Parse feature support table for scan-without-lockfiles
    feature_table = None
    for t in soup.find_all('table'):
        if t.find('th') and 'Reachability' in t.get_text() and 'Scan without lockfiles' in t.get_text():
            feature_table = t
            break
    if feature_table:
        for row in feature_table.find_all('tr')[1:]:
            cells = row.find_all(['td', 'th'])
            if not cells or len(cells) < 2:
                continue
            
            lang_text = cells[0].get_text(strip=True)
            
            # Handle potential multiple languages in a single cell
            lang_names = [name.strip() for name in lang_text.replace('/', ',').split(',')]
            
            # Check for scan-without-lockfiles support
            scan_without = '✅' in cells[1].get_text() or 'yes' in cells[1].get_text().lower()
            
            # Match languages precisely
            for lang_name in lang_names:
                normalized_lang = lang_name.lower().strip()
                
                for l in languages:
                    normalized_existing = l['language'].lower().strip()
                    
                    # Exact match or close match handling
                    if (normalized_lang == normalized_existing or 
                        normalized_lang in normalized_existing or 
                        normalized_existing in normalized_lang):
                        
                        # Special handling for common ambiguous cases
                        if normalized_lang == 'java' and 'javascript' in normalized_existing:
                            continue  # Skip JavaScript when looking for Java
                        if normalized_lang == 'javascript' and normalized_existing == 'java':
                            continue  # Skip Java when looking for JavaScript
                        
                        l['scan_without_lockfiles'] = scan_without
                        break
    return languages

# 3. Enrich local JSON
def enrich_languages():
    local_langs = load_languages()
    old_langs = copy.deepcopy(local_langs)
    docs_langs = fetch_semgrep_docs()
    for doc_lang in docs_langs:
        doc_name = doc_lang['language'].replace('/', '').replace(' ', '').lower()
        found = False
        for local in local_langs:
            local_name = local['language'].replace('/', '').replace(' ', '').lower()
            if doc_name == local_name:
                local['semgrep_docs'] = doc_lang
                found = True
                break
        if not found:
            local_langs.append({
                'language': doc_lang['language'],
                'maturity': doc_lang['maturity'],
                'milan_comments': '',
                'semgrep_docs': doc_lang
            })
    save_languages(local_langs)
    print('languages.json enriched with Semgrep docs data.')
    # Compare and print changes
    added, removed, changed = compare_languages(old_langs, local_langs)
    print("\n=== Languages DB Changes ===")
    if added:
        print(f"Added languages: {[l['language'] for l in added]}")
    if removed:
        print(f"Removed languages: {[l['language'] for l in removed]}")
    if changed:
        print("Modified languages:")
        for c in changed:
            print(f"- {c['language']}")
            for field, diff in c['diffs'].items():
                print(f"    {field}: {diff['before']} -> {diff['after']}")
    if not (added or removed or changed):
        print("No changes detected.")

if __name__ == '__main__':
    enrich_languages() 