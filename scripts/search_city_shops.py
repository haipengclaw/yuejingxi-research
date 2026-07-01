#!/usr/bin/env python3
"""Search Dianping for restaurants by city + template using the browse tool.

Usage:
  python3 scripts/search_city_shops.py --city 苏州 --template benbang
"""
import argparse, json, os, sys, time

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'
with open(os.path.join(REPO, 'data/city_config.json')) as f:
    CONFIG = json.load(f)

OUTPUT_DIR = os.path.join(REPO, 'data', 'cities')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLEEP_S = CONFIG['dianping'].get('sleep_between_requests_ms', 5000) / 1000
MAX_PAGES = CONFIG['dianping'].get('max_pages_per_keyword', 4)

sys.path.insert(0, os.path.dirname(__file__))
from browse_client import extract_search_shops, cookie_import

EXCLUDE_NAME_TERMS = [
    '游泳','健身','游泳馆','运动','瑜伽','舞蹈','拳击',
    '美发','美甲','美容','美睫','纹身','祛痘','化妆','养发',
    '摄影','照相馆','映画','写真','拍照','摄像',
    '装饰','装修','家居','家具','建材','家装',
    '会员商店','便利店','超市','商场','mall','Mall','MALL','广场','批发',
    '药店','医院','诊所','齿科','体检','中医',
    '学校','培训','教育','自习室','银行','证券','保险',
    '按摩','足疗','洗浴','汗蒸','SPA','养生馆','棋牌','KTV','酒吧','鸡尾酒','cocktail','Cocktail','Whisky','whisky','清吧','音乐吧',
    '密室','轰趴','网吧','采摘','农家乐',
    '园区','工作室','茶文化','花店','鲜花','手作','钓鱼','母婴','护理','哺乳','月子',
    '汽车','宠物','洗衣','家政','维修','售票','索道','缆车','musicbar','酒吧','鸡尾酒','cocktail','Cocktail','Whisky','whisky','清吧','音乐吧','KTV','演艺','演绎','剧场','影城','影院','广场','商场','mall','Mall','MALL','公园','收藏品','艺术空间','野兽派',
]


def is_restaurant(name):
    return not any(t in name for t in EXCLUDE_NAME_TERMS)


def classify_shops(shops, category_cfg):
    """Filter non-restaurants, deduplicate, and optionally sort shops."""
    seen = set()
    unique = []
    for s in shops:
        name = s.get('name', '')
        if not is_restaurant(name):
            continue
        sid = s.get('shopId')
        if sid and sid not in seen:
            seen.add(sid)
            unique.append(s)

    sort_by = category_cfg.get('sort_by')
    max_n = category_cfg.get('max', 60)
    if sort_by == 'reviewCount':
        unique = sorted(unique, key=lambda x: x.get('reviewCount', 0), reverse=True)
    return unique[:max_n]


def run_search(city_name, template_key):
    city_info = next((c for c in CONFIG['cities'] if c['name'] == city_name), None)
    if not city_info:
        raise ValueError(f'Unknown city: {city_name}')

    template = CONFIG['templates'].get(template_key)
    if not template:
        raise ValueError(f'Unknown template: {template_key}')

    city_id = city_info['cityId']
    pinyin = city_info['pinyin']
    cuisine_name = template['cuisine_name']
    print(f'\n=== {city_name} · {cuisine_name} (template={template_key}) ===')

    cookie_path = os.path.join(REPO, CONFIG['dianping']['cookies_file'])
    cookie_import(cookie_path)

    results = {}
    for cat_cfg in template['report_categories']:
        cat_label = cat_cfg['key']
        keywords = cat_cfg.get('search_keywords', [])
        if not keywords:
            keywords = [f'{city_name}{cuisine_name}']

        cat_shops = []
        for kw in keywords:
            for page in range(1, MAX_PAGES + 1):
                try:
                    shops = extract_search_shops(city_id, kw, page=page)
                    # Filter out non-restaurants immediately so we stop early
                    real_shops = [s for s in shops if is_restaurant(s.get('name', ''))]
                    print(f'    🔍 [{cat_label}] {kw} p{page} -> {len(shops)} shops ({len(real_shops)} 餐饮)')
                    cat_shops.extend(real_shops)
                    if len(real_shops) == 0:
                        break
                    time.sleep(SLEEP_S)
                except RuntimeError as e:
                    print(f'    🛑 {e}')
                    raise
                except Exception as e:
                    print(f'    ❌ error searching {kw}: {e}')
                    break

        filtered = classify_shops(cat_shops, cat_cfg)
        results[cat_label] = [[s['name'], s['shopId']] for s in filtered]
        print(f'    ✅ {cat_label}: {len(filtered)} shops')

    out_path = os.path.join(OUTPUT_DIR, f'{pinyin}_{template_key}_search_results.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'  💾 saved {out_path}')
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--city', required=True)
    parser.add_argument('--template', required=True)
    args = parser.parse_args()
    run_search(args.city, args.template)


if __name__ == '__main__':
    main()
