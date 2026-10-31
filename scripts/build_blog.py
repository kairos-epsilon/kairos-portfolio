#!/usr/bin/env python3
"""ブログのビルド：blog-src/*.html（先頭に --- で囲んだメタ情報）から blog/ 以下のページ、
feed.xml、sitemap.xml のブログ分、llms.txt のブログ節を生成する。

使い方:  python scripts/build_blog.py [--strict]
  --strict : 禁止語リスト（~/.claude/kairos-blog-banned.txt）が無ければエラーにする
エラーがあれば何も書き出さず、終了コード 1 で止まる。
"""
import html, json, re, sys
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from email.utils import format_datetime

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "blog-src"
OUT = ROOT / "blog"
B = "https://kairos-web.jp/"
CATEGORIES = ["ホームページ制作", "SEO・集客", "システム開発", "セキュリティ", "業務効率化・DX", "ニュース解説", "蟹江町・地域"]
SOURCE_REQUIRED = {"セキュリティ", "ニュース解説"}
ALLOWED_TAGS = {"p", "h2", "h3", "ul", "ol", "li", "strong", "em", "a", "table", "thead", "tbody", "tr", "th", "td", "blockquote", "br", "code"}
VOID = {"br"}
BANNED_FILE = Path.home() / ".claude" / "kairos-blog-banned.txt"
PINNED = [("ホームページのセキュリティ、何を確認すればいい？", "2026年10月のPHPの脆弱性をもとに、確認することとチェックリストを解説します。", "/column-security.html")]
JST = timezone(timedelta(hours=9))

errors = []
def err(msg): errors.append(msg)

# ---------------------------------------------------------------- 読み込み
def parse_post(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", raw, re.S)
    if not m:
        err(f"{path.name}: 先頭の --- メタ情報が読めません"); return None
    meta = {"sources": [], "faq": []}
    cur = None
    for line in m.group(1).splitlines():
        if not line.strip(): continue
        if line.startswith("- ") and cur in ("sources", "faq"):
            a, _, b = line[2:].partition(" | ")
            meta[cur].append((a.strip(), b.strip()))
            continue
        k, _, v = line.partition(":")
        k = k.strip(); v = v.strip()
        if k in ("sources", "faq"): cur = k; continue
        cur = k; meta[k] = v
    meta["slug"] = path.stem
    meta["body"] = m.group(2).strip()
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return meta

class Checker(HTMLParser):
    def __init__(self, name):
        super().__init__(); self.name = name; self.stack = []; self.links = []
    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS: err(f"{self.name}: 使えないタグ <{tag}>")
        for k, v in attrs:
            if k.startswith("on") or k in ("style", "class", "id"): err(f"{self.name}: 使えない属性 {k}")
            if tag == "a" and k == "href": self.links.append(v or "")
        if tag not in VOID: self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in VOID: return
        if not self.stack or self.stack[-1] != tag:
            err(f"{self.name}: タグの閉じ方が不正 </{tag}>（開いている: {self.stack[-1] if self.stack else 'なし'}）")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag: pass
        else:
            self.stack.pop()
    def close(self):
        super().close()
        if self.stack: err(f"{self.name}: 閉じていないタグ {self.stack}")

def plain(h): return re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", h)))

def load_banned(strict):
    if BANNED_FILE.exists():
        return [w.strip() for w in BANNED_FILE.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("#")]
    if strict: err(f"禁止語リストが見つかりません: {BANNED_FILE}")
    else: print(f"警告: 禁止語リストなし（{BANNED_FILE}）。--strict では失敗します")
    return []

def site_pages():
    return {p.name for p in ROOT.glob("*.html")}

def validate(posts, banned):
    today = datetime.now(JST).date()
    pages = site_pages(); slugs = set(); titles = set()
    for p in posts:
        n = p["slug"] + ".html"
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", p["slug"]): err(f"{n}: ファイル名は英小文字・数字・ハイフンのみ")
        if p["slug"] in slugs: err(f"{n}: 重複")
        slugs.add(p["slug"])
        for k in ("title", "description", "date", "category"):
            if not p.get(k): err(f"{n}: {k} がありません")
        if p.get("title") in titles: err(f"{n}: タイトルが重複")
        titles.add(p.get("title"))
        if p.get("category") and p["category"] not in CATEGORIES: err(f"{n}: カテゴリは {CATEGORIES} のいずれか")
        for k in ("date", "updated"):
            if p.get(k):
                try:
                    d = date.fromisoformat(p[k])
                    if d > today: err(f"{n}: {k} が未来の日付")
                except ValueError: err(f"{n}: {k} は YYYY-MM-DD")
        if p.get("title") and len(p["title"]) > 60: err(f"{n}: タイトルが長い（{len(p['title'])}文字、60以内）")
        if p.get("description") and not (50 <= len(p["description"]) <= 170): err(f"{n}: description は50〜170文字（いま{len(p['description'])}）")
        text = plain(p["body"])
        if len(text) < 1500: err(f"{n}: 本文が短い（{len(text)}文字、1500以上）")
        if "<h2" not in p["body"]: err(f"{n}: h2 見出しがありません")
        c = Checker(n); c.feed(p["body"]); c.close()
        for href in c.links:
            if href.startswith("https://"): continue
            if href.startswith("/") or not re.match(r"[a-z]+:", href):
                t = href.lstrip("/").split("#")[0].split("?")[0]
                if t and not (t in pages or t.startswith("blog/") or t == "feed.xml"): err(f"{n}: 内部リンク先がありません: {href}")
                if t.startswith("blog/") and t not in ("blog/",) and Path(t).stem not in slugs | {p["slug"]} and t != "blog/index.html":
                    pass  # 他の記事へのリンクは全記事の読み込み後に確認
            else: err(f"{n}: 使えないリンク {href}")
        if p.get("category") in SOURCE_REQUIRED and not p["sources"]: err(f"{n}: このカテゴリは出典（sources）が必須")
        for t, u in p["sources"]:
            if not u.startswith("https://"): err(f"{n}: 出典URLは https:// で始める: {t}")
        for q, a in p["faq"]:
            if not q or not a: err(f"{n}: FAQ の形式が不正")
        blob = " ".join([p.get("title", ""), p.get("description", ""), text, " ".join(a for _, a in p["faq"])])
        for w in banned:
            if w in blob: err(f"{n}: 使えない語が含まれています「{w}」")
    # 記事間リンクの存在確認
    for p in posts:
        for href in re.findall(r'href="(/blog/[^"#]+)"', p["body"]):
            t = href[len("/blog/"):]
            if t and t != "" and not (ROOT / "blog-src" / (Path(t).stem + ".html")).exists():
                err(f'{p["slug"]}.html: 記事リンク先がありません: {href}')

# ---------------------------------------------------------------- テンプレート
src_tpl = (ROOT / "case-refunfun.html").read_text(encoding="utf-8")
def absolutize(s):
    return re.sub(r'(href|src)="(?!https?:|/|#|mailto:|tel:|data:)([^"]+)"', r'\1="/\2"', s)
CSS = re.search(r"<style>.*?</style>", src_tpl, re.S).group(0).replace("</style>", """.prose p{font-size:13px;line-height:2.2;color:var(--gray-dark);max-width:760px;margin-top:16px}.prose h2{font-family:'Playfair Display','Noto Sans JP',serif;font-size:clamp(20px,2.6vw,26px);font-weight:400;line-height:1.6;margin-top:48px;max-width:760px}.prose h3{font-size:15px;font-weight:500;line-height:1.8;margin-top:32px;max-width:760px}.prose ul,.prose ol{margin:16px 0 0 1.2em;max-width:760px}.prose li{font-size:13px;line-height:2.2;color:var(--gray-dark)}.prose a,.src a,.lead a,.note a{color:var(--accent)}.prose blockquote{border-left:2px solid var(--accent);padding:4px 0 4px 18px;margin:20px 0 0;max-width:760px}.prose table{width:100%;max-width:760px;border-collapse:collapse;margin-top:24px;font-size:12px}.prose th,.prose td{border-bottom:1px solid var(--border);padding:12px 10px;text-align:left;line-height:1.9;color:var(--gray-dark)}.prose th{font-weight:500;color:var(--black)}.meta{font-size:11px;color:var(--gray);margin-top:20px;letter-spacing:.06em}.src li{font-size:12px;line-height:2.1;color:var(--gray-dark);margin-left:1.2em}.faq details{border-bottom:1px solid var(--border);padding:18px 0}.faq summary{cursor:pointer;font-size:14px;font-weight:500;line-height:1.8}.faq details p{font-size:12px;line-height:2.1;color:var(--gray-dark);margin-top:10px}.note{font-size:11px;color:var(--gray);line-height:2;margin-top:16px}.plist{list-style:none;margin:28px 0 0;padding:0;max-width:860px}.plist li{border-bottom:1px solid var(--border);padding:22px 0}.plist a.t{font-size:16px;font-weight:500;line-height:1.7;color:var(--black);text-decoration:none}.plist a.t:hover{color:var(--accent)}.plist .m{font-size:10px;letter-spacing:.12em;color:var(--gray);margin-bottom:6px}.plist .m b{color:var(--accent);font-weight:500;margin-left:10px}.plist p{font-size:12px;line-height:2;color:var(--gray-dark);margin-top:6px}.pin{background:var(--bg);padding:22px 24px;margin-top:28px;max-width:860px}.pin .m{font-size:10px;letter-spacing:.2em;color:var(--accent);margin-bottom:6px}</style>""")
TRACK = """<!-- Google tag (GA4) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-0D5FE87BBJ"></script>
<script>
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());gtag('config','G-0D5FE87BBJ');
</script>
<!-- Microsoft Clarity -->
<script>
(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","z6cmrb2gry");
</script>
"""
BODY_START = absolutize(re.search(r"<body>.*?<div class=\"page-hero\">", src_tpl, re.S).group(0).replace('<div class="page-hero">', "").replace(' class="active"', ""))
FOOTER = absolutize(re.search(r"<footer>.*?</html>", src_tpl, re.S).group(0))
CTA = """<section class="cta">
  <div class="wrap">
    <p>ホームページやシステムのお困りごとを、お聞かせください。<br>ヒアリングとお見積りは無料です。ご返信は通常2営業日以内です。</p>
    <a href="https://lin.ee/SvN5SIm" target="_blank" rel="noopener" class="btn">LINEで相談する →</a>
    <p class="sub">フォームからのご相談は<a href="/index.html#contact">こちら</a></p>
  </div>
</section>
"""
def jld(o): return '<script type="application/ld+json">\n' + json.dumps(o, ensure_ascii=False, separators=(",", ":")) + "\n</script>\n"
def esc(s): return html.escape(s, quote=True)
def fmt(d): y, m, dd = d.split("-"); return f"{y}年{int(m)}月{int(dd)}日"

def head(title, desc, url, ldjson, og="article"):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/rss+xml" title="Kairos ブログ" href="/feed.xml">
<meta property="og:type" content="{og}">
<meta property="og:locale" content="ja_JP">
<meta property="og:site_name" content="Kairos">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{B}assets/ogp.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{B}assets/ogp.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="icon" href="/icon-192.png" type="image/png" sizes="192x192">
<link rel="icon" href="/icon-512.png" type="image/png" sizes="512x512">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Noto+Sans+JP:wght@300;400;500;700&display=swap" rel="stylesheet">
{ldjson}{CSS}
{TRACK}</head>
"""

def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(items, 1)]}

# ---------------------------------------------------------------- 出力
def post_html(p, posts):
    url = f"{B}blog/{p['slug']}.html"
    upd = p.get("updated") or p["date"]
    art = {"@context": "https://schema.org", "@type": "BlogPosting", "@id": url + "#post", "mainEntityOfPage": url, "url": url,
           "headline": p["title"], "description": p["description"], "inLanguage": "ja", "image": B + "assets/ogp.png",
           "datePublished": p["date"], "dateModified": upd, "articleSection": p["category"],
           "author": {"@id": B + "#business"}, "publisher": {"@id": B + "#business"}, "isPartOf": {"@id": B + "#website"}}
    if p["tags"]: art["keywords"] = ", ".join(p["tags"])
    ld = jld(art) + jld(crumbs_ld([("Home", B), ("ブログ", B + "blog/"), (p["title"], url)]))
    if p["faq"]:
        ld += jld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]})
    body = p["body"].replace("<table>", '<table class="ptable">')
    body = re.sub(r'href="(?!https?:|/|#)([^"]+)"', r'href="/\1"', body)
    out = head(p["title"] + "｜Kairos ブログ", p["description"], url, ld)
    out += BODY_START
    out += f"""<div class="page-hero">
  <p class="breadcrumb"><a href="/index.html">Home</a> / <a href="/blog/">ブログ</a> / {esc(p['category'])}</p>
  <p class="eyebrow">{esc(p['category'])}</p>
  <h1 class="page-title">{esc(p['title'])}</h1>
  <p class="meta">公開：{fmt(p['date'])}{('／更新：' + fmt(p['updated'])) if p.get('updated') and p['updated'] != p['date'] else ''}</p>
</div>

<section class="blk">
  <div class="wrap prose">
{body}
  </div>
</section>
"""
    if p["sources"]:
        lis = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in p["sources"])
        out += f"""<section class="blk" style="background:var(--bg)">
  <div class="wrap src">
    <p class="eyebrow">Sources</p>
    <h2 class="h2">出典・参考</h2>
    <ul>{lis}</ul>
    <p class="note">この記事は、公開日時点の情報にもとづきます。最新の情報は、各出典でご確認ください。</p>
  </div>
</section>
"""
    if p["faq"]:
        fh = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in p["faq"])
        out += f"""<section class="blk">
  <div class="wrap faq">
    <p class="eyebrow">FAQ</p>
    <h2 class="h2">よくあるご質問</h2>
    {fh}
  </div>
</section>
"""
    rel = [q for q in posts if q["slug"] != p["slug"]]
    rel.sort(key=lambda q: (q["category"] != p["category"], -date.fromisoformat(q["date"]).toordinal()))
    rel = rel[:3]
    if rel:
        li = "".join(f'<li><div class="m">{fmt(q["date"])}<b>{esc(q["category"])}</b></div><a class="t" href="/blog/{q["slug"]}.html">{esc(q["title"])}</a></li>' for q in rel)
        out += f"""<section class="blk" style="background:var(--bg)">
  <div class="wrap">
    <p class="eyebrow">Related</p>
    <h2 class="h2">あわせて読みたい</h2>
    <ul class="plist">{li}</ul>
    <p class="note"><a href="/blog/">ブログの一覧へ</a></p>
  </div>
</section>
"""
    out += CTA + "\n" + FOOTER
    return out

def index_html(posts):
    url = B + "blog/"
    title = "ブログ｜ホームページ制作・システム開発・セキュリティの話題｜Kairos"
    desc = "蟹江町のKairosが、ホームページ制作、システム開発、SEO、セキュリティ、業務効率化など、事業者さまの役に立つ話題を、出典を確かめてお届けするブログです。"
    ld = jld({"@context": "https://schema.org", "@type": "Blog", "@id": url + "#blog", "url": url, "name": "Kairos ブログ", "description": desc,
              "inLanguage": "ja", "publisher": {"@id": B + "#business"},
              "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f"{B}blog/{p['slug']}.html", "datePublished": p["date"]} for p in posts[:20]]})
    ld += jld(crumbs_ld([("Home", B), ("ブログ", url)]))
    out = head(title, desc, url, ld, og="website") + BODY_START
    out += """<div class="page-hero">
  <p class="breadcrumb"><a href="/index.html">Home</a> / ブログ</p>
  <p class="eyebrow">Blog</p>
  <h1 class="page-title">Kairos ブログ</h1>
  <p class="page-desc">ホームページ制作、システム開発、SEO、セキュリティ、業務効率化など、事業者さまの役に立つ話題をお届けします。時事の話題は、公式発表などの出典を確かめて書いています。</p>
</div>

<section class="blk">
  <div class="wrap">
"""
    for t, d, u in PINNED:
        out += f'    <div class="pin"><p class="m">PICKUP</p><a class="t" href="{u}" style="font-size:16px;font-weight:500;color:var(--black);text-decoration:none">{esc(t)}</a><p class="note" style="margin-top:6px">{esc(d)}</p></div>\n'
    if posts:
        li = "".join(f'<li><div class="m">{fmt(p["date"])}<b>{esc(p["category"])}</b></div><a class="t" href="/blog/{p["slug"]}.html">{esc(p["title"])}</a><p>{esc(p["description"])}</p></li>' for p in posts)
        out += f'    <ul class="plist">{li}</ul>\n'
    else:
        out += '    <p class="lead" style="margin-top:28px">記事を準備しています。</p>\n'
    out += """    <p class="note">このブログの記事は、AI の支援を受けて作成し、出典を確かめたうえで公開しています。内容に誤りがあれば、お問い合わせからご連絡ください。</p>
    <p class="note"><a href="/feed.xml">RSS フィード</a></p>
  </div>
</section>

""" + CTA + "\n" + FOOTER
    return out

def feed_xml(posts):
    items = ""
    for p in posts[:20]:
        d = datetime.fromisoformat(p["date"]).replace(hour=9, tzinfo=JST)
        u = f"{B}blog/{p['slug']}.html"
        items += f"  <item>\n    <title>{esc(p['title'])}</title>\n    <link>{u}</link>\n    <guid isPermaLink=\"true\">{u}</guid>\n    <pubDate>{format_datetime(d)}</pubDate>\n    <category>{esc(p['category'])}</category>\n    <description>{esc(p['description'])}</description>\n  </item>\n"
    last = format_datetime(datetime.fromisoformat(posts[0]["date"]).replace(hour=9, tzinfo=JST)) if posts else format_datetime(datetime.now(JST))
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n  <title>Kairos ブログ</title>\n  <link>{B}blog/</link>\n  <description>ホームページ制作・システム開発・セキュリティなどの話題</description>\n  <language>ja</language>\n  <lastBuildDate>{last}</lastBuildDate>\n{items}</channel>\n</rss>\n'

def update_sitemap(posts):
    p = ROOT / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    ents = re.findall(r"  <url>\s*<loc>(.*?)</loc>(?:\s*<lastmod>(.*?)</lastmod>)?\s*</url>", s, re.S)
    keep = [(l, m) for l, m in ents if "/blog/" not in l]
    new = [(B + "blog/", posts[0].get("updated") or posts[0]["date"] if posts else date.today().isoformat())]
    new += [(f"{B}blog/{q['slug']}.html", q.get("updated") or q["date"]) for q in posts]
    head_part = s.split("<urlset", 1)[0]
    body = "".join(f"  <url>\n    <loc>{l}</loc>\n" + (f"    <lastmod>{m}</lastmod>\n" if m else "") + "  </url>\n" for l, m in keep + new)
    p.write_text(head_part + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n", encoding="utf-8", newline="")

def update_llms(posts):
    p = ROOT / "llms.txt"
    s = p.read_text(encoding="utf-8")
    sec = f"## ブログ\n- [Kairos ブログ]({B}blog/): ホームページ制作・システム開発・SEO・セキュリティ・業務効率化の話題。出典を確かめて公開しています\n"
    sec += "".join(f"- [{q['title']}]({B}blog/{q['slug']}.html): {q['description']}\n" for q in posts[:15]) + "\n"
    s = re.sub(r"## ブログ\n.*?(?=\n## |\Z)", "", s, flags=re.S)
    s = s.replace("## 問い合わせ", sec + "## 問い合わせ", 1) if "## 問い合わせ" in s else s.rstrip("\n") + "\n\n" + sec
    s = re.sub(r"\n{3,}", "\n\n", s)
    p.write_text(s, encoding="utf-8", newline="")

def main():
    for st in (sys.stdout, sys.stderr):
        try: st.reconfigure(encoding="utf-8")
        except Exception: pass
    strict = "--strict" in sys.argv
    posts = [x for x in (parse_post(f) for f in sorted(SRC.glob("*.html"))) if x]
    banned = load_banned(strict)
    validate(posts, banned)
    if errors:
        print("ビルドを中止しました。次を直してください：")
        for e in errors: print(" -", e)
        sys.exit(1)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    OUT.mkdir(exist_ok=True)
    keep = {f"{p['slug']}.html" for p in posts} | {"index.html"}
    for f in OUT.glob("*.html"):
        if f.name not in keep: f.unlink()
    for p in posts: (OUT / f"{p['slug']}.html").write_text(post_html(p, posts), encoding="utf-8", newline="")
    (OUT / "index.html").write_text(index_html(posts), encoding="utf-8", newline="")
    (ROOT / "feed.xml").write_text(feed_xml(posts), encoding="utf-8", newline="")
    update_sitemap(posts); update_llms(posts)
    print(f"完了：記事 {len(posts)} 本" + ("（禁止語チェック済み）" if banned else ""))

if __name__ == "__main__":
    main()
