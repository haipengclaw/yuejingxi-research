#!/usr/bin/env python3
"""Batch-extract Dianping shop details (text + dish pairs) for a city using browse tool.

Usage:
  python3 scripts/batch_extract_city.py --city 苏州 --template benbang
"""
import argparse, json, os, sys, time

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'
with open(os.path.join(REPO, 'data/city_config.json')) as f:
    CONFIG = json.load(f)

sys.path.insert(0, os.path.dirname(__file__))
from browse_client import extract_shop_details, cookie_import


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--city', required=True)
    parser.add_argument('--template', required=True)
    parser.add_argument('--sleep', type=int, default=7, help='Seconds between shops')
    args = parser.parse_args()

    city_name = args.city
    template_key = args.template

    city_info = next((c for c in CONFIG['cities'] if c['name'] == city_name), None)
    if not city_info:
        print(f'Unknown city: {city_name}')
        sys.exit(1)

    pinyin = city_info['pinyin']
    data_path = os.path.join(REPO, 'data', 'cities', f'{pinyin}_{template_key}_search_results.json')
    if not os.path.exists(data_path):
        print(f'Search data not found: {data_path}')
        sys.exit(1)

    with open(data_path) as f:
        data = json.load(f)

    shop_ids = set()
    for cat, shops in data.items():
        for name, sid in shops:
            shop_ids.add(sid)
    shop_ids = list(shop_ids)
    print(f'\n=== {city_name} · {template_key}: {len(shop_ids)} shops to extract ===\n')

    out_dir = os.path.join('/tmp', 'shops', pinyin)
    os.makedirs(out_dir, exist_ok=True)

    cookie_path = os.path.join(REPO, CONFIG['dianping']['cookies_file'])
    cookie_import(cookie_path)

    for i, shop_id in enumerate(shop_ids):
        print(f'[{i+1}/{len(shop_ids)}] {shop_id}', end=' ')
        try:
            body_text, paired = extract_shop_details(shop_id)

            text_path = os.path.join(out_dir, f't_{shop_id}.txt')
            with open(text_path, 'w') as f:
                f.write(body_text)

            paired_path = os.path.join(out_dir, f'p_{shop_id}.json')
            with open(paired_path, 'w') as f:
                json.dump(paired, f, ensure_ascii=False, indent=2)

            print(f'- {paired.get("count", 0)} dishes')
        except RuntimeError as e:
            print(f'\n  🛑 {e}')
            sys.exit(1)
        except Exception as e:
            print(f'\n  ❌ error: {e}')

        if i < len(shop_ids) - 1:
            time.sleep(args.sleep)

    print(f'\nDone. Output: {out_dir}')


if __name__ == '__main__':
    main()
