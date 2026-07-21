"""
AMXL Canada DS — Dashboard Data Refresh
========================================
Run this script weekly to pull fresh data from QuickSight
and push it to GitHub so the cloud dashboard updates automatically.

Usage:
    uv run --with openpyxl --python 3.12 python refresh_dashboard.py
"""
import subprocess, sys, shutil, os
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
GIT        = r'C:\Users\wennouni\AppData\Local\Programs\Git\bin\git.exe'
TMP        = Path(r'C:\Users\wennouni\.aki\tmp')
CLOUD_REPO = Path(r'C:\Users\wennouni\.aki\tmp\amxl_cloud')
CLOUD_DATA = CLOUD_REPO / 'data'

QUICKSUITE_SOURCES = {
    'service_time_station_weekly.csv': {
        'account': 'amxl-bi-quicksight',
        'url': 'https://us-east-1.quicksight.aws.amazon.com/sn/account/amxl-bi-quicksight/dashboards/825dd7e0-e45b-42ec-90fa-76a02c786b10/sheets/825dd7e0-e45b-42ec-90fa-76a02c786b10_affd95e9-c26c-48a1-ab2e-3c15c23aa34c',
        'label': 'Service Time (DD Service Time sheet)',
    },
    'star_rating_weekly.csv': {
        'account': 'amxl-bi-quicksight',
        'url': 'https://us-east-1.quicksight.aws.amazon.com/sn/account/amxl-bi-quicksight/dashboards/0f883032-b23d-4c41-ba76-5131eccbd743/sheets/0f883032-b23d-4c41-ba76-5131eccbd743_8cda3c4c-82c7-451a-b46e-a9b8e109d2bb',
        'label': 'Star Rating Trend sheet',
    },
    'iaq_urr_raw.csv': {
        'account': 'amazonbi',
        'url': 'https://us-east-1.quicksight.aws.amazon.com/sn/account/amazonbi/dashboards/90494bd1-014f-4a3d-9587-6b48420361b2/sheets/90494bd1-014f-4a3d-9587-6b48420361b2_344be1f8-f258-4fa7-8766-9222234477a0',
        'label': 'IAQ/URR by Station sheet',
    },
    'star_nfpr_raw.csv': {
        'account': 'amxl-bi-quicksight',
        'url': 'https://us-east-1.quicksight.aws.amazon.com/sn/account/amxl-bi-quicksight/dashboards/0f883032-b23d-4c41-ba76-5131eccbd743/sheets/0f883032-b23d-4c41-ba76-5131eccbd743_c3f379a7-36a9-49f6-bf1a-7db839dc3ad9',
        'label': 'Customer Feedback (NFPR Station sheet)',
    },
    'mom_service_time_raw.csv': {
        'account': 'amxl-bi-quicksight',
        'url': 'https://us-east-1.quicksight.aws.amazon.com/sn/account/amxl-bi-quicksight/dashboards/0f883032-b23d-4c41-ba76-5131eccbd743/sheets/0f883032-b23d-4c41-ba76-5131eccbd743_c34fb804-8a1c-4720-85b3-570354e7936d',
        'label': 'MoM Service Time (ROC/DDU by site and month)',
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def git(*args):
    result = run([GIT] + list(args), cwd=str(CLOUD_REPO))
    if result.returncode != 0:
        print(f'  git error: {result.stderr.strip()}')
    return result

def step(msg):
    print(f'\n{"─"*60}\n{msg}')

# ── 1. Extract from QuickSight ────────────────────────────────────────────────
step('STEP 1 — Pulling fresh data from QuickSight')
failed = []
for filename, src in QUICKSUITE_SOURCES.items():
    out_path = TMP / filename
    print(f'\n  [{src["label"]}]')
    result = run([
        'aki', 'ext', 'quicksuite', 'get-visual-data',
        '--account', src['account'],
        '--format', 'csv',
        '-o', str(out_path),
        src['url']
    ])
    if result.returncode == 0 and out_path.exists():
        size = out_path.stat().st_size
        print(f'  ✓ {filename} ({size:,} bytes)')
    else:
        print(f'  ✗ FAILED — {result.stderr.strip()[:120]}')
        failed.append(filename)

if failed:
    print(f'\n⚠ {len(failed)} source(s) failed: {", ".join(failed)}')
    print('  Continuing with files that succeeded...')

# ── 2. Copy to cloud data folder ──────────────────────────────────────────────
step('STEP 2 — Copying CSVs to cloud data folder')
copied = []
for filename in QUICKSUITE_SOURCES:
    src_file = TMP / filename
    dst_file = CLOUD_DATA / filename
    if src_file.exists():
        shutil.copy2(src_file, dst_file)
        print(f'  ✓ {filename}')
        copied.append(filename)
    else:
        print(f'  - {filename} (not refreshed, keeping existing)')

if not copied:
    print('\nNo files to push. Exiting.')
    sys.exit(1)

# ── 3. Git commit and push ─────────────────────────────────────────────────────
step('STEP 3 — Pushing to GitHub')
week = datetime.now().strftime('W%V %Y')
git('add', 'data/')
status = git('status', '--short')
if not status.stdout.strip():
    print('  No changes detected — data is already up to date.')
    sys.exit(0)
print(f'  Changes:\n{status.stdout}')
git('commit', '-m', f'Data refresh {week} — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
push = git('push')
if push.returncode == 0:
    print(f'\n✅ Done! Cloud dashboard will update in ~60 seconds.')
    print(f'   URL: https://amxl-canada-dashboard-eamgy5ciapkq6dy5kjdm7f.streamlit.app')
else:
    print(f'\n✗ Push failed: {push.stderr.strip()}')
