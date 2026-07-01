#!/usr/bin/env python3
"""Generate reports for a city + template using shared utilities."""
import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from report_utils import CONFIG, find_paired, get_shop_info, CSS, JS, score_class

REPO = CONFIG['paths']['repo']
DATE = CONFIG.get('date', datetime.now().strftime('%Y%m%d'))
BRANDS_FILE = os.path.join(REPO, 'brands', 'data.json')
brands_data = {}
if os.path.exists(BRANDS_FILE):
    try:
        brands_data = json.load(open(BRANDS_FILE, encoding='utf-8'))
    except Exception:
        brands_data = {}


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_search_data(city_pinyin, template_key):
    data_dir = os.path.join(REPO, 'data', 'cities')
    path = os.path.join(data_dir, f'{city_pinyin}_{template_key}_search_results.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def generate_one_report(city_name, city_pinyin, cuisine_name, category_label, shops):
    if not shops:
        print(f'  ⚠️ {city_name} {cuisine_name} {category_label}: no shops')
        return None

    shown = len(shops)
    cat_key = category_label.replace('/', '_')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="referrer" content="no-referrer">
<title>{city_name}{cuisine_name} {cat_key} 餐厅研究报告</title>
<style>{CSS}</style>
<script>{JS}</script>
</head>
<body>
<div class="container">
<div class="header">
<div style="float:right;font-size:13px;opacity:.9;background:rgba(255,255,255,.15);padding:4px 14px;border-radius:20px">
<a href="../research_list.html" style="color:#fff;text-decoration:none">📋 研究清单 <span id="researchCount" style="font-weight:700">0</span> 道菜</a>
</div>
<h1>🍜 {city_name}{cuisine_name} · {cat_key}</h1>
<div class="desc">📍 {city_name} · 数据来源：大众点评 · {DATE[:4]}-{DATE[4:6]}-{DATE[6:]} · 已收录 <strong>{shown}</strong> 家 · 粤京熹 R&D 助手</div>
<button class="btn-print" onclick="window.print()" style="float:right;margin-top:8px;padding:4px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;font-size:12px;cursor:pointer">🖨️ 导出PDF</button>
</div>'''

    for idx, (name, shop_id) in enumerate(shops):
        paired = find_paired(shop_id, city_pinyin)
        info = get_shop_info(shop_id, name, city_name)
        rating = info.get('rating', 0)
        stars = '★' * max(1, round(rating)) if rating else ''
        bp = os.path.join(REPO, 'docs', 'brands', city_name, f'{name}.html')
        dbn = f' <a href="/yuejingxi-research/brands/{city_name}/{name}.html" class="detail-btn" title="查看品牌详情">📋 详细</a>' if os.path.exists(bp) else ''

        html += f'''
<div class="shop-card">
<div class="shop-banner">
<h2>{idx+1}. {name}{dbn}</h2>
<div class="meta">
<span class="stars">{stars}</span>
<span class="{score_class(rating)}" style="font-weight:700;font-size:16px">{rating}</span>
<span>|</span><span class="price-tag">{info.get('price','')}</span>
<span>|</span><span>{info.get('category','')}</span>
{f'<span>|📍 {info.get("location","")}</span>' if info.get('location') else ''}
{f'<span class="award-badge">🏅 {info.get("award","")}</span>' if info.get('award') else ''}
</div>
</div>
<div class="score-grid">
<div class="score-item"><div class="val {score_class(info.get('tasteScore'))}">{info.get('tasteScore','')}</div><div class="lbl">口味</div></div>
<div class="score-item"><div class="val {score_class(info.get('envScore'))}">{info.get('envScore','')}</div><div class="lbl">环境</div></div>
<div class="score-item"><div class="val {score_class(info.get('serviceScore'))}">{info.get('serviceScore','')}</div><div class="lbl">服务</div></div>
<div class="score-item"><div class="val">{info.get('reviewCount','')}</div><div class="lbl">评价数</div></div>
{f'<div class="score-item"><div class="val" style="font-size:13px">{info.get("address","")}</div><div class="lbl">地址</div></div>' if info.get('address') else ''}
</div>'''

        dishes = paired.get('paired', [])[:10] if paired and 'paired' in paired else []
        if dishes:
            html += '\n<div class="section"><h3>🍽️ 推荐菜 Top 10</h3>\n<div class="dish-grid">'
            for j, d in enumerate(dishes):
                de = d["name"].replace("'", "\\'").replace('"', '&quot;')
                ne = name.replace("'", "\\'").replace('"', '&quot;')
                img_tag = f'<img src="{d["img"]}" loading="lazy" onerror="this.parentElement.innerHTML=\'<div class=no-img>🍽️</div>\'">'
                hot = '🔥' if j < 3 else ''
                html += f'''
<div class="dish-card">
<div class="img-wrap">{img_tag}</div>
<div class="info">
<div class="dish-name"><span class="rank">{j+1}</span>{d["name"]}</div>
<div class="dish-count">{hot} <span class="select-btn" data-dish="{de}" data-shop="{ne}" data-img="{d["img"]}" onclick="toggleDish(this,\'{de}\',\'{ne}\',\'{d["img"]}\')" style="cursor:pointer;margin-left:6px;font-size:16px">☆</span></div>
</div>
</div>'''
            html += '\n</div>\n<div class="select-hint">💡 点击菜品上的 <span style="color:#f5a623">☆</span> 收藏到研究清单</div></div>'

        keywords = info.get('keywords', [])
        if keywords:
            html += f'\n<div class="section"><h3>💬 评价关键词 <span class="badge">共{len(keywords)}个</span></h3><div class="kw-grid">'
            for kw, cnt in keywords[:20]:
                html += f'<span class="kw-tag">{kw} <span class="cnt">{cnt}</span></span>'
            html += '</div></div>'

        # Brand intro section
        brand_info = brands_data.get(name, None)
        if brand_info:
            highlights_html = ' · '.join(f'🏷️ {h}' for h in brand_info.get('highlights', []))
            detail_link = brand_info.get('page', '')
            brand_path = os.path.join(REPO, "docs", "brands", city_name, detail_link)
            detail_btn = f'<a href="/yuejingxi-research/brands/{city_name}/{detail_link}" class="detail-btn" >📋 详细案例</a>' if detail_link and os.path.exists(brand_path) else ''
            html += f'''
    <div class="section">
    <h3>🏪 门店/品牌简介</h3>
    <p style="font-size:13px;line-height:1.7;color:#555;margin-bottom:8px">{brand_info["summary"]}</p>
    <div style="font-size:12px;color:#666;margin-bottom:8px">{highlights_html}</div>
    {detail_btn}
    </div>'''

        html += '\n</div>\n'

    html += f'''
<div class="footer">
<p>粤京熹 R&D 助手 · {city_name}{cuisine_name} {cat_key} · {DATE[:4]}-{DATE[4:6]}-{DATE[6:]}</p>
</div>
</div>
</body>
</html>'''

    fname = f'{city_name}{cuisine_name}_{cat_key}_{DATE}.html'
    return fname, html


def save_report(fname, html, city_name):
    reports_dir = os.path.join(REPO, 'reports')
    desktop_dir = os.path.join(CONFIG['paths']['desktop'], city_name)
    ensure_dir(reports_dir)
    ensure_dir(desktop_dir)

    repo_path = os.path.join(reports_dir, fname)
    desktop_path = os.path.join(desktop_dir, fname)

    with open(repo_path, 'w') as f:
        f.write(html)
    with open(desktop_path, 'w') as f:
        f.write(html)

    return repo_path, desktop_path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--city', required=True, help='City Chinese name')
    parser.add_argument('--template', required=True, help='Template key, e.g. benbang/jiangzhe')
    parser.add_argument('--dry-run', action='store_true', help='Do not write files')
    args = parser.parse_args()

    city_name = args.city
    template_key = args.template

    city_info = None
    for c in CONFIG['cities']:
        if c['name'] == city_name:
            city_info = c
            break
    if not city_info:
        print(f'Unknown city: {city_name}')
        sys.exit(1)

    template = CONFIG['templates'].get(template_key)
    if not template:
        print(f'Unknown template: {template_key}')
        sys.exit(1)

    city_pinyin = city_info['pinyin']
    cuisine_name = template['cuisine_name']
    data = load_search_data(city_pinyin, template_key)

    generated = []
    for cat_cfg in template['report_categories']:
        cat_label = cat_cfg['key']
        shops = data.get(cat_label, [])
        result = generate_one_report(city_name, city_pinyin, cuisine_name, cat_label, shops)
        if not result:
            continue
        fname, html = result
        if not args.dry_run:
            save_report(fname, html, city_name)
        generated.append(fname)
        print(f'  ✅ {fname} ({len(shops)}家)')

    print(f'\n{city_name} · {cuisine_name}: generated {len(generated)} reports')


if __name__ == '__main__':
    main()
