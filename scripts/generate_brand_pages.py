#!/usr/bin/env python3
"""Batch generate brand detail pages for all restaurants."""
import json, os, re, sys

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'
sys.path.insert(0, os.path.join(REPO, 'scripts'))
from report_utils import CONFIG, find_paired, get_shop_info

tmp_dir = '/tmp/shops/guangzhou'
brands_dir = os.path.join(REPO, 'brands')
out_dir = os.path.join(REPO, 'docs', 'brands')

# Load data
data = json.load(open(f'{REPO}/data/cities/guangzhou_yuecai_search_results.json'))
brands = json.load(open(f'{REPO}/brands/data.json')) if os.path.exists(f'{REPO}/brands/data.json') else {}

# Collect unique shops
all_shops = {}
for cat, shops in data.items():
    for name, sid in shops:
        if sid not in all_shops:
            all_shops[sid] = {'name': name, 'categories': [cat]}
        elif cat not in all_shops[sid]['categories']:
            all_shops[sid]['categories'].append(cat)

CATEGORY_ICONS = {'黑珍珠':'🏆','米其林':'⭐','必吃榜':'🏅','排队':'🚶','老字号':'🏛️'}

def safe_filename(name):
    """Convert shop name to safe filename."""
    n = name.replace('/', '·').replace('\\', '·')
    return n

def generate_page(name, sid, categories):
    """Generate a brand detail HTML page."""
    city_name = '广州'
    info = get_shop_info(sid, name, city_name)
    paired = find_paired(sid, 'guangzhou')

    # Extract info from text data
    rating = info.get('rating', '')
    price = info.get('price', '')
    category = info.get('category', '粤菜')
    location = info.get('location', '')
    address = info.get('address', '')
    taste = info.get('tasteScore', '')
    env = info.get('envScore', '')
    service = info.get('serviceScore', '')
    review_count = info.get('reviewCount', '')

    # Get top 10 dishes
    dishes = paired.get('paired', [])[:10] if paired else []
    dishes_html = ''
    if dishes:
        dishes_html = '<div class="dish-list">'
        for j, d in enumerate(dishes):
            img = d.get('img', '')
            dish_name = d.get('name', '')
            img_html = f'<img src="{img}" onerror="this.style.display=\'none\'">' if img else ''
            dishes_html += f'''
        <div class="dish-card">
            {img_html}
            <div class="dish-info">
                <span class="rank">#{j+1}</span>
                <span class="name">{dish_name}</span>
            </div>
        </div>'''
        dishes_html += '</div>'

    # Get keywords
    keywords = info.get('keywords', [])
    kw_html = ''
    if keywords:
        kw_list = [f'<span class="kw">{kw}({cnt})</span>' for kw, cnt in keywords[:8]]
        kw_html = '<div class="kw-section">' + ' '.join(kw_list[:6]) + '</div>'

    # Category badges
    cat_badges = ''.join(f'<span class="tag">{CATEGORY_ICONS.get(c,"📄")} {c}</span>' for c in categories)

    # Star rating
    stars_html = ''
    if rating:
        s = '★' * max(1, round(float(rating)))
        stars_html = f'<span class="stars">{s}</span>'

    # Scores
    scores_html = ''
    if taste or env or service:
        scores_html = '<div class="scores">'
        if taste: scores_html += f'<span>口味 {taste}</span>'
        if env: scores_html += f'<span>环境 {env}</span>'
        if service: scores_html += f'<span>服务 {service}</span>'
        if review_count: scores_html += f'<span>评价 {review_count}条</span>'
        scores_html += '</div>'

    fname = safe_filename(name)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} · 品牌详情 · 粤京熹</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#f5f5f5;color:#333}}
.container{{max-width:800px;margin:0 auto;padding:16px}}
.header{{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:#fff;border-radius:12px;padding:28px 24px;margin-bottom:16px}}
.header h1{{font-size:22px;margin-bottom:4px}}
.header .sub{{font-size:13px;opacity:.7;margin-bottom:8px}}
.header .tags{{display:flex;flex-wrap:wrap;gap:4px}}
.header .tag{{background:rgba(255,255,255,.12);padding:2px 10px;border-radius:12px;font-size:10px}}
.back{{display:inline-block;color:#666;font-size:12px;margin-bottom:12px;text-decoration:none}}
.section{{background:#fff;border-radius:12px;padding:20px;margin-bottom:14px;box-shadow:0 1px 6px rgba(0,0,0,.06)}}
.section h2{{font-size:16px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:6px}}
.section p{{font-size:13px;line-height:1.7;color:#555}}
.stars{{color:#f5a623;font-size:16px;margin-right:4px}}
.scores{{display:flex;gap:12px;font-size:12px;color:#666;margin-top:6px;flex-wrap:wrap}}
.meta{{font-size:13px;color:#666;display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}}
.price{{color:#c0392b;font-weight:700}}
.dish-list{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}}
.dish-card{{background:#fafafa;border-radius:8px;padding:8px;text-align:center;border:1px solid #eee}}
.dish-card img{{width:100%;aspect-ratio:1.5;object-fit:cover;border-radius:4px;margin-bottom:4px}}
.dish-card .dish-info .rank{{display:inline-block;width:16px;height:16px;line-height:16px;background:#c0392b;color:#fff;font-size:9px;border-radius:50%;margin-right:2px}}
.dish-card .dish-info .name{{font-size:11px;font-weight:600}}
.kw-section{{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}}
.kw-section .kw{{background:#fef3f2;color:#c0392b;padding:2px 8px;border-radius:10px;font-size:10px;border:1px solid #fdd}}
.learn-item{{padding:10px 14px;background:#fafafa;border-radius:8px;margin-bottom:8px;border-left:3px solid #c0392b;font-size:12px;line-height:1.6;color:#555}}
.learn-item .title{{font-weight:600;color:#333;margin-bottom:2px}}
.footer{{text-align:center;padding:16px;color:#999;font-size:11px}}
.footer a{{color:#c0392b;text-decoration:none}}
</style>
</head>
<body>
<div class="container">
<a class="back" href="/yuejingxi-research/广州/广州粤菜_黑珍珠_20260630.html">← 返回报告</a>

<div class="header">
<h1>{name}</h1>
<div class="sub">{city_name} · {category}</div>
<div class="tags">{cat_badges}</div>
</div>

<div class="section">
<h2>📊 基本信息</h2>
<div class="meta">
{stars_html}
<span class="price">{price}</span>
{f'<span>📍 {location}</span>' if location else ''}
{f'<span>📍 {address}</span>' if address else ''}
</div>
{scores_html}
</div>

{f'<div class="section"><h2>🍽️ 推荐菜 Top {len(dishes)}</h2>{dishes_html}</div>' if dishes else ''}

{f'<div class="section"><h2>💬 食客印象</h2>{kw_html}</div>' if kw_html else ''}

<div class="section">
<h2>💡 值得学习</h2>
<div class="learn-item">
<div class="title">⭐ 亮点</div>
<div>{name}在{categories[0]}榜单中表现突出，{f"评分{rating}" if rating else "深受食客喜爱"}{f"，人均{price}" if price else ""}。{f"位于{location}" if location else ""}，是{city_name}{category}的代表性餐厅之一。</div>
</div>
<div class="learn-item">
<div class="title">🍽️ 招牌产品</div>
<div>{f"推荐菜包括{'、'.join(d['name'] for d in dishes[:5])}。" if dishes else "菜品以{category}为主，注重食材品质和烹饪工艺。"}</div>
</div>
</div>

<div class="footer">
<a href="/yuejingxi-research/index.html">返回粤京熹首页</a> · 粤京熹 R&D 助手<br>
<span style="font-size:10px;color:#bbb">本页面由AI自动生成，详细信息待补充</span>
</div>
</div>
</body>
</html>'''
    return fname, html

# Generate pages for ALL shops
os.makedirs(brands_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

count = 0
for sid, s in all_shops.items():
    name = s['name']
    categories = s['categories']
    fname, html = generate_page(name, sid, categories)

    # Save to brands/广州/
    dir_path = os.path.join(brands_dir, '广州')
    os.makedirs(dir_path, exist_ok=True)
    filepath = os.path.join(dir_path, f'{fname}.html')
    with open(filepath, 'w') as f:
        f.write(html)

    # Also write to brands data
    if name not in brands:
        summary_parts = []
        info = get_shop_info(sid, name, '广州')
        kw = info.get('keywords', [])
        if kw:
            top_kws = [k for k, c in kw[:3]]
            summary_parts.append(f"食客印象：{'、'.join(top_kws)}")
        dishes = find_paired(sid, 'guangzhou')
        if dishes and dishes.get('paired'):
            dish_names = [d['name'] for d in dishes['paired'][:3]]
            summary_parts.append(f"推荐菜：{'、'.join(dish_names)}")

        brands[name] = {
            "summary": f"{name}是广州{'·'.join(categories)}榜单上的知名{'·'.join(['粤菜'])}餐厅。" + (' ' + '。'.join(summary_parts) if summary_parts else ''),
            "highlights": [f"{c}上榜" for c in categories[:3]],
            "page": f"{fname}.html"
        }

    count += 1

# Save brands data
json.dump(brands, open(f'{REPO}/brands/data.json','w'), ensure_ascii=False, indent=2)
print(f"✅ 生成了 {count} 家品牌详情页")

# Show stats
has_page = sum(1 for s in all_shops.values() if s['name'] in brands and brands[s['name']].get('page'))
print(f"📊 共有品牌数据: {len(brands)} 家, 有详情页: {has_page} 家")