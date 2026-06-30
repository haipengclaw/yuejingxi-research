#!/usr/bin/env python3
"""Validate data quality for generated city reports."""
import json, os, sys
from collections import defaultdict

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'
with open(os.path.join(REPO, 'data/city_config.json')) as f:
    CONFIG = json.load(f)

sys.path.insert(0, os.path.join(REPO, 'scripts'))
from report_utils import find_paired, get_shop_info, tmp_shop_dir


def validate_city_template(city_name, template_key):
    city_info = next((c for c in CONFIG['cities'] if c['name'] == city_name), None)
    if not city_info:
        return None
    pinyin = city_info['pinyin']
    template = CONFIG['templates'][template_key]

    data_path = os.path.join(REPO, 'data', 'cities', f'{pinyin}_{template_key}_search_results.json')
    if not os.path.exists(data_path):
        return {
            'city': city_name,
            'template': template_key,
            'cuisine': template['cuisine_name'],
            'error': 'search results not found'
        }

    with open(data_path) as f:
        data = json.load(f)

    all_shops = []
    dupes = []
    seen_ids = {}
    for cat, shops in data.items():
        for name, sid in shops:
            all_shops.append((name, sid, cat))
            if sid in seen_ids:
                dupes.append((sid, name, seen_ids[sid], cat))
            else:
                seen_ids[sid] = cat

    missing_rating = 0
    missing_price = 0
    missing_dishes = 0
    low_image = 0
    missing_text = 0
    total = len(all_shops)

    for name, sid, cat in all_shops:
        info = get_shop_info(sid, name, city_name)
        paired = find_paired(sid, pinyin)

        text_path = os.path.join(tmp_shop_dir(pinyin), f't_{sid}.txt')
        if not os.path.exists(text_path):
            missing_text += 1

        if not info.get('rating'):
            missing_rating += 1
        if not info.get('price'):
            missing_price += 1

        dishes = paired.get('paired', []) if paired else []
        if not dishes:
            missing_dishes += 1
        elif len(dishes) < 3:
            low_image += 1

    def pct(n):
        return round(n / total * 100, 1) if total else 0

    return {
        'city': city_name,
        'template': template_key,
        'cuisine': template['cuisine_name'],
        'total': total,
        'missing_rating': (missing_rating, pct(missing_rating)),
        'missing_price': (missing_price, pct(missing_price)),
        'missing_dishes': (missing_dishes, pct(missing_dishes)),
        'missing_text': (missing_text, pct(missing_text)),
        'low_image': (low_image, pct(low_image)),
        'duplicates': dupes,
        'categories': {k: len(v) for k, v in data.items()}
    }


def status(pct, threshold):
    return '✅' if pct <= threshold else '⚠️'


def main():
    results = []
    for job in CONFIG['jobs']:
        r = validate_city_template(job['city'], job['template'])
        if r:
            results.append(r)

    lines = ['# 数据质量校验报告\n']
    lines.append(f'生成日期：{CONFIG["date"][:4]}-{CONFIG["date"][4:6]}-{CONFIG["date"][6:]}\n')
    lines.append(f'校验任务数：{len(results)}\n\n')

    val = CONFIG['validation']

    for r in results:
        if 'error' in r:
            lines.append(f'## {r["city"]} · {r["cuisine"]}')
            lines.append(f'❌ {r["error"]}\n')
            continue

        lines.append(f'## {r["city"]} · {r["cuisine"]}')
        lines.append(f'- 总门店数：{r["total"]}')
        lines.append(f'- 缺失评分：{r["missing_rating"][0]} ({r["missing_rating"][1]}%) {status(r["missing_rating"][1], val["max_missing_rating"]*100)}')
        lines.append(f'- 缺失价格：{r["missing_price"][0]} ({r["missing_price"][1]}%) {status(r["missing_price"][1], val["max_missing_price"]*100)}')
        lines.append(f'- 缺失菜品：{r["missing_dishes"][0]} ({r["missing_dishes"][1]}%) {status(r["missing_dishes"][1], val["max_missing_dishes"]*100)}')
        lines.append(f'- 缺失页面文本：{r["missing_text"][0]} ({r["missing_text"][1]}%)')
        lines.append(f'- 菜品图片<3：{r["low_image"][0]} ({r["low_image"][1]}%) {status(r["low_image"][1], val["max_low_image_ratio"]*100)}')
        lines.append(f'- 重复门店：{len(r["duplicates"])}')
        for cat, cnt in r['categories'].items():
            lines.append(f'  - {cat}：{cnt} 家')
        if r['duplicates']:
            lines.append('- 重复明细：')
            for sid, name, cat1, cat2 in r['duplicates']:
                lines.append(f'  - {name} ({sid}) 出现在 {cat1} 和 {cat2}')
        lines.append('')

    report = '\n'.join(lines)
    out_path = os.path.join(REPO, 'reports', 'validation_report.md')
    with open(out_path, 'w') as f:
        f.write(report)
    print(report)
    print(f'\nSaved: {out_path}')


if __name__ == '__main__':
    main()
