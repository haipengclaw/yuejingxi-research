#!/usr/bin/env python3
"""Thin wrapper around the gstack browse binary."""
import json, os, re, subprocess, time

BROWSE_BIN = '/Users/macclaw/.claude/skills/gstack/browse/dist/browse'


def run(args, timeout=60):
    """Run a browse command and return stdout."""
    cmd = [BROWSE_BIN] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr


def goto(url, wait=5):
    run(['goto', url], timeout=60)
    time.sleep(wait)
    # ensure navigation completed by checking url matches
    for _ in range(5):
        cur = run(['url'], timeout=10).strip()
        if url in cur or cur == url:
            break
        time.sleep(1)
    else:
        # retry once
        run(['goto', url], timeout=60)
        time.sleep(wait)


def js(expr, wait=0):
    if wait:
        time.sleep(wait)
    out = run(['js', expr], timeout=30)
    # Strip untrusted markers if present
    lines = out.splitlines()
    cleaned = []
    in_untrusted = False
    for line in lines:
        if '--- BEGIN UNTRUSTED EXTERNAL CONTENT' in line:
            in_untrusted = True
            continue
        if '--- END UNTRUSTED EXTERNAL CONTENT' in line:
            in_untrusted = False
            continue
        if not in_untrusted:
            cleaned.append(line)
    return '\n'.join(cleaned).strip()


def cookie_import(path):
    run(['cookie-import', path], timeout=10)


def text():
    out = run(['text'], timeout=30)
    return out


def is_verify_page():
    out = run(['url'], timeout=10)
    if 'verify.meituan.com' in out or 'spiderindefence' in out:
        return True
    txt = text()
    return any(k in txt for k in ['身份核实', '请依次点击', '验证码', '安全验证'])


def extract_search_shops(city_id, keyword, page=1):
    """Use browse to search and extract shop list.

    Page 1: human-like search via UI (click input → type → Enter) to avoid anti-scraping.
    Pages 2+: use direct /p{page} URL (works once first page is loaded).
    """
    from urllib.parse import quote
    encoded = quote(keyword)

    if page == 1:
        # Step 1: Go to city homepage to set city context
        cities = {'1':'shanghai','2':'beijing','3':'hangzhou','4':'guangzhou','5':'nanjing',
                  '6':'suzhou','7':'shenzhen','8':'chengdu','9':'chongqing','10':'tianjin',
                  '11':'ningbo','12':'yangzhou','13':'wuxi'}
        slug = cities.get(str(city_id), 'guangzhou')
        goto(f'https://www.dianping.com/{slug}', wait=4)

        if is_verify_page():
            raise RuntimeError(f'Verification page for {keyword}')

        # Step 2: Human-like search — click input, type, press Enter
        for attempt in range(3):
            try:
                run(['click', 'input[type="text"]'], timeout=10)
                time.sleep(1)
                run(['type', keyword], timeout=10)
                time.sleep(1)
                run(['press', 'Enter'], timeout=10)
                time.sleep(6)
                u = run(['url'], timeout=10)
                if '/search/keyword/' in u:
                    break
                print(f'      ↻ search redirect attempt {attempt+1}')
            except Exception as e:
                print(f'      ⚠️ search attempt {attempt+1}: {e}')
                time.sleep(3)
    else:
        # Pages 2+: direct URL works
        url = f'https://www.dianping.com/search/keyword/{city_id}/0_{encoded}/p{page}'
        goto(url, wait=5)

    if is_verify_page():
        raise RuntimeError(f'Verification page for {keyword}')

    # Scroll
    js("window.scrollBy(0, 800)", wait=1)
    js("window.scrollBy(0, 800)", wait=1)
    js("window.scrollBy(0, 800)", wait=2)

    expr = """
    JSON.stringify((function(){
      function getShopId(c){
        var el=c.querySelector('[data-shopid]');
        if(el) return el.getAttribute('data-shopid');
        var links=c.querySelectorAll('a[href*="shop/"]');
        for(var i=0;i<links.length;i++){
          var m=links[i].getAttribute('href').match(/shop\\/([A-Za-z0-9]+)/);
          if(m) return m[1];
        }
        var imgs=c.querySelectorAll('img');
        for(var i=0;i<imgs.length;i++){
          var src=imgs[i].getAttribute('src')||'';
          var m=src.match(/shop\\/([A-Za-z0-9]+)/);
          if(m) return m[1];
        }
        return null;
      }
      function getName(c){
        var titleLink=c.querySelector('a[data-hippo-type="shop"]');
        if(titleLink){
          var h4=titleLink.querySelector('h4');
          if(h4) return h4.textContent.trim();
          var t=titleLink.getAttribute('title');
          if(t) return t.trim();
        }
        var h4=c.querySelector('h4');
        if(h4) return h4.textContent.trim();
        var img=c.querySelector('img[title]');
        if(img) return (img.getAttribute('title')||img.getAttribute('alt')||'').trim();
        return '';
      }
      var r=[], s=new Set();
      document.querySelectorAll('#shop-all-list li').forEach(function(c){
        var id=getShopId(c);
        if(!id || s.has(id)) return;
        s.add(id);
        var name=getName(c);
        if(!name || name.length<2 || name.indexOf('!')>=0) return;
        var t=c.innerText || '';
        var rm=t.match(/([\\d,]+)\\s*条评价/);
        var rc=rm ? parseInt(rm[1].replace(/,/g,'')) : 0;
        var pm=t.match(/人均\\s*￥(\\d+)/);
        var ap=pm ? parseInt(pm[1]) : 0;
        var cm=t.match(/条评价[\\s\\|]*(\\S+?)(?:\\s*\\||\\s+&)/);
        var cat=cm ? cm[1].trim() : '';
        var b=Array.from(c.querySelectorAll('.badge,.tag,[class*="badge"],[class*="mark"]')).map(function(x){return x.textContent.trim();}).filter(function(x){return x && x.length<20;});
        r.push({shopId:id, name:name, reviewCount:rc, avgPrice:ap, category:cat, badges:b});
      });
      return r;
    })())
    """
    raw = js(expr, wait=1)
    try:
        return json.loads(raw)
    except Exception:
        print(f'    ⚠️ failed to parse search results: {raw[:200]}')
        return []


def extract_shop_details(shop_id):
    """Extract text and paired dishes from a shop page."""
    url = f'https://www.dianping.com/shop/{shop_id}'
    goto(url, wait=5)

    if is_verify_page():
        raise RuntimeError(f'Verification page for shop {shop_id}')

    # Scroll dish section
    js("const sc=document.querySelector('.scrolldishPics-pc');if(sc)sc.scrollLeft=500;", wait=2)

    # Text
    body_text = text()

    # Paired dishes
    dish_expr = """
    JSON.stringify((function(){
      var c = document.querySelector('.scrolldishPics-pc') || document.querySelector('.dishPics');
      if(!c) return {count:0, paired:[]};
      var imgs=[];
      c.querySelectorAll('.lazyload-image').forEach(function(el){
        var bg=el.style.backgroundImage;
        if(bg && bg !== 'none') imgs.push(bg.replace(/^url\\([\"']?|[\"']?\\)$/g,'').split('?')[0]);
      });
      var nc=c.querySelector('.dishNameContainer');
      var names=[];
      if(nc){
        nc.querySelectorAll('.dishName,[class*=dishName]').forEach(function(el){
          var t=(el.textContent||'').trim();
          if(t && t.length>=2) names.push(t);
        });
      }
      var paired=[];
      for(var i=0;i<Math.min(imgs.length,names.length);i++){
        paired.push({rank:i+1, name:names[i], img:imgs[i]});
      }
      var m = window.location.href.match(/shop\\/([^\\/?#]+)/);
      return {id: m?m[1]:'', count:paired.length, paired:paired};
    })())
    """
    raw = js(dish_expr, wait=1)
    try:
        paired = json.loads(raw)
    except Exception:
        paired = {'count': 0, 'paired': []}

    return body_text, paired
