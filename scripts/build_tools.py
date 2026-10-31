#!/usr/bin/env python3
"""無料診断ツール（tools/）のページを生成する。ブログと同じテンプレートを使う。

使い方:  python scripts/build_tools.py
生成: tools/index.html, tools/security-check.html, tools/php-check.html
更新: sitemap.xml（tools の3ページ）、llms.txt（無料診断の節）
"""
import re, sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_blog import ROOT, B, head, BODY_START, FOOTER, jld, crumbs_ld, esc, JST  # noqa: E402

OUT = ROOT / "tools"
TODAY = datetime.now(JST).date().isoformat()

EXTRA_CSS = """<style>
.tool{max-width:760px}
.tool .q{border:0;border-bottom:1px solid var(--border);padding:22px 0;margin:0}
.tool .q legend{font-size:14px;font-weight:500;line-height:1.8;padding:0}
.tool .q .why{font-size:11px;color:var(--gray);line-height:1.9;margin-top:4px}
.tool .q label{display:inline-flex;align-items:center;gap:6px;margin:10px 20px 0 0;font-size:13px;color:var(--gray-dark);cursor:pointer}
.tool .q.miss{background:#fbf0ea;outline:1px solid var(--accent)}
.tool input[type=text]{font-family:inherit;font-size:14px;padding:12px 14px;border:1px solid var(--border);width:100%;max-width:320px;background:#fff}
.tool button.btn{border:0;cursor:pointer;font-family:inherit}
.tool .actions{margin-top:28px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.tool .err{font-size:12px;color:#b3401b;margin-top:12px;min-height:1.2em}
.result{display:none;background:var(--bg);padding:34px 32px;margin-top:36px;max-width:760px}
.result.show{display:block}
.result h2{font-family:'Playfair Display','Noto Sans JP',serif;font-size:clamp(20px,2.6vw,26px);font-weight:400;line-height:1.6;margin-bottom:10px}
.result .badge{display:inline-block;font-size:10px;letter-spacing:.14em;padding:3px 12px;border:1px solid;border-radius:99px;margin-bottom:14px}
.result .badge.ok{color:#2f7a4d;border-color:#2f7a4d}.result .badge.mid{color:#a9751a;border-color:#a9751a}.result .badge.ng{color:#b3401b;border-color:#b3401b}
.result p{font-size:13px;line-height:2.1;color:var(--gray-dark);margin-top:12px}
.result ul{margin:14px 0 0 1.2em}.result li{font-size:13px;line-height:2.1;color:var(--gray-dark);margin-top:8px}
.result li b{color:var(--black);font-weight:500}
.result .cta-box{border-top:1px solid var(--border);margin-top:28px;padding-top:24px}
.result .note{font-size:11px;color:var(--gray);line-height:2;margin-top:18px}
.tcards{display:grid;grid-template-columns:repeat(2,1fr);gap:2px;background:var(--border);margin-top:28px;max-width:860px}
.tcards a{background:var(--white);padding:30px 28px;text-decoration:none;color:inherit;display:block}
.tcards a:hover{background:var(--bg)}
.tcards h3{font-size:15px;font-weight:500;line-height:1.7;margin-bottom:8px}.tcards p{font-size:12px;line-height:2;color:var(--gray-dark)}
.tcards span{display:block;font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:8px}
@media(max-width:960px){.tcards{grid-template-columns:1fr}.result{padding:26px 20px}}
</style>
"""

CTA_LINE = "https://lin.ee/SvN5SIm"
LEAD = "Kairos は、ホームページの制作と、公開後の保守・運用を一貫して担当しています。この診断は、「公開後に守る」ことの、最初の一歩として作りました。"

def page(fn, title, desc, h1, lead, crumb, body, script, app_name, faq=None):
    url = f"{B}tools/{fn}" if fn != "index.html" else f"{B}tools/"
    ld = ""
    if fn != "index.html":
        ld += jld({"@context": "https://schema.org", "@type": "WebApplication", "name": app_name, "url": url, "description": desc,
                   "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "inLanguage": "ja",
                   "offers": {"@type": "Offer", "price": "0", "priceCurrency": "JPY"}, "publisher": {"@id": B + "#business"}})
    items = [("Home", B), ("セキュリティ簡易無料診断", B + "tools/")]
    if fn != "index.html": items.append((crumb, url))
    if faq:
        ld += jld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in faq]})
    ld += jld(crumbs_ld(items)) + EXTRA_CSS
    out = head(title, desc, url, ld, og="website") + BODY_START
    bc = '<a href="/index.html">Home</a> / ' + (f'<a href="/tools/">セキュリティ簡易無料診断</a> / {esc(crumb)}' if fn != "index.html" else "セキュリティ簡易無料診断")
    out += f"""<div class="page-hero">
  <p class="breadcrumb">{bc}</p>
  <p class="eyebrow">Free Check</p>
  <h1 class="page-title">{h1}</h1>
  <p class="page-desc">{lead}</p>
</div>

{body}{faq_html(faq)}
<section class="cta">
  <div class="wrap">
    <p>ホームページの「守り」について、不安なことがあればご相談ください。<br>ヒアリングとお見積りは無料です。ご返信は通常2営業日以内です。</p>
    <a href="{CTA_LINE}" target="_blank" rel="noopener" class="btn" data-cta="bottom">LINEで相談する →</a>
    <p class="sub">フォームからのご相談は<a href="/index.html#contact">こちら</a></p>
  </div>
</section>

{FOOTER}"""
    if script: out = out.replace("</body>", f"<script>\n{script}\n</script>\n</body>", 1)
    (OUT / fn).write_text(out, encoding="utf-8", newline="")

def faq_html(faq):
    if not faq: return ""
    items = "".join(f"<details><summary>{esc(q)}</summary><p>{a}</p></details>" for q, a in faq)
    return f'''<section class="blk" style="background:var(--bg)">
  <div class="wrap faq" style="max-width:760px">
    <p class="eyebrow">FAQ</p>
    <h2 class="h2">よくあるご質問</h2>
    {items}
  </div>
</section>
'''

ARTICLES = [("PHP2shell（PHPの脆弱性）とは？何が問題で、何をすればいい？", "/blog/php2shell-explained.html"),
            ("WordPressは影響を受ける？PHPバージョンの確認方法と対応", "/blog/wordpress-php-version-check.html"),
            ("ホームページが改ざん・乗っ取りされたら？初動対応と日頃の備え", "/blog/website-hacked-what-to-do.html"),
            ("「保護されていない通信」と表示されたら｜運営者向けの確認", "/blog/not-secure-warning-https.html"),
            ("ホームページのセキュリティ、何を確認すればいい？", "/column-security.html")]
def related():
    li = "".join(f'<li style="font-size:13px;line-height:2.2;margin-top:6px"><a href="{u}" style="color:var(--accent)">{esc(t)}</a></li>' for t, u in ARTICLES)
    return f'<h2 class="h2" style="margin-top:56px;font-size:20px">関連する解説記事</h2><ul style="margin:12px 0 0 1.2em;max-width:760px">{li}</ul>'

# ------------------------------------------------------------------ セルフチェック
SEC_JS = r"""
(function(){
var Q=[
{id:'owner',q:'ホームページのサーバーとドメインの契約先、契約者、更新期限を、把握していますか？',why:'契約が切れるとサイトが突然見えなくなったり、他人にドメインを取られたりすることがあります。',na:false,
 fix:'契約している会社、契約者名義、更新期限を、1枚にまとめて残しておきましょう。制作会社に任せている場合は、その会社に確認します。'},
{id:'update',q:'WordPress などのシステム、テーマ、プラグインを、この3か月以内に更新しましたか？',why:'古いままの部分は、攻撃の入口になりやすいところです。',na:true,
 fix:'更新の通知が出ていないか、管理画面で確認しましょう。更新の前には、必ずバックアップを取ります。'},
{id:'php',q:'ホームページが使っているPHPのバージョンを、把握していますか？',why:'2026年10月に、PHPの重大な脆弱性が公表されました。古い版は、修正プログラムが出ないものがあります。',na:true,
 fix:'PHPバージョン診断（<a href="/tools/php-check.html">こちら</a>）で、更新が必要かを確認できます。バージョンは、制作会社やサーバー会社に聞くか、WordPress の「サイトヘルス」で見られます。'},
{id:'unused',q:'使っていないプラグインや、古いテスト用のサイトを、残していませんか？（残していない＝「はい」）',why:'使っていない機能や、放置したサイトは、気づかれないまま狙われやすくなります。',na:true,
 fix:'使っていないプラグインは、削除しましょう（無効化だけでは残ります）。昔のテスト用サイトも、不要なら消します。'},
{id:'password',q:'管理画面・サーバーのパスワードは、ほかのサービスと使い回さず、長く複雑にしていますか？',why:'使い回しのパスワードは、ほかのサービスから漏れた情報で、不正にログインされるおそれがあります。',na:false,
 fix:'サービスごとに別のパスワードにし、パスワード管理ツールを使うと管理しやすくなります。'},
{id:'twofa',q:'管理画面やサーバー、ドメインの管理画面で、二段階認証を使っていますか？（使えるものだけでかまいません）',why:'パスワードが漏れても、すぐには不正にログインされにくくなります。',na:false,
 fix:'二段階認証に対応しているサービスから、順にオンにしましょう。'},
{id:'backup',q:'サイトのバックアップを定期的に取り、サーバーとは別の場所にも保管していますか？',why:'改ざんや故障が起きたときに、元に戻せるかどうかは、バックアップで決まります。',na:false,
 fix:'バックアップの頻度と保管場所を決め、実際に戻せるかも確認しましょう。サーバー会社の自動バックアップの内容も、確認します。'},
{id:'accounts',q:'管理画面にログインできる人を、把握していますか？（退職した人や、昔の制作会社のアカウントが残っていない＝「はい」）',why:'使われていないアカウントが残っていると、そこから不正に入られるおそれがあります。',na:false,
 fix:'ログインできる人の一覧を確認し、不要なアカウントは削除します。'},
{id:'https',q:'ホームページは、https:// で始まるアドレスで表示され、ブラウザに警告は出ませんか？',why:'警告が出るサイトは、訪れた人に不安を与え、信頼も下がります。',na:false,
 fix:'証明書（SSL）の期限と、自動更新の設定を確認しましょう。'},
{id:'privacy',q:'問い合わせフォームなどで個人情報を受け取っている場合、その取り扱い（保存先、見られる人）を把握し、プライバシーポリシーを載せていますか？',why:'個人情報を扱う以上、保存場所と、見られる人の管理は欠かせません。',na:true,
 fix:'フォームの送信先、保存される場所、見られる人を整理し、プライバシーポリシーを載せましょう。'},
{id:'incident',q:'改ざんやサイト停止が起きたとき、誰に連絡し、何をするかを、決めていますか？',why:'起きた直後の対応が遅れると、被害が広がります。',na:false,
 fix:'連絡先（制作会社、サーバー会社、担当者）と、最初にやることを、メモにしておきましょう。'},
{id:'maintain',q:'ホームページの更新や点検を、継続して担当している人（または会社）が、決まっていますか？',why:'安全は、作ったときではなく、保ち続けることで決まります。',na:false,
 fix:'担当を決めましょう。自社で難しい場合は、保守を引き受ける会社に相談する方法があります。'}
];
var form=document.getElementById('sc-form'),res=document.getElementById('sc-result'),err=document.getElementById('sc-err');
form.innerHTML=Q.map(function(x,i){
 var o='<label><input type="radio" name="'+x.id+'" value="yes"> はい</label><label><input type="radio" name="'+x.id+'" value="no"> いいえ</label><label><input type="radio" name="'+x.id+'" value="unknown"> わからない</label>';
 if(x.na) o+='<label><input type="radio" name="'+x.id+'" value="na"> 該当しない</label>';
 return '<fieldset class="q" id="q-'+x.id+'"><legend>'+(i+1)+'. '+x.q+'</legend><p class="why">'+x.why+'</p>'+o+'</fieldset>';
}).join('');
function ga(n,p){try{if(window.gtag)gtag('event',n,p||{});}catch(e){}}
function tier(n){return n===0?'ok':(n<=3?'mid':'ng');}
var MSG={
 ok:{badge:'心配な点は、見つかりませんでした',h:'この簡易チェックの範囲では、心配な点は見つかりませんでした。',
  p:'ただし、これで安心とは言い切れません。ホームページの安全は、更新や点検を続けることで保たれます。',
  cta:'毎月の更新・点検をお任せいただく保守プラン（ライト 月5,000円〜、スタンダード 月15,000円〜、システム保守 月30,000円〜／税込、最低契約6か月）もあります。古くなったサイトを、安心して使える状態に見直す（リフレッシュする）ご相談も承ります。'},
 mid:{badge:'いくつか確認したい点があります',h:'いくつか、確認したい点がありました。',
  p:'今すぐ問題があるとは限りませんが、早めに手を打っておくと安心です。下の項目から、順に確認してみてください。',
  cta:'「自分で直すのは難しい」「何から手を付ければよいか分からない」という場合は、ご相談ください。現状をうかがい、優先順位をつけてお伝えします（ヒアリングは無料）。点検や更新をお任せいただく保守プランもあります。'},
 ng:{badge:'早めの確認をおすすめします',h:'心配な点が、いくつかありました。早めの確認をおすすめします。',
  p:'「わからない」も、確認が必要な項目に数えています。分からないことは、ホームページの管理で、ごく普通のことです。まずは、下の項目を1つずつ確認しましょう。',
  cta:'一人で抱え込まず、ご相談ください。現状をうかがい、何を・どの順番で直すかをお伝えします（ヒアリングは無料）。状態によっては、サイトの見直し（リフレッシュ）や、保守プランで、継続的に守る方法もご提案できます。'}
};
function build(){
 var miss=[],ans={};
 Q.forEach(function(x){var el=form.querySelector('input[name="'+x.id+'"]:checked');ans[x.id]=el?el.value:null;document.getElementById('q-'+x.id).classList.remove('miss');if(!el)miss.push(x);});
 if(miss.length){err.textContent='まだ答えていない質問が '+miss.length+' 件あります。';miss.forEach(function(x){document.getElementById('q-'+x.id).classList.add('miss');});document.getElementById('q-'+miss[0].id).scrollIntoView({behavior:'smooth',block:'center'});return;}
 err.textContent='';
 var flags=Q.filter(function(x){return ans[x.id]==='no'||ans[x.id]==='unknown';});
 var n=flags.length,t=tier(n),m=MSG[t];var tot=Q.filter(function(x){return ans[x.id]!=='na';}).length;
 var list=flags.length?'<ul>'+flags.map(function(x){return '<li><b>'+x.q.replace(/（[^）]*）/g,'')+'</b><br>'+(ans[x.id]==='unknown'?'まず、確認しましょう。':'')+x.fix+'</li>';}).join('')+'</ul>':'';
 var txt='【ホームページのセキュリティ セルフチェック結果】\n確認が必要な項目：'+n+' / '+Q.length+'件\n'+flags.map(function(x,i){return (i+1)+'. '+x.q.replace(/（[^）]*）/g,'');}).join('\n');
 res.innerHTML='<span class="badge '+t+'">'+m.badge+'</span><h2>'+m.h+'</h2><p>確認が必要な項目：<b>'+n+' / '+tot+'件</b></p><p>'+m.p+'</p>'+list+
 '<div class="cta-box"><p>'+m.cta+'</p><div class="actions"><a class="btn" data-cta="result" href="https://lin.ee/SvN5SIm" target="_blank" rel="noopener">LINEで無料相談する →</a><button type="button" class="btn ghost" id="sc-copy">結果をコピー</button></div><p class="note" id="sc-copied">「結果をコピー」で、結果の要点をコピーできます。相談のときに、貼り付けてください。</p></div>'+
 '<p class="note">この診断は、質問への回答をもとにした簡易チェックです。実際のサイトを調べてはおらず、安全を保証するものでもありません。入力内容は、この端末の中だけで処理され、送信されません。</p>';
 res.classList.add('show');res.scrollIntoView({behavior:'smooth',block:'start'});
 ga('security_check_complete',{tier:t,flagged:n});
 document.getElementById('sc-copy').onclick=function(){
  var done=function(){document.getElementById('sc-copied').textContent='コピーしました。LINEやフォームに貼り付けてください。';};
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,function(){});}
  else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(ta);}
 };
}
document.getElementById('sc-run').onclick=build;
document.getElementById('sc-reset').onclick=function(){form.reset();res.classList.remove('show');res.innerHTML='';err.textContent='';Array.prototype.forEach.call(form.querySelectorAll('.q'),function(e){e.classList.remove('miss');});window.scrollTo({top:0,behavior:'smooth'});};
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-cta]');if(a)ga('security_check_cta',{place:a.getAttribute('data-cta')});});
})();
"""

SEC_BODY = """<section class="blk">
  <div class="wrap tool">
    <p class="lead">12の質問に答えるだけで、ホームページの「守り」に、確認したい点がないかを、すぐに調べられます。所要時間は、3分ほどです。分からない質問は、「わからない」を選んでください。</p>
    <p class="note">入力内容は、この端末の中だけで処理され、送信されません。登録も不要です。</p>
    <form id="sc-form" onsubmit="return false"></form>
    <div class="actions"><button type="button" class="btn" id="sc-run">結果を見る</button><button type="button" class="btn ghost" id="sc-reset">やり直す</button></div>
    <p class="err" id="sc-err" role="alert"></p>
    <div class="result" id="sc-result" aria-live="polite"></div>
    <p class="note" style="margin-top:40px">""" + LEAD + """あわせて、<a href="/column-security.html">ホームページのセキュリティの基本</a>、<a href="/tools/php-check.html">PHPバージョン診断</a>もご覧ください。</p>
    """ + related() + """
  </div>
</section>
"""

# ------------------------------------------------------------------ PHP診断
PHP_JS = r"""
(function(){
var FIXED={'8.2':35,'8.3':36,'8.4':27,'8.5':12};
var EOL82='<p><b>PHP 8.2 をお使いの方へ：</b>PHP の公式サイト（php.net）によると、PHP 8.2 のセキュリティサポートは、2026年12月31日に終了します。年内に、8.3 以降への移行を計画してください。</p>';
var inp=document.getElementById('php-in'),res=document.getElementById('php-result'),err=document.getElementById('php-err');
function ga(n,p){try{if(window.gtag)gtag('event',n,p||{});}catch(e){}}
function show(t,badge,h,body){
 res.innerHTML='<span class="badge '+t+'">'+badge+'</span><h2>'+h+'</h2>'+body+
 '<div class="cta-box"><p>更新や、新しいバージョンへの移行の作業が不安な場合は、ご相談ください。現状をうかがい、何を・どの順番で行うかをお伝えします（ヒアリングは無料）。更新や点検をお任せいただく保守プランもあります（ライト 月5,000円〜／税込、最低契約6か月）。</p><div class="actions"><a class="btn" data-cta="result" href="https://lin.ee/SvN5SIm" target="_blank" rel="noopener">LINEで無料相談する →</a></div></div>'+
 '<p class="note">この診断は、入力されたバージョン番号だけをもとにした簡易判定です。実際のサイトは調べていません。サーバー会社が、バージョン表示を変えずに対策のプログラムだけを適用している場合もあるため、不明なときは、サーバー会社に確認してください。判定の基準は、IPAの注意喚起（2026年10月22日公開、10月27日更新）と、PHP の公式サイト（php.net）にもとづきます。最新の情報は、<a href="https://www.ipa.go.jp/security/security-alert/2026/alert20261022.html" target="_blank" rel="noopener">IPAのページ</a>でご確認ください。入力内容は、この端末の中だけで処理され、送信されません。</p>';
 res.classList.add('show');res.scrollIntoView({behavior:'smooth',block:'start'});
}
function run(){
 var v=(inp.value||'').trim().replace(/^php\s*/i,'');
 var m=v.match(/^(\d+)\.(\d+)(?:\.(\d+))?/);
 res.classList.remove('show');
 if(!m){err.textContent='「8.3.30」のように、数字とピリオドで入力してください。';return;}
 err.textContent='';
 var maj=+m[1],min=+m[2],pat=m[3]===undefined?null:+m[3],key=maj+'.'+min,t,r;
 if(maj<8||(maj===8&&min<=1)){
  t='ng';r='eol';
  show('ng','移行が必要です','PHP '+key+' は、サポートが終了しています。','<p>IPAは、PHP 8.1 以前は、サポートが終了しているため、修正プログラムが提供されないとしています。サポートされている版（8.2〜8.5）への移行が必要です。</p><ul><li><b>まずやること：</b>制作会社やサーバー会社に、移行できるかを確認します。</li><li><b>対策済みの場合もあります：</b>Linux の配布元や、長期サポートを提供する事業者が、独自に対策した版を出している場合があり、そのときは、バージョンの表示が古くても、対策が済んでいることがあります。サーバー会社に確認してください。</li><li><b>注意：</b>WordPress のテーマやプラグインが、新しいPHPに対応していないことがあります。バックアップを取り、確認してから移行します。</li></ul>');
 }else if(FIXED[key]!==undefined){
  if(pat===null){
   err.textContent='パッチ番号まで入力してください（例：'+key+'.30）。';return;
  }
  if(pat<FIXED[key]){t='ng';r='old';
   show('ng','更新が必要です','PHP '+v+' は、修正版より古い版です。','<p>この脆弱性の修正版は、PHP '+key+' 系では <b>'+key+'.'+FIXED[key]+'</b> 以降です。いまの版は、それより古いため、更新が必要です。</p><ul><li><b>まずやること：</b>制作会社やサーバー会社に、'+key+'.'+FIXED[key]+' 以降への更新を依頼します。</li><li><b>更新の前に：</b>バックアップを取ります。</li></ul>'+(key==='8.2'?EOL82:''));
  }else{t='ok';r='fixed';
   show('ok','この脆弱性については、修正版以降です','PHP '+v+' は、修正版以降の版です。','<p>この脆弱性（CVE-2026-109618・CVE-2026-109619）については、修正版（'+key+'.'+FIXED[key]+'）以降なので、対策済みと考えられます。</p><p>ただし、ほかのシステム（WordPress 本体、プラグイン、テーマ）にも、更新が必要なものがないかを、あわせて確認してください。</p>'+(key==='8.2'?EOL82:''));
  }
 }else{
  t='mid';r='unknown';
  show('mid','確認をおすすめします','PHP '+key+' は、この診断の想定にない版です。','<p>この診断は、PHP 5〜8.5 を想定しています。IPAの最新の情報を確認してください。</p>');
 }
 ga('php_check_complete',{result:r});
}
document.getElementById('php-run').onclick=run;
inp.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();run();}});
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-cta]');if(a)ga('php_check_cta',{place:a.getAttribute('data-cta')});});
})();
"""

PHP_BODY = """<section class="blk">
  <div class="wrap tool">
    <p class="lead">2026年10月、PHP の重大な脆弱性（PHP2shell）が公表されました。自分のホームページが使っているPHPのバージョンを入れると、更新が必要かを、すぐに判定します。</p>
    <p class="note">入力内容は、この端末の中だけで処理され、送信されません。登録も不要です。</p>
    <div style="margin-top:28px">
      <label for="php-in" style="display:block;font-size:13px;font-weight:500;margin-bottom:10px">PHP のバージョン（例：8.3.30）</label>
      <input type="text" id="php-in" placeholder="8.3.30" inputmode="decimal" autocomplete="off">
    </div>
    <div class="actions"><button type="button" class="btn" id="php-run">判定する</button></div>
    <p class="err" id="php-err" role="alert"></p>
    <div class="result" id="php-result" aria-live="polite"></div>
    <h2 class="h2" style="margin-top:56px;font-size:20px">PHP のバージョンの調べ方</h2>
    <ul style="margin:14px 0 0 1.2em;max-width:760px">
      <li style="font-size:13px;line-height:2.2;color:var(--gray-dark)">制作を依頼した会社や、サーバー会社に、「PHPのバージョンを教えてください」と聞くのが確実です。</li>
      <li style="font-size:13px;line-height:2.2;color:var(--gray-dark)">WordPress の場合は、管理画面の「ツール」→「サイトヘルス」→「情報」→「サーバー」で見られます。</li>
      <li style="font-size:13px;line-height:2.2;color:var(--gray-dark)">サーバーの管理画面に、PHPの設定（バージョン）の項目がある場合もあります。</li>
    </ul>
    <p class="note" style="margin-top:32px">""" + LEAD + """背景は、<a href="/column-security.html">ホームページのセキュリティ、何を確認すればいい？</a>で解説しています。ほかの項目も確認したい方は、<a href="/tools/security-check.html">セキュリティのセルフチェック</a>をお使いください。</p>
    """ + related() + """
  </div>
</section>
"""

IDX_BODY = """<section class="blk">
  <div class="wrap">
    <p class="lead">ホームページを「作る」だけでなく、公開後に「守る」ための、無料の診断です。どちらも登録は不要で、入力内容は、この端末の中だけで処理されます。</p>
    <div class="tcards">
      <a href="/tools/security-check.html"><span>Self Check / 3 min</span><h3>ホームページのセキュリティチェック</h3><p>12の質問に答えて、更新・パスワード・バックアップなど、「守り」の確認したい点を調べます。</p></a>
      <a href="/tools/php-check.html"><span>PHP / 1 min</span><h3>PHP脆弱性チェック（PHPバージョン診断）</h3><p>2026年10月に公表されたPHPの脆弱性について、バージョンを入れると、更新が必要かを判定します。</p></a>
    </div>
    <p class="note" style="margin-top:32px">""" + LEAD + """保守プランは、ライト 月5,000円〜、スタンダード 月15,000円〜、システム保守 月30,000円〜（税込、最低契約6か月）です。詳しくは<a href="/index.html#maintenance">保守・運用</a>をご覧ください。</p>
  </div>
</section>
"""

SEC_FAQ = [
 ("ホームページのセキュリティチェックでは、何を調べますか？", "更新、パスワード、二段階認証、バックアップ、アカウント、SSL、個人情報の扱い、緊急時の連絡など、12の項目について、質問に答える形で確認します。実際のサイトを調べる診断ではありません。"),
 ("入力した内容は、送信されますか？", "いいえ。入力内容は、お使いの端末の中だけで処理され、当方のサーバーには送信されません。登録も不要です。"),
 ("「心配な点は見つかりませんでした」と出れば、安全ですか？", "安全を保証するものではありません。簡易チェックの範囲では、気になる点がなかったということです。ホームページの安全は、更新や点検を続けることで保たれます。"),
 ("心配な点があると出ました。どうすればよいですか？", "結果に表示される、項目ごとの対処のヒントを、順に確認してください。自分での対応が難しい場合は、ご相談ください（ヒアリングは無料です）。"),
 ("ホームページが改ざんされた場合は、どうすればよいですか？", "直ちにサービスを止め、ログを保存し、警察などに相談する流れを、警察庁が案内しています。詳しくは、<a href=\"/blog/website-hacked-what-to-do.html\">改ざん・乗っ取りされたら？初動対応と日頃の備え</a>をご覧ください。"),
]
PHP_FAQ = [
 ("PHP2shell とは何ですか？", "2026年10月に公表された、PHP の2件の脆弱性（CVE-2026-109618、CVE-2026-109619）を組み合わせた通称です。条件がそろうと、外部の第三者が、サーバー上でプログラムを実行できてしまうおそれがあります。詳しくは、<a href=\"/blog/php2shell-explained.html\">PHP2shell とは？何が問題で、何をすればいい？</a>をご覧ください。"),
 ("WordPress は、PHP の脆弱性の影響を受けますか？", "WordPress は PHP で動いているため、PHP のバージョンが修正版より古ければ、影響を受けうります。WordPress 本体の更新では、PHP のバージョンは変わりません。PHP は、サーバー側で更新します。詳しくは、<a href=\"/blog/wordpress-php-version-check.html\">WordPress は影響を受ける？PHPバージョンの確認方法</a>をご覧ください。"),
 ("PHP のバージョンは、どう確認しますか？", "制作会社やサーバー会社に聞くのが確実です。WordPress なら、管理画面の「ツール」→「サイトヘルス」→「情報」→「サーバー」で見られます。"),
 ("PHP 8.1 以前を使っています。どうなりますか？", "PHP のプロジェクトからは、更新が提供されません。ただし、Linux の配布元や、長期サポートの事業者が、独自に対策した版を出している場合があります。サーバー会社に確認し、必要なら、サポートされている版（8.2 〜 8.5）へ移行してください。"),
 ("PHP 8.2 を使っています。修正版にすれば安心ですか？", "この脆弱性については、8.2.35 以降で対策済みと考えられます。ただし、PHP 8.2 のセキュリティサポートは、2026年12月31日に終了します（php.net）。年内に、8.3 以降への移行を計画してください。"),
]

def update_sitemap_llms():
    p = ROOT / "sitemap.xml"; s = p.read_text(encoding="utf-8")
    s = re.sub(r"  <url>\s*<loc>https://kairos-web\.jp/tools/[^<]*</loc>.*?</url>\n", "", s, flags=re.S)
    add = "".join(f"  <url>\n    <loc>{B}tools/{x}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </url>\n" for x in ("", "security-check.html", "php-check.html"))
    s = s.replace("</urlset>", add + "</urlset>")
    p.write_text(s, encoding="utf-8", newline="")
    p = ROOT / "llms.txt"; s = p.read_text(encoding="utf-8")
    sec = (f"## セキュリティ簡易無料診断\n- [セキュリティ簡易無料診断]({B}tools/): ホームページの「守り」を確認できる、無料の診断ツール（登録不要、入力内容は端末内のみで処理）\n"
           f"- [ホームページのセキュリティチェック]({B}tools/security-check.html): 12の質問で、更新・パスワード・バックアップなどの確認したい点を調べる\n"
           f"- [PHP脆弱性チェック（PHPバージョン診断）]({B}tools/php-check.html): 2026年10月のPHPの脆弱性（IPAの注意喚起）について、バージョンから更新の要否を判定する\n\n")
    s = re.sub(r"## (?:セキュリティ簡易)?無料診断\n.*?(?=\n## |\Z)", "", s, flags=re.S)
    s = s.replace("## 問い合わせ", sec + "## 問い合わせ", 1) if "## 問い合わせ" in s else s.rstrip("\n") + "\n\n" + sec
    s = re.sub(r"\n{3,}", "\n\n", s)
    p.write_text(s, encoding="utf-8", newline="")

def main():
    for st in (sys.stdout, sys.stderr):
        try: st.reconfigure(encoding="utf-8")
        except Exception: pass
    OUT.mkdir(exist_ok=True)
    page("index.html", "セキュリティ簡易無料診断｜ホームページのセキュリティチェック・PHP脆弱性チェック｜Kairos",
         "ホームページのセキュリティチェックと、PHP脆弱性チェック（PHPバージョン診断）。登録不要・無料で、更新やバックアップなど「守り」の確認したい点を調べられます。蟹江町のKairos。",
         "セキュリティ簡易<br>無料診断", "公開後の「守り」を、無料で確認できます。", "セキュリティ簡易無料診断", IDX_BODY, "", "Kairos セキュリティ簡易無料診断")
    page("security-check.html", "ホームページのセキュリティチェック（無料）｜12の質問で確認｜Kairos",
         "ホームページのセキュリティチェックを、12の質問に答えるだけで。更新・パスワード・バックアップ・SSLなど、「守り」の確認したい点を、無料で調べられます。登録不要、入力内容は送信されません。",
         "ホームページの<br>セキュリティチェック（無料）", "12の質問で、確認したい点を調べます（無料・3分・登録不要）。", "セキュリティチェック", SEC_BODY, SEC_JS, "ホームページのセキュリティチェック", faq=SEC_FAQ)
    page("php-check.html", "PHP脆弱性チェック｜PHPバージョン確認と更新の要否を判定（無料）｜Kairos",
         "PHP脆弱性（PHP2shell、2026年10月公表）のチェックツール。PHPのバージョンを入れると、更新が必要かを無料で判定します。WordPressの方も。IPAの注意喚起にもとづく。",
         "PHP脆弱性チェック<br>（PHPバージョン診断）", "バージョンを入れると、更新が必要かを判定します（無料・1分・登録不要）。", "PHP脆弱性チェック", PHP_BODY, PHP_JS, "PHP脆弱性チェック（PHPバージョン診断）", faq=PHP_FAQ)
    update_sitemap_llms()
    print("完了：tools/ 3ページ")

if __name__ == "__main__":
    main()
