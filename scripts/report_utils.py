#!/usr/bin/env python3
"""Shared utilities for city-parameterized restaurant research reports."""
import json, os, re

REPO = '/Users/macclaw/yuejingxi-r-and-d-assistant'

with open(os.path.join(REPO, 'data/city_config.json')) as f:
    CONFIG = json.load(f)

CITY_AREAS = {
    '广州': ['天河路/体育中心','珠江新城','滨江路沿线','琶洲商圈','大石商圈',
             '沙面商圈','广州大道沿线','滨江路','北京路','上下九','西关',
             '江南西','海珠广场','越秀公园','东山口','淘金','天河北',
             '岗顶','龙洞','猎德','员村','广州塔','白云大道',
             '黄沙','芳村','花都','番禺','增城','从化'],
    '上海': ['淮海路','南京西路商圈','南京东路商圈','陆家嘴商圈','静安寺商圈',
             '徐家汇商圈','新天地/马当路','虹桥枢纽','八佰伴','外滩商圈',
             '北新泾/淞虹路','张江商圈','曲阳地区','复兴西路/丁香花园',
             '苏河湾','松江大学城','前滩','桃浦商圈','金山区','长寿路商圈',
             '中山公园','西藏北路','打浦桥','老西门','虹口足球场','人民广场',
             '世纪大道','天山','万体馆','肇嘉浜路','城隍庙','洋泾','御桥',
             '江桥','七宝商圈','北蔡商圈','国家会展中心','中山中路','衡山路',
             '静安寺'],
    '苏州': ['观前街','平江路','山塘街','金鸡湖','苏州中心','园区','木渎',
             '石路','十全街','李公堤','圆融时代广场','久光百货','新街口']
}

CSS = '''
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#f5f5f5;color:#333;padding:20px}
.container{max-width:1100px;margin:0 auto}
.header{background:linear-gradient(135deg,#c0392b,#e74c3c);color:#fff;padding:40px 24px;border-radius:16px;margin-bottom:24px;text-align:center}
.header h1{font-size:26px}
.header .desc{font-size:13px;opacity:.85;margin-top:8px}
.shop-card{background:#fff;border-radius:16px;margin-bottom:28px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,.08)}
.shop-banner{padding:18px 24px;border-bottom:1px solid #eee;background:#fafafa}
.shop-banner h2{font-size:17px;font-weight:700;margin-bottom:2px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}.detail-btn{display:inline-block;font-size:12px;background:#c0392b;color:#fff!important;padding:4px 14px;border-radius:16px;text-decoration:none;font-weight:600;white-space:nowrap;border:1px solid rgba(255,255,255,.3)}.detail-btn:hover{background:#a93226;transform:scale(1.05)}
.shop-banner .meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:2px;font-size:13px;color:#666;align-items:center}
.shop-banner .stars{color:#f5a623;font-size:15px}
.score-high{color:#27ae60}.score-mid{color:#f39c12}
.price-tag{color:#c0392b;font-weight:700;font-size:17px}
.award-badge{display:inline-block;background:#c0392b;color:#fff;padding:2px 10px;border-radius:12px;font-size:11px}
.score-grid{display:flex;gap:10px;padding:10px 24px;border-bottom:1px solid #eee;flex-wrap:wrap}
.score-item{flex:1;min-width:55px;text-align:center}
.score-item .val{font-size:16px;font-weight:700}
.score-item .lbl{font-size:11px;color:#999}
.section{padding:14px 24px;border-bottom:1px solid #eee}
.section:last-child{border-bottom:none}
.section h3{font-size:14px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.section h3 .badge{background:#c0392b;color:#fff;font-size:10px;padding:1px 8px;border-radius:10px}
.dish-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
.dish-card{background:#fff;border:1px solid #eee;border-radius:8px;overflow:hidden}
.dish-card .img-wrap{width:100%;aspect-ratio:1.54;background:#f5f5f5;overflow:hidden;display:flex;align-items:center;justify-content:center}
.dish-card .img-wrap img{width:100%;height:100%;object-fit:cover}
.dish-card .img-wrap .no-img{color:#ddd;font-size:30px}
.dish-card .info{padding:6px 8px}
.dish-card .dish-name{font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dish-card .dish-count{font-size:11px;color:#999}
.select-btn{color:#ccc;cursor:pointer;font-size:16px;margin-left:4px;transition:color .2s;user-select:none}
.select-btn:hover{color:#f5a623}
.select-btn.selected{color:#f5a623}
.dish-card .rank{display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;background:#c0392b;color:#fff;font-size:10px;border-radius:50%;margin-right:3px}
.dish-card:nth-child(n+4) .rank{background:#e67e22}
.dish-card:nth-child(n+7) .rank{background:#95a5a6}
.kw-grid{display:flex;flex-wrap:wrap;gap:5px}
.kw-tag{background:#fef3f2;color:#c0392b;padding:4px 10px;border-radius:14px;font-size:12px;border:1px solid #fdd;white-space:nowrap}
.kw-tag .cnt{color:#e74c3c;font-weight:700;margin-left:3px}
.select-hint{font-size:11px;color:#999;text-align:center;padding:4px 0 8px;border-bottom:1px solid #eee}.brand-summary{font-size:13px;line-height:1.7;color:#555;margin-bottom:8px}.brand-tags{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:12px;color:#666;margin-bottom:8px}
.footer{text-align:center;padding:20px;color:#999;font-size:12px}
@media(max-width:768px){.dish-grid{grid-template-columns:repeat(2,1fr)}.shop-banner h2{font-size:15px}.detail-btn{font-size:11px;padding:3px 10px}.score-grid{gap:6px;padding:8px 12px}.score-item .val{font-size:14px}.section{padding:10px 14px}.dish-card .dish-name{font-size:11px}}
@media print{body{background:#fff;padding:0}.shop-card{box-shadow:none;border:1px solid #ddd;break-inside:avoid}.header{background:#c0392b!important;-webkit-print-color-adjust:exact}.select-btn,.select-hint,.btn-print{display:none!important}}
'''

JS = '''
function toggleDish(btn,dishName,shopName,imgUrl){
  const list=(function(){
  var d = JSON.parse(localStorage.getItem('yjx_researchList')||'[]');
  if(d.length===0) d = JSON.parse(localStorage.getItem('researchList')||'[]');
  if(d.length && !localStorage.getItem('yjx_researchList')){
    localStorage.setItem('yjx_researchList',JSON.stringify(d));
    localStorage.removeItem('researchList');
  }
  return d;
})();
  const key=shopName+'::'+dishName;
  const idx=list.findIndex(item=>item.shop+'::'+item.dish===key);
  if(idx>=0){list.splice(idx,1);btn.classList.remove('selected');btn.textContent='☆';}
  else{list.push({shop:shopName,dish:dishName,img:imgUrl||''});btn.classList.add('selected');btn.textContent='★';}
  localStorage.setItem('yjx_researchList',JSON.stringify(list));
  updateCount();
}
function updateCount(){
  const el=document.getElementById('researchCount');
  if(el)el.textContent=(JSON.parse(localStorage.getItem('yjx_researchList')||'[]')).length;
}
window.addEventListener('load',function(){
  updateCount();
  document.querySelectorAll('.select-btn').forEach(b=>{
    const list=(function(){
  var d = JSON.parse(localStorage.getItem('yjx_researchList')||'[]');
  if(d.length===0) d = JSON.parse(localStorage.getItem('researchList')||'[]');
  if(d.length && !localStorage.getItem('yjx_researchList')){
    localStorage.setItem('yjx_researchList',JSON.stringify(d));
    localStorage.removeItem('researchList');
  }
  return d;
})();
    if(list.some(i=>i.shop===b.dataset.shop&&i.dish===b.dataset.dish)){b.classList.add('selected');b.textContent='★';}
  });
});
'''


def load_city_config():
    return CONFIG


def city_data_dir(city_pinyin):
    return os.path.join(REPO, 'data', 'cities')


def tmp_shop_dir(city_pinyin):
    return os.path.join('/tmp', 'shops', city_pinyin)


def find_paired(shop_id, city_pinyin):
    fpath = os.path.join(tmp_shop_dir(city_pinyin), f'p_{shop_id}.json')
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def get_shop_info(shop_id, shop_name, city_name):
    """Extract structured shop info from Dianping text dump."""
    city_pinyin = None
    for c in CONFIG['cities']:
        if c['name'] == city_name:
            city_pinyin = c['pinyin']
            break
    if not city_pinyin:
        city_pinyin = 'shanghai'

    text = None
    direct_path = os.path.join(tmp_shop_dir(city_pinyin), f't_{shop_id}.txt')
    if os.path.exists(direct_path):
        with open(direct_path) as f:
            text = f.read()
    else:
        # Fallback: search all text files by shop name prefix
        data_dir = tmp_shop_dir(city_pinyin)
        if os.path.isdir(data_dir):
            for fname in os.listdir(data_dir):
                if fname.endswith('.txt') and not fname.startswith('t_'):
                    try:
                        with open(os.path.join(data_dir, fname)) as f:
                            content = f.read()
                        if shop_name[:6] in content:
                            text = content
                            break
                    except Exception:
                        pass

    info = {'name': shop_name}
    if not text:
        return info

    text = re.sub(r'--- BEGIN.*?CONTENT ---\n?', '', text)
    text = re.sub(r'--- END.*?CONTENT ---', '', text)
    text = re.sub(r'^打开App\s*', '', text)

    m = re.search(r'★+\s*(\d\.\d)\s*(\d+)\s*条', text)
    if m:
        info['rating'] = float(m.group(1))
        info['reviewCount'] = int(m.group(2))

    m = re.search(r'¥(\d+)', text)
    if m:
        info['price'] = '¥' + m.group(1)

    m = re.search(r'(?:¥\d+/\w+)\s*(粤菜|顺德菜|广式|潮汕菜|客家菜|本帮菜|苏浙菜|浙菜|淮扬菜|特色菜|面馆|江浙菜|苏帮菜|杭帮菜|宁波菜|绍兴菜|台州菜|温州菜)', text)
    if not m:
        m = re.search(r'/\w+\s*(粤菜|顺德菜|广式|潮汕菜|客家菜|本帮菜|苏浙菜|浙菜|淮扬菜|特色菜|面馆|江浙菜|苏帮菜|杭帮菜|宁波菜|绍兴菜|台州菜|温州菜)', text)
    if m:
        info['category'] = m.group(1)

    m = re.search(r'口味:\s*([\d.]+)\s+环境:\s*([\d.]+)\s+服务:\s*([\d.]+)', text)
    if m:
        info['tasteScore'] = float(m.group(1))
        info['envScore'] = float(m.group(2))
        info['serviceScore'] = float(m.group(3))

    m = re.search(r'(\d{4}上榜[^营]+)', text)
    if m:
        info['award'] = m.group(1)

    m = re.search(r'([一-鿿]+路[一-鿿0-9]+号[一-鿿0-9]*(?:商场|广场|大厦|中心|楼|馆|店)?)', text)
    if m:
        info['address'] = m.group(1)

    areas = CITY_AREAS.get(city_name, [])
    for area in areas:
        if area in text:
            info['location'] = area
            break

    m = re.search(r'(热门榜\s*[··]\s*第\d+名)', text)
    if m:
        info['rank'] = m.group(1)

    info['keywords'] = extract_keywords(text)
    return info


def extract_keywords(text):
    keywords = []
    for m in re.finditer(r'([一-鿿]{2,20})\s+(\d{2,5})', text):
        kw = m.group(1).strip()
        cnt = int(m.group(2))
        skip_words = ['分钟前', '小时前', '时前有', '查看全部']
        if not any(s in kw for s in skip_words) and cnt > 2:
            keywords.append((kw, cnt))
    return keywords


def score_class(s):
    if s is None:
        return ''
    if s >= 4.5:
        return 'score-high'
    if s >= 4.0:
        return 'score-mid'
    return ''
