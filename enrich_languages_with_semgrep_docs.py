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
        for row in pm_table.find_all('tr')[1:]:
            cells = row.find_all(['td', 'th'])
            if not cells or len(cells) < 2:
                continue
            lang = cells[0].get_text(strip=True)
            managers = [m.strip() for m in cells[1].get_text(',').split(',') if m.strip()]
            lockfiles = [l.strip() for l in cells[2].get_text(',').split(',') if l.strip()] if len(cells) > 2 else []
            for l in languages:
                if l['language'].lower() in lang.lower() or lang.lower() in l['language'].lower():
                    l['package_managers'] = managers
                    l['lockfiles'] = lockfiles
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
            lang = cells[0].get_text(strip=True)
            scan_without = '✅' in cells[1].get_text() or 'yes' in cells[1].get_text().lower()
            for l in languages:
                if l['language'].lower() in lang.lower() or lang.lower() in l['language'].lower():
                    l['scan_without_lockfiles'] = scan_without
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