import json
import requests
from bs4 import BeautifulSoup
import os
import copy
import re

SCMS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scms.json')
SEMGREP_SCMS_URL = 'https://semgrep.dev/docs/getting-started/scm-support'

def load_scms():
    with open(SCMS_JSON) as f:
        return json.load(f)

def save_scms(scms):
    with open(SCMS_JSON, 'w') as f:
        json.dump(scms, f, indent=2)

def compare_scms(old, new):
    def scm_key(scm):
        return scm['scm'].lower()
    old_map = {scm_key(s): s for s in old}
    new_map = {scm_key(s): s for s in new}
    added = [s for k, s in new_map.items() if k not in old_map]
    removed = [s for k, s in old_map.items() if k not in new_map]
    changed = []
    for k in old_map:
        if k in new_map:
            old_s = old_map[k]
            new_s = new_map[k]
            diffs = {}
            # Compare plans
            if set(old_s.get('plans', [])) != set(new_s.get('plans', [])):
                diffs['plans'] = {'before': old_s.get('plans', []), 'after': new_s.get('plans', [])}
            # Compare unsupported_features_by_plan
            old_uf = old_s.get('unsupported_features_by_plan', {})
            new_uf = new_s.get('unsupported_features_by_plan', {})
            all_plans = set(old_uf.keys()).union(new_uf.keys())
            plan_diffs = {}
            for plan in all_plans:
                if old_uf.get(plan) != new_uf.get(plan):
                    plan_diffs[plan] = {'before': old_uf.get(plan), 'after': new_uf.get(plan)}
            if plan_diffs:
                diffs['unsupported_features_by_plan'] = plan_diffs
            if diffs:
                changed.append({'scm': old_s['scm'], 'diffs': diffs})
    return added, removed, changed

def split_features(uf):
    # If already a list, return as is
    if isinstance(uf, list):
        return uf
    # If empty or dash, return empty list
    if not uf or uf.strip() == '-' or uf.strip() == '—':
        return []
    # Expanded known features from Semgrep docs
    known = [
        'Semgrep Assistant',
        'Semgrep Managed Scans',
        'Pull request comments',
        'Query console',
        'Diff-aware scans',
        'Sending findings to Semgrep AppSec Platform',
        'Default branch identification',
        'Auto PRs for Supply Chain findings',
        'Generic secrets (requires Semgrep Assistant)',
        'Auto PRs for Supply Chain findings',
        'Semgrep Managed Scans*',
        'Semgrep Assistant†',
        'Semgrep Managed Scan†',
        'Diff-aware scans require Bitbucket Data Center version 8.8 or later.',
        'Generic secrets (requires Semgrep Assistant)',
        'Semgrep Managed Scans*',
        'Query console',
        'Auto PRs for Supply Chain findings',
        'Sending findings to Semgrep AppSec Platform',
        'Default branch identification',
        'Generic secrets (requires Semgrep Assistant)',
    ]
    # Try to split by known features
    features = []
    s = uf
    for feat in known:
        s = s.replace(feat, f'|{feat}')
    for part in s.split('|'):
        part = part.strip()
        if part:
            features.append(part)
    # Only use regex fallback if no features found
    if len(features) == 0:
        features = re.split(r'(?<!^)(?=[A-Z])', uf)
        features = [f.strip() for f in features if f.strip()]
    return features

def fetch_semgrep_scms():
    resp = requests.get(SEMGREP_SCMS_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Find the table with SCM plans and unsupported features
    table = soup.find('table')
    if not table:
        raise Exception('Could not find SCM table in docs')
    scms = []
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    for row in table.find_all('tr')[1:]:
        cells = row.find_all(['td', 'th'])
        if not cells or len(cells) < 2:
            continue
        plan = cells[0].get_text(strip=True)
        unsupported = cells[1].get_text(strip=True)
        # Try to extract SCM name from plan (e.g., "GitHub Free", "Azure DevOps Cloud")
        plan_parts = plan.split()
        if not plan_parts:
            continue
        if plan_parts[0] in ["GitHub", "GitLab", "Bitbucket", "Azure"]:
            if plan_parts[0] == "Azure":
                scm_name = "Azure DevOps"
            elif plan_parts[0] == "Bitbucket":
                scm_name = "Bitbucket"
            elif plan_parts[0] == "GitHub":
                scm_name = "GitHub"
            elif plan_parts[0] == "GitLab":
                scm_name = "GitLab"
            else:
                scm_name = plan_parts[0]
        else:
            scm_name = plan_parts[0]
        # Store unsupported_features as a list
        unsupported_list = split_features(unsupported)
        scms.append({
            'scm': scm_name,
            'plan': plan,
            'unsupported_features': unsupported_list,
        })
    return scms

def enrich_scms():
    local_scms = load_scms()
    old_scms = copy.deepcopy(local_scms)
    docs_scms = fetch_semgrep_scms()
    all_scm_names = set([scm['scm'] for scm in docs_scms])
    enriched = []
    for scm_name in sorted(all_scm_names):
        plans = [scm for scm in docs_scms if scm['scm'] == scm_name]
        enriched.append({
            'scm': scm_name,
            'plans': [p['plan'] for p in plans],
            'unsupported_features_by_plan': {p['plan']: p['unsupported_features'] for p in plans},
        })
    save_scms(enriched)
    print('scms.json enriched with Semgrep docs data.')
    # Compare and print changes
    added, removed, changed = compare_scms(old_scms, enriched)
    print("\n=== SCMs DB Changes ===")
    if added:
        print(f"Added SCMs: {[s['scm'] for s in added]}")
    if removed:
        print(f"Removed SCMs: {[s['scm'] for s in removed]}")
    if changed:
        print("Modified SCMs:")
        for c in changed:
            print(f"- {c['scm']}")
            for field, diff in c['diffs'].items():
                if field == 'unsupported_features_by_plan':
                    print(f"    {field}:")
                    for plan, pdiff in diff.items():
                        print(f"      {plan}: {pdiff['before']} -> {pdiff['after']}")
                else:
                    print(f"    {field}: {diff['before']} -> {diff['after']}")
    if not (added or removed or changed):
        print("No changes detected.")

if __name__ == '__main__':
    enrich_scms() 