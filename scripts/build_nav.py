#!/usr/bin/env python3
"""全ページのヘッダーメニュー（PC：ドロップダウン／スマホ：アコーディオン）を同じ形に揃える。

使い方:  python scripts/build_nav.py
- ルート直下の *.html（404.html を除く）のヘッダーと、スマホメニューを書き換える。
- ブログ・無料診断のページは、case-refunfun.html を雛形に build_blog.py / build_tools.py が作るので、
  このスクリプトのあとで両方を実行する。
- メニューの項目を変えるときは、下の GROUPS だけを直す。何度流しても同じ結果になる。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (グループ名, [(リンク先, 表示名), ...])。リンク先の "@" は、トップページ（index.html）の意味。
GROUPS = [
    ("制作実績", [("lp.html", "LP制作"), ("corporate.html", "コーポレート"), ("ec.html", "EC・実装"), ("system.html", "システム開発")]),
    ("料金・サービス", [("@#pricing", "料金"), ("@#maintenance", "保守・運用"), ("@#logistics", "運送・物流業の方へ"), ("@#faq", "FAQ")]),
    ("ブログ・診断", [("blog/", "ブログ"), ("tools/", "セキュリティ診断")]),
    ("Kairosについて", [("@#message", "代表挨拶"), ("@#company", "運営者情報")]),
]

CHEVRON = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 3.5 5 7l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'

CSS = """<style id="gnav-css">
.gnav{display:flex;align-items:center;gap:30px}
@media (max-width:960px){.gnav{display:none}}
.gn-group{position:relative}
.gn-btn{font-family:'Noto Sans JP',sans-serif;font-size:12px;font-weight:500;letter-spacing:.08em;text-transform:none;color:var(--text-muted,var(--gray,#888));background:none;border:0;cursor:pointer;display:inline-flex;align-items:center;gap:7px;padding:12px 2px;border-bottom:1px solid transparent;transition:color .2s,border-color .2s}
.gn-btn svg{width:10px;height:10px;transition:transform .25s}
.gn-group:has(a.active)>.gn-btn{color:var(--text-primary,var(--black,#0f0f0f));border-bottom-color:var(--accent,#c4714a)}
.gn-btn:hover,.gn-group.open>.gn-btn{color:var(--text-primary,var(--black,#0f0f0f))}
.gn-group.open>.gn-btn svg{transform:rotate(180deg)}
.gn-panel{position:absolute;top:100%;left:50%;min-width:210px;padding-top:10px;transform:translate(-50%,6px);opacity:0;visibility:hidden;transition:opacity .2s,transform .25s,visibility .2s;z-index:210}
.gn-panel-in{background:#fff;border:1px solid var(--border,#e5e5e5);border-radius:10px;box-shadow:0 14px 44px rgba(0,0,0,.13);padding:8px}
.gn-group.open>.gn-panel{opacity:1;visibility:visible;transform:translate(-50%,0)}
@media (hover:hover){.gn-group:hover>.gn-panel{opacity:1;visibility:visible;transform:translate(-50%,0)}.gn-group:hover>.gn-btn{color:var(--text-primary,var(--black,#0f0f0f))}.gn-group:hover>.gn-btn svg{transform:rotate(180deg)}}
.gn-panel a{display:block;padding:11px 16px;border-radius:6px;font-family:'Noto Sans JP',sans-serif;font-size:13px;font-weight:400;letter-spacing:.04em;text-transform:none;white-space:nowrap;color:var(--text-primary,var(--black,#0f0f0f))!important;transition:background .2s,color .2s}
.gn-panel a::after{display:none!important}
.gn-panel a:hover{background:rgba(196,113,74,.09);color:var(--accent,#c4714a)!important}
.gn-panel a.active{color:var(--accent,#c4714a)!important;font-weight:500}
.mobile-menu{display:flex;flex-direction:column;align-items:center;justify-content:safe center;overflow-y:auto;padding:72px 0 40px;gap:0}
.mm-wrap{width:min(88vw,380px)}
.mm-home,.mm-group>summary{display:flex;justify-content:space-between;align-items:center;padding:19px 4px;font-family:'Playfair Display','Noto Sans JP',serif;font-size:20px;font-weight:400;color:var(--text-primary,var(--black,#0f0f0f));border-bottom:1px solid var(--border,#e5e5e5);cursor:pointer;list-style:none}
.mm-group>summary::-webkit-details-marker{display:none}
.mm-group>summary::after{content:'';width:8px;height:8px;margin-right:6px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg);transition:transform .3s}
.mm-group[open]>summary{border-bottom-color:transparent}
.mm-group[open]>summary::after{transform:rotate(-135deg)}
.mm-group[open]{border-bottom:1px solid var(--border,#e5e5e5)}
.mobile-menu .mm-links{display:grid;padding:0 0 16px}
.mobile-menu .mm-links a{font-family:'Noto Sans JP',sans-serif;font-size:15px;font-weight:400;letter-spacing:.04em;padding:12px 4px 12px 18px;color:var(--text-secondary,var(--gray-dark,#555));border-radius:6px}
.mobile-menu .mm-links a.active{color:var(--accent,#c4714a);font-weight:500}
.mobile-menu a.mm-contact{display:block;margin-top:28px;padding:15px 0;text-align:center;border:1px solid var(--text-primary,var(--black,#0f0f0f));border-radius:999px;font-family:'Noto Sans JP',sans-serif;font-size:14px;letter-spacing:.14em;color:var(--text-primary,var(--black,#0f0f0f))}
</style>"""

JS = """<script id="gnav-js">
(function(){
  var gs=[].slice.call(document.querySelectorAll('.gn-group'));
  function closeAll(except){gs.forEach(function(g){if(g!==except){g.classList.remove('open');g.querySelector('.gn-btn').setAttribute('aria-expanded','false');}});}
  gs.forEach(function(g){
    var b=g.querySelector('.gn-btn');
    b.addEventListener('click',function(e){
      e.stopPropagation();
      if(e.detail>0&&window.matchMedia('(hover:hover)').matches)return;
      var o=!g.classList.contains('open');closeAll(g);g.classList.toggle('open',o);b.setAttribute('aria-expanded',String(o));
    });
  });
  document.addEventListener('click',function(){closeAll();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeAll();});
  var ds=[].slice.call(document.querySelectorAll('.mm-group'));
  ds.forEach(function(d){if(d.querySelector('a.active'))d.open=true;});
  ds.forEach(function(d){d.addEventListener('toggle',function(){if(d.open)ds.forEach(function(o){if(o!==d)o.open=false;});});});
})();
</script>"""


def href_of(target, is_index):
    if target.startswith("@"):
        return target[1:] if is_index else "index.html" + target[1:]
    return target


def build(is_index, active, contact_html, nav_class):
    def item(t, label, extra_click=""):
        h = href_of(t, is_index)
        key = t if not t.startswith("@") else "index.html" + t[1:]
        cls = ' class="active"' if active and active == t else ""
        return f'<a href="{h}"{cls}{extra_click}>{label}</a>'

    pc = [f'<nav class="{nav_class}" aria-label="メインメニュー">']
    for gi, (name, items) in enumerate(GROUPS):
        pc.append(
            f'  <div class="gn-group"><button type="button" class="gn-btn" aria-expanded="false" aria-haspopup="true">{name}{CHEVRON}</button>'
            f'<div class="gn-panel"><div class="gn-panel-in">' + "".join(item(t, l) for t, l in items) + "</div></div></div>"
        )
    pc.append("  " + contact_html)
    pc.append("</nav>")

    mm = ['<div class="mobile-menu" id="mobileMenu">',
          '  <button class="mobile-close" onclick="toggleMenu()" aria-label="メニューを閉じる">✕</button>',
          '  <div class="mm-wrap">']
    if not is_index:
        mm.append('    <a class="mm-home" href="index.html" onclick="toggleMenu()">ホーム</a>')
    for name, items in GROUPS:
        mm.append(f'    <details class="mm-group"><summary>{name}</summary><div class="mm-links">'
                  + "".join(item(t, l, ' onclick="toggleMenu()"') for t, l in items) + "</div></details>")
    mm.append("    " + re.sub(r'class="[^"]*"', 'class="mm-contact"', contact_html, count=1).replace(' <span class="arrow">→</span>', "").replace('onclick=""', "") .replace("<a ", '<a onclick="toggleMenu()" ', 1))
    mm.append("  </div>")
    mm.append("</div>")
    return "\n".join(pc), "\n".join(mm)


def process(path):
    s = path.read_text(encoding="utf-8")
    is_index = path.name == "index.html"
    # 既存のメニューから、現在ページ・Contact の形を引き継ぐ
    nav_m = re.search(r"<nav( class=\"header-nav\"| class=\"gnav[^\"]*\")?[^>]*>.*?</nav>", s, re.S)
    if not nav_m:
        return False
    nav_html = nav_m.group(0)
    cm = re.search(r'<a [^>]*class="nav-contact[^"]*"[^>]*>.*?</a>', nav_html, re.S)
    if not cm:
        sys.exit(f"{path.name}: Contact のリンクが見つかりません")
    contact = re.sub(r"\s+", " ", cm.group(0)).strip()
    am = re.search(r'<a href="([^"]+)" class="active"', nav_html)
    active = None
    if am:
        a = am.group(1)
        active = a
    else:
        gm = re.search(r'<a href="([^"]+)"[^>]*class="active"', nav_html)
        active = gm.group(1) if gm else None
    if active and not any(active == t for _, its in GROUPS for t, _ in its):
        active = None
    nav_class = "gnav header-nav" if is_index else "gnav"
    new_nav, new_mm = build(is_index, active, contact, nav_class)
    s = s.replace(nav_html, new_nav, 1)
    s, n = re.subn(r'<div class="mobile-menu" id="mobileMenu">.*?\n</div>', lambda m: new_mm, s, count=1, flags=re.S)
    if n != 1:
        sys.exit(f"{path.name}: スマホメニューが見つかりません")
    # CSS・JS（毎回置き換える）
    s = re.sub(r'\n?<style id="gnav-css">.*?</style>\n?', "\n", s, flags=re.S)
    s = re.sub(r'\n?<script id="gnav-js">.*?</script>\n?', "\n", s, flags=re.S)
    s = s.replace(new_mm, new_mm + "\n" + CSS + "\n" + JS, 1)
    path.write_text(s, encoding="utf-8", newline="")
    return True


def main():
    for p in sorted(ROOT.glob("*.html")):
        if p.name == "404.html":
            continue
        print(("OK  " if process(p) else "skip"), p.name)


if __name__ == "__main__":
    main()
