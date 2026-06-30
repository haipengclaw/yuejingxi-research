#!/usr/bin/env python3
"""Run one job end-to-end: search -> extract -> generate reports -> validate.

Usage:
  python3 scripts/run_job.py --city 苏州 --template benbang
"""
import argparse, subprocess, sys, os

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'


def run(cmd):
    print(f'\n$ {cmd}')
    rc = subprocess.call(cmd, shell=True, cwd=REPO)
    if rc != 0:
        print(f'Command failed with rc={rc}: {cmd}')
        sys.exit(rc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--city', required=True)
    parser.add_argument('--template', required=True)
    parser.add_argument('--sleep', type=int, default=7, help='Seconds between shop extractions')
    parser.add_argument('--skip-search', action='store_true')
    parser.add_argument('--skip-extract', action='store_true')
    parser.add_argument('--skip-generate', action='store_true')
    args = parser.parse_args()

    if not args.skip_search:
        run(f'python3 scripts/search_city_shops.py --city {args.city} --template {args.template}')
    if not args.skip_extract:
        run(f'python3 scripts/batch_extract_city.py --city {args.city} --template {args.template} --sleep {args.sleep}')
    run(f'python3 scripts/filter_search_results.py --city {args.city} --template {args.template}')
    if not args.skip_generate:
        run(f'python3 scripts/generate_city_reports.py --city {args.city} --template {args.template}')

    print(f'\n✅ Job completed: {args.city} · {args.template}')


if __name__ == '__main__':
    main()
