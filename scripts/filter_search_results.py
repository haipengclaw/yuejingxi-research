#!/usr/bin/env python3
"""Clean search results after shop detail extraction.

Removes obvious non-restaurants (by name) and deduplicates shops across categories.

Usage:
  python3 scripts/filter_search_results.py --city 苏州 --template benbang
"""
import argparse, json, os, sys

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'
with open(os.path.join(REPO, 'data/city_config.json')) as f:
    CONFIG = json.load(f)

CATEGORY_PRIORITY = ['黑珍珠', '米其林', '必吃榜', '老字号', '排队']
EXCLUDE_NAME_TERMS = [
    # 运动/健身
    '游泳', '健身', '游泳馆', '运动', '瑜伽', '舞蹈', '拳击',
    # 美容/美发/美甲
    '美发', '美甲', '美容', '美睫', '纹身', '祛痘', '化妆', '养发',
    # 摄影/照相
    '摄影', '照相馆', '映画', '写真', '拍照', '摄像',
    # 装饰/装修/家居
    '装饰', '装修', '家居', '家具', '建材', '家装',
    # 购物
    '会员商店', '便利店', '超市', '商场', '批发',
    # 医疗
    '药店', '医院', '诊所', '齿科', '体检', '中医',
    # 教育
    '学校', '培训', '教育', '自习室',
    # 金融
    '银行', '证券', '保险',
    # 休闲/娱乐（非餐饮）
    '按摩', '足疗', '洗浴', '汗蒸', 'SPA', '养生馆', '棋牌', 'KTV', '酒吧',
    '密室', '轰趴', '网吧', '采摘', '农家乐',
    # 其他非餐饮
    '园区', '工作室', '茶文化', '花店', '鲜花', '手作', '钓鱼',
    '汽车', '宠物', '洗衣', '家政', '维修', '招聘', '人才',
]


def is_restaurant(name):
    """Exclude obvious non-restaurants by name."""
    return not any(t in name for t in EXCLUDE_NAME_TERMS)


def filter_results(city_name, template_key):
    city_info = next((c for c in CONFIG['cities'] if c['name'] == city_name), None)
    if not city_info:
        raise ValueError(f'Unknown city: {city_name}')
    pinyin = city_info['pinyin']

    data_path = os.path.join(REPO, 'data', 'cities', f'{pinyin}_{template_key}_search_results.json')
    if not os.path.exists(data_path):
        print(f'Not found: {data_path}')
        return

    with open(data_path) as f:
        data = json.load(f)

    # Filter each category by name
    filtered = {}
    for cat, shops in data.items():
        kept = []
        for name, sid in shops:
            if is_restaurant(name):
                kept.append([name, sid])
            else:
                print(f'  🗑️ [{cat}] {name}')
        filtered[cat] = kept

    # Deduplicate within each category only (don't remove from other categories)
    final = {}
    for cat, shops in filtered.items():
        seen = set()
        kept = []
        for name, sid in shops:
            if sid not in seen:
                seen.add(sid)
                kept.append([name, sid])
        final[cat] = kept

    # Preserve original order
    original_order = {sid: i for cat, shops in data.items() for i, (name, sid) in enumerate(shops)}
    for cat in final:
        final[cat].sort(key=lambda x: original_order.get(x[1], 9999))

    # Backup raw and overwrite
    backup_path = data_path + '.raw'
    if not os.path.exists(backup_path):
        with open(backup_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    with open(data_path, 'w') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f'\n{city_name} · {template_key}:')
    for cat in final:
        before = len(data.get(cat, []))
        after = len(final[cat])
        print(f'  {cat}: {before} -> {after}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--city', required=True)
    parser.add_argument('--template', required=True)
    args = parser.parse_args()
    filter_results(args.city, args.template)


if __name__ == '__main__':
    main()
