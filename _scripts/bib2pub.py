#!/usr/bin/env python3
"""
Convert bib.bib → 50_publications.markdown.

Run manually:
    python3 _scripts/bib2pub.py

Or install the git hook so it runs automatically on commit:
    python3 _scripts/bib2pub.py --install-hook

Adding a new paper:
  1. Add the entry to bib.bib (standard @article / @inproceedings / @phdthesis).
  2. Add its URL to KNOWN_URLS below (keyed by bib key), OR add a `url = {https://...}`
     field directly in the bib entry — the script will pick it up automatically.
  3. Commit; the hook regenerates the page.
"""

import re
import sys
import os
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Keys to skip entirely (deliverables, incomplete entries)
SKIP_KEYS = {'castaman2020h2020', 'nicola2021drapebot', 'nicolahuman'}

# Keys that are theses (not standard @phdthesis/@mastersthesis in this bib)
PHD_KEYS    = {'franceschi2024human'}
MASTER_KEYS = {'bonini2015modeling'}

# (bib_key, entry_type) → (paper_url, free_pdf_url or None)
# entry_type is lowercase: 'article', 'inproceedings', etc.
# Use (key, type) tuples when the same key is reused for two entries (bib bug).
KNOWN_URLS = {
    # --- journals ---
    ('villagrossi2025efficient',    'article'):       ('https://www.sciencedirect.com/science/article/pii/S0278612525002729', None),
    ('franceschi2024design',        'article'):       ('https://ieeexplore.ieee.org/abstract/document/10606422', None),
    ('franceschi2023human',         'article'):       ('https://ieeexplore.ieee.org/abstract/document/10275780', None),
    ('franceschi2023identification','article'):       ('https://www.sciencedirect.com/science/article/pii/S0957415823000429', None),
    ('franceschi2022optimal',       'article'):       ('https://www.sciencedirect.com/science/article/pii/S0736584522000886', None),
    ('franceschi2022framework',     'article'):       ('https://www.tandfonline.com/doi/abs/10.1080/0951192X.2021.1992666',
                                                       'https://www.researchgate.net/profile/Paolo-Franceschi-2/publication/355840136_A_framework_for_cyber-physical_production_system_management_and_digital_twin_feedback_monitoring_for_fast_failure_recovery/links/6214aec208bee946f395d60a/A-framework-for-cyber-physical-production-system-management-and-digital-twin-feedback-monitoring-for-fast-failure-recovery.pdf'),
    ('franceschi2020precise',       'article'):       ('https://ieeexplore.ieee.org/abstract/document/9285243', None),
    ('roveda2020model',             'article'):       ('https://link.springer.com/article/10.1007/s10846-020-01183-3', None),
    # --- conferences ---
    ('franceschi2023human',         'inproceedings'): ('https://ieeexplore.ieee.org/abstract/document/10202313', None),
    ('franceschi2023learning',      'inproceedings'): ('https://ieeexplore.ieee.org/abstract/document/10342014', None),
    ('franceschi2022adaptive',      'inproceedings'): ('https://ieeexplore.ieee.org/abstract/document/9811853',
                                                       'https://www.researchgate.net/profile/Paolo-Franceschi-2/publication/361254590_Adaptive_Impedance_Controller_for_Human-Robot_Arbitration_based_on_Cooperative_Differential_Game_Theory/links/62a6f025c660ab61f877f89a/Adaptive-Impedance-Controller-for-Human-Robot-Arbitration-based-on-Cooperative-Differential-Game-Theory.pdf'),
    ('franceschi2022inverse',       'inproceedings'): ('https://ieeexplore.ieee.org/document/9921553', None),
    ('franceschi2021combining',     'inproceedings'): ('https://www.spiedigitallibrary.org/conference-proceedings-of-spie/11785/1178510/Combining-visual-and-force-feedback-for-the-precise-robotic-manipulation/10.1117/12.2595613.short#_=_', None),
    ('roveda2020control',           'inproceedings'): ('https://ieeexplore.ieee.org/abstract/document/9197141',
                                                       'https://ipg.idsia.ch/preprints/Roveda2020f.pdf'),
    ('roveda2018human',             'inproceedings'): ('https://ieeexplore.ieee.org/abstract/document/8616062', None),
    # --- theses ---
    ('franceschi2024human',         'article'):       ('https://www.researchgate.net/publication/386245137_Human_modeling_Game_Theory_and_Role_Arbitration_for_physical_Human-Robot_Interaction', None),
    ('bonini2015modeling',          'article'):       ('https://www.politesi.polimi.it/handle/10589/133799', None),
}

# Preprint links to attach alongside published papers  (bib_key → arXiv URL)
PREPRINT_LINKS = {
    'franceschi2023learning': 'https://arxiv.org/abs/2307.10743',
    '10406758':               'https://arxiv.org/abs/2307.10739',
}


# ---------------------------------------------------------------------------
# LaTeX → unicode cleanup
# ---------------------------------------------------------------------------

_LATEX = [
    (r"{\`o}", "ò"), (r"{\'o}", "ó"), (r"{\`a}", "à"), (r"{\'a}", "á"),
    (r"{\`e}", "è"), (r"{\'e}", "é"), (r"{\`i}", "ì"), (r"{\'i}", "í"),
    (r"{\`u}", "ù"), (r"{\'u}", "ú"), (r"{\`A}", "À"), (r"{\`E}", "È"),
    (r"{\`}", "`"),  (r"\&", "&"),    (r"\ ", " "),
]

def clean(s):
    for k, v in _LATEX:
        s = s.replace(k, v)
    s = re.sub(r'[{}\\]', '', s)
    s = s.replace('--', '–')   # en-dash
    return s.strip()


def title_case_name(name):
    """Normalise ALL-CAPS names like 'TOMMASO BONINI' → 'Tommaso Bonini'."""
    if name == name.upper() and len(name) > 2:
        return name.title()
    return name


# ---------------------------------------------------------------------------
# BibTeX parser
# ---------------------------------------------------------------------------

def parse_bib(path):
    text = Path(path).read_text(encoding='utf-8')
    entries = []
    i = 0
    while i < len(text):
        at = text.find('@', i)
        if at == -1:
            break
        brace = text.find('{', at)
        if brace == -1:
            break
        etype = text[at+1:brace].strip().lower()
        if etype in ('comment', 'string', 'preamble'):
            i = brace + 1
            continue
        comma = text.find(',', brace)
        if comma == -1:
            break
        key = text[brace+1:comma].strip()
        # find matching closing brace
        depth, j = 1, brace + 1
        while j < len(text) and depth > 0:
            if text[j] == '{':   depth += 1
            elif text[j] == '}': depth -= 1
            j += 1
        body = text[comma+1:j-1].strip()
        fields = {'_type': etype, '_key': key}
        # parse fields
        pos = 0
        while pos < len(body):
            while pos < len(body) and body[pos] in ' \t\n\r':
                pos += 1
            if pos >= len(body):
                break
            eq = body.find('=', pos)
            if eq == -1:
                break
            fname = body[pos:eq].strip().lower()
            pos = eq + 1
            while pos < len(body) and body[pos] in ' \t\n\r':
                pos += 1
            if pos >= len(body):
                break
            if body[pos] == '{':
                depth2, start = 1, pos + 1
                pos += 1
                while pos < len(body) and depth2 > 0:
                    if body[pos] == '{':   depth2 += 1
                    elif body[pos] == '}': depth2 -= 1
                    pos += 1
                value = body[start:pos-1]
            elif body[pos] == '"':
                start = pos + 1
                pos += 1
                while pos < len(body) and body[pos] != '"':
                    pos += 1
                value = body[start:pos]
                pos += 1
            else:
                start = pos
                while pos < len(body) and body[pos] not in ',\n':
                    pos += 1
                value = body[start:pos].strip()
            fields[fname] = value
            while pos < len(body) and body[pos] in ' \t\n\r,':
                pos += 1
        entries.append(fields)
        i = j
    return entries


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_authors(s):
    parts = re.split(r'\s+and\s+', s, flags=re.IGNORECASE)
    names = []
    for p in parts:
        p = p.strip()
        if ',' in p:
            last, first = p.split(',', 1)
            first = title_case_name(clean(first.strip()))
            last  = title_case_name(clean(last.strip()))
            # Expand single initials: "P" → keep as-is only if followed by more names;
            # expand known abbreviations when they unambiguously match Paolo Franceschi.
            name = f"{first} {last}"
        else:
            name = title_case_name(clean(p))
        if re.search(r'\bFranceschi\b', name, re.IGNORECASE):
            name = f"**{name}**"
        names.append(name)
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ', '.join(names[:-1]) + f', and {names[-1]}'


def get_url(e):
    key, etype = e['_key'], e['_type']
    # (key, type) lookup first (handles duplicate keys)
    if (key, etype) in KNOWN_URLS:
        return KNOWN_URLS[(key, etype)][0]
    # fall back to plain key
    for (k, t), (url, _) in KNOWN_URLS.items():
        if k == key:
            return url
    # bib url field
    if 'url' in e:
        return e['url']
    # construct from doi
    if 'doi' in e:
        return f"https://doi.org/{e['doi']}"
    return None


def get_pdf(e):
    key, etype = e['_key'], e['_type']
    if (key, etype) in KNOWN_URLS:
        return KNOWN_URLS[(key, etype)][1]
    for (k, t), (_, pdf) in KNOWN_URLS.items():
        if k == key and pdf:
            return pdf
    return None


def venue(e):
    etype = e['_type']
    if etype == 'inproceedings':
        v = clean(e.get('booktitle', ''))
        v = re.sub(r'^\d{4}\s+', '', v)   # strip leading year
        return v
    j = clean(e.get('journal', e.get('publisher', '')))
    return j


def render_entry(e):
    title   = clean(e.get('title', ''))
    authors = format_authors(e.get('author', ''))
    year    = e.get('year', '')
    url     = get_url(e)
    pdf     = get_pdf(e)
    pre     = PREPRINT_LINKS.get(e['_key'])
    ven     = venue(e)

    title_part = f"[*{title}*]({url})" if url else f"*{title}*"
    if pdf:
        title_part += f" - [[pdf]]({pdf})"
    if pre:
        title_part += f" - [[preprint]]({pre})"

    return (
        f"{title_part}  \n"
        f"*{authors}*  \n"
        f"{ven}, {year}.  \n"
    )


# ---------------------------------------------------------------------------
# Classify entries
# ---------------------------------------------------------------------------

def classify(e):
    key   = e['_key']
    etype = e['_type']
    if key in SKIP_KEYS:
        return None
    if key in PHD_KEYS:
        return 'phd'
    if key in MASTER_KEYS:
        return 'master'
    if etype == 'inproceedings':
        return 'conference'
    if etype == 'article':
        journal = e.get('journal', '').lower()
        return 'preprint' if 'arxiv' in journal else 'journal'
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

HEADER = """\
---
layout: page
title: Publications
permalink: /publications/
---
"""

def generate():
    entries = parse_bib(ROOT / 'bib.bib')

    buckets = {'journal': [], 'conference': [], 'preprint': [], 'phd': [], 'master': []}
    for e in entries:
        cat = classify(e)
        if cat:
            buckets[cat].append(e)

    key_year = lambda e: int(e.get('year', '0'))
    for cat in ('journal', 'conference', 'preprint'):
        buckets[cat].sort(key=key_year, reverse=True)

    out = [HEADER]

    out += ["## Journal Publications", "___", ""]
    for e in buckets['journal']:
        out.append(render_entry(e))

    out += ["", "## Conference Publications", "___", ""]
    for e in buckets['conference']:
        out.append(render_entry(e))

    if buckets['preprint']:
        out += ["", "## Preprints", "___", ""]
        for e in buckets['preprint']:
            out.append(render_entry(e))

    if buckets['phd']:
        out += ["", "### Ph.D. thesis", ""]
        for e in buckets['phd']:
            out.append(render_entry(e))

    if buckets['master']:
        out += ["", "### Master thesis", ""]
        for e in buckets['master']:
            out.append(render_entry(e))

    dest = ROOT / '50_publications.markdown'
    dest.write_text('\n'.join(out), encoding='utf-8')
    print(
        f"Generated {dest.name}  "
        f"({len(buckets['journal'])} journals, "
        f"{len(buckets['conference'])} conferences, "
        f"{len(buckets['preprint'])} preprints, "
        f"{len(buckets['phd']) + len(buckets['master'])} theses)"
    )


HOOK_SCRIPT = """\
#!/bin/bash
# Auto-regenerate 50_publications.markdown when bib.bib is staged.
if git diff --cached --name-only | grep -q 'bib\\.bib'; then
  echo "[hook] bib.bib changed — regenerating publications page..."
  python3 _scripts/bib2pub.py
  git add 50_publications.markdown
fi
"""

def install_hook():
    hook_path = ROOT / '.git' / 'hooks' / 'pre-commit'
    existing = hook_path.read_text() if hook_path.exists() else ''
    if 'bib2pub' in existing:
        print("Hook already installed.")
        return
    if existing and not existing.startswith('#!/bin/bash'):
        print(f"Existing pre-commit hook found at {hook_path}; not overwriting.")
        print("Add this manually:\n" + HOOK_SCRIPT)
        return
    hook_path.write_text((existing + '\n' + HOOK_SCRIPT).strip() + '\n')
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Installed pre-commit hook at {hook_path}")


if __name__ == '__main__':
    if '--install-hook' in sys.argv:
        install_hook()
    else:
        generate()
