#!/usr/bin/env python3
"""Run all configured jobs sequentially. Resumes if interrupted.

Usage:
  python3 scripts/run_all_jobs.py [--sleep 7]
"""
import argparse, json, os, subprocess, sys

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'
with open(os.path.join(REPO, 'data/city_config.json')) as f:
    CONFIG = json.load(f)

PROGRESS_FILE = os.path.join(REPO, 'data', 'run_all_progress.json')


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'done': []}


def save_progress(done):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'done': done}, f, ensure_ascii=False, indent=2)


def run_job(city, template, sleep):
    cmd = f'python3 scripts/run_job.py --city {city} --template {template} --sleep {sleep}'
    print(f'\n>>> {cmd}')
    rc = subprocess.call(cmd, shell=True, cwd=REPO)
    return rc == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sleep', type=int, default=7)
    parser.add_argument('--reset', action='store_true', help='Clear progress and restart')
    args = parser.parse_args()

    progress = load_progress()
    done = [] if args.reset else progress.get('done', [])

    jobs = CONFIG['jobs']
    for i, job in enumerate(jobs):
        key = f"{job['city']}-{job['template']}"
        if key in done:
            print(f'  ⏭️  skipping {key} (already done)')
            continue
        print(f'\n=== [{i+1}/{len(jobs)}] {key} ===')
        ok = run_job(job['city'], job['template'], args.sleep)
        if ok:
            done.append(key)
            save_progress(done)
        else:
            print(f'  ❌ {key} failed, stopping')
            sys.exit(1)

    print('\n✅ All jobs completed')
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)


if __name__ == '__main__':
    main()
