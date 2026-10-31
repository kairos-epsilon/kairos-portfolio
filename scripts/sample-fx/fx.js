/* Kairos sample FX — 制作サンプルを「豪華に」見せる共通の演出モジュール
 * 既存の文言・構成は変えず、演出だけを足す。GSAP が読めなくても内容は全部見える。
 * 設定: window.KFX = { accent:'#c8922a', mode:'rise'|'drift', light:false }
 *   accent … 光の粒・進捗線・カーソルの光の色
 *   mode   … rise=下から舞い上がる粒（火の粉・湯気）／ drift=漂ってカーソルに寄る粒
 *   light  … 明るい背景のサイトなら true（粒を加算合成にしない）
 *   exclude… この選択子の中は演出しない（既定：dialog・モーダル・ドロワー。開閉する部品で文字が透明のまま残るのを防ぐ）
 */
(function () {
  'use strict';
  var C = window.KFX || {};
  var accent = C.accent || '#c8922a';
  var mode = C.mode || 'drift';
  var light = !!C.light;
  var exclude = C.exclude || 'dialog,[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="drawer"]';
  var doc = document;
  var fine = window.matchMedia && matchMedia('(pointer:fine)').matches;
  var narrow = window.innerWidth < 768;

  function $(s, r) { return (r || doc).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); }
  function rgbOf(h) {
    h = String(h).replace('#', '');
    if (h.length === 3) h = h.replace(/./g, '$&$&');
    var n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  var rgb = rgbOf(accent);
  var rgbStr = rgb.join(',');

  /* ── CSS ── */
  var st = doc.createElement('style');
  st.setAttribute('data-kfx', '');
  st.textContent =
    ':root{--kfx:' + accent + ';--kfx-rgb:' + rgbStr + '}' +
    '.kfx-progress{position:fixed;top:0;left:0;right:0;height:3px;z-index:100000;pointer-events:none;background:linear-gradient(90deg,rgba(var(--kfx-rgb),.35),var(--kfx));transform-origin:0 50%;transform:scaleX(0);box-shadow:0 0 12px rgba(var(--kfx-rgb),.7)}' +
    '.kfx-glow{position:fixed;top:0;left:0;width:420px;height:420px;margin:-210px 0 0 -210px;border-radius:50%;pointer-events:none;z-index:99990;opacity:0;background:radial-gradient(circle,rgba(var(--kfx-rgb),' + (light ? '.16' : '.2') + ') 0%,rgba(var(--kfx-rgb),0) 65%);' + (light ? '' : 'mix-blend-mode:screen;') + 'transition:opacity .5s}' +
    '.kfx-glow.on{opacity:1}' +
    '.kfx-ch{display:inline-block;will-change:transform,opacity}' +
    '.kfx-w{display:inline-block;white-space:nowrap}' +
    '.kfx-cv{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:2' + (light ? '' : ';mix-blend-mode:screen') + '}' +
    '.kfx-blob{position:absolute;width:min(46vw,640px);aspect-ratio:1;border-radius:50%;pointer-events:none;z-index:-1;opacity:.5;' +
    'background:radial-gradient(circle,rgba(var(--kfx-rgb),' + (light ? '.12' : '.16') + ') 0%,rgba(var(--kfx-rgb),0) 68%)}' +
    '.kfx-blob.a{top:-8%;left:0}.kfx-blob.b{bottom:-8%;right:0}' +
    '.kfx-iso{position:relative;isolation:isolate}' +
    '@media(max-width:768px){.kfx-glow{display:none}}';
  doc.head.appendChild(st);

  /* ── 進捗線 ── */
  var bar = doc.createElement('div');
  bar.className = 'kfx-progress';
  doc.body.appendChild(bar);
  function onScroll() {
    var h = doc.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = 'scaleX(' + (h > 0 ? Math.min(1, window.scrollY / h) : 0) + ')';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ── カーソルの光 ── */
  var glow = null;
  if (fine) {
    glow = doc.createElement('div');
    glow.className = 'kfx-glow';
    doc.body.appendChild(glow);
    var gx = 0, gy = 0, tx = 0, ty = 0;
    window.addEventListener('pointermove', function (e) {
      tx = e.clientX; ty = e.clientY; glow.classList.add('on');
    }, { passive: true });
    doc.addEventListener('pointerleave', function () { glow.classList.remove('on'); });
    (function loop() {
      gx += (tx - gx) * 0.12; gy += (ty - gy) * 0.12;
      glow.style.transform = 'translate3d(' + gx + 'px,' + gy + 'px,0)';
      requestAnimationFrame(loop);
    })();
  }

  /* ── Hero を探す ── */
  function findHero() {
    var h = $('.hero,#hero,.hero-section,.main-visual,.mv,.fv,header.hero');
    if (h) return h;
    var cands = $$('section,header,div[class*="hero"]');
    for (var i = 0; i < cands.length; i++) {
      if (cands[i].offsetHeight > 360 && !cands[i].closest('nav')) return cands[i];
    }
    return null;
  }
  var hero = findHero();

  /* ── 光の粒（Hero の中） ── */
  function initParticles() {
    if (!hero) return;
    if (getComputedStyle(hero).position === 'static') hero.style.position = 'relative';
    var cv = doc.createElement('canvas');
    cv.className = 'kfx-cv';
    hero.appendChild(cv);
    var ctx = cv.getContext('2d');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0, ps = [];
    var N = narrow ? 44 : 90;
    var mx = -9999, my = -9999;
    function size() {
      W = hero.clientWidth; H = hero.clientHeight;
      cv.width = W * dpr; cv.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function spawn(initial) {
      return {
        x: Math.random() * W,
        y: mode === 'rise' ? (initial ? Math.random() * H : H + 10) : Math.random() * H,
        r: 0.6 + Math.random() * 2.2,
        vx: (Math.random() - 0.5) * 0.3,
        vy: mode === 'rise' ? -(0.25 + Math.random() * 0.9) : (Math.random() - 0.5) * 0.3,
        a: 0.25 + Math.random() * 0.6,
        t: Math.random() * 6.28
      };
    }
    size();
    for (var i = 0; i < N; i++) ps.push(spawn(true));
    hero.addEventListener('pointermove', function (e) {
      var b = hero.getBoundingClientRect();
      mx = e.clientX - b.left; my = e.clientY - b.top;
    }, { passive: true });
    hero.addEventListener('pointerleave', function () { mx = my = -9999; });
    window.addEventListener('resize', size);
    var visible = true;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) { visible = en[0].isIntersecting; }).observe(hero);
    }
    function frame() {
      requestAnimationFrame(frame);
      if (!visible) return;
      ctx.clearRect(0, 0, W, H);
      ctx.globalCompositeOperation = light ? 'source-over' : 'lighter';
      for (var i = 0; i < ps.length; i++) {
        var p = ps[i];
        p.t += 0.02;
        p.x += p.vx + Math.sin(p.t) * 0.25;
        p.y += p.vy;
        var dx = mx - p.x, dy = my - p.y, d2 = dx * dx + dy * dy;
        if (d2 < 22000) {
          var f = (1 - d2 / 22000) * (mode === 'rise' ? -0.5 : 0.6);
          p.x += dx * 0.004 * f * 10; p.y += dy * 0.004 * f * 10;
        }
        if (p.y < -12 || p.y > H + 14 || p.x < -12 || p.x > W + 12) {
          ps[i] = spawn(false);
          if (mode !== 'rise') { ps[i].x = Math.random() * W; ps[i].y = Math.random() * H; }
          continue;
        }
        var al = p.a * (mode === 'rise' ? Math.max(0, Math.min(1, p.y / (H * 0.9))) : 1);
        var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 6);
        g.addColorStop(0, 'rgba(' + rgbStr + ',' + al + ')');
        g.addColorStop(1, 'rgba(' + rgbStr + ',0)');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 6, 0, 6.2832); ctx.fill();
      }
    }
    frame();
  }
  initParticles();

  /* ── 文字を1つずつに分ける（中の要素はそのまま残す） ── */
  function splitChars(el) {
    var chars = [];
    var label = el.textContent.replace(/\s+/g, ' ').trim();
    function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var txt = n.nodeValue;
          if (!txt.trim() && txt.indexOf('\n') > -1) return;
          var frag = doc.createDocumentFragment();
          txt.split(/([A-Za-z0-9][A-Za-z0-9\-·.,'’&]*)/).forEach(function (part) {
            if (!part) return;
            if (/^[A-Za-z0-9]/.test(part)) {
              var w = doc.createElement('span'); w.className = 'kfx-w'; w.setAttribute('aria-hidden', 'true');
              part.split('').forEach(function (c) {
                var s = doc.createElement('span'); s.className = 'kfx-ch'; s.textContent = c; w.appendChild(s); chars.push(s);
              });
              frag.appendChild(w);
            } else {
              part.split('').forEach(function (c) {
                if (/\s/.test(c)) { frag.appendChild(doc.createTextNode(c)); return; }
                var s = doc.createElement('span'); s.className = 'kfx-ch'; s.setAttribute('aria-hidden', 'true'); s.textContent = c;
                frag.appendChild(s); chars.push(s);
              });
            }
          });
          node.replaceChild(frag, n);
        } else if (n.nodeType === 1 && n.tagName !== 'BR' && n.tagName !== 'SCRIPT') {
          walk(n);
        }
      });
    }
    walk(el);
    el.setAttribute('aria-label', label);
    return chars;
  }

  /* ── GSAP の演出 ── */
  function initGsap() {
    if (!window.gsap || !window.ScrollTrigger) return;
    gsap.registerPlugin(ScrollTrigger);
    var inHero = function (el) { return hero && hero.contains(el); };
    var hasLoader = !!$('.loading,.loader,#loader,#loading,.preloader');

    // 見出し：1文字ずつ立ち上がる
    var tsel = (C.titles || 'h1,h2,[class*="sec-title"],[class*="section-title"],[class*="-quote"],[class*="catch"],[class*="hero-title"]');
    $$(tsel).forEach(function (el) {
      if (el.closest('nav,footer') || el.closest(exclude) || el.dataset.kfx) return;
      if (el.textContent.trim().length === 0 || el.textContent.trim().length > 60) return;
      if (el.querySelector('img,svg,video,canvas')) return;
      el.dataset.kfx = '1';
      var chars = splitChars(el);
      if (!chars.length) return;
      var each = Math.min(0.05, 0.9 / chars.length);
      var vars = { opacity: 0, y: '0.55em', rotateX: -50, filter: 'blur(8px)', duration: 1, ease: 'power3.out', stagger: each, transformOrigin: '50% 100%' };
      if (inHero(el)) {
        vars.delay = hasLoader ? 1.1 : 0.25;
      } else {
        vars.scrollTrigger = { trigger: el, start: 'top 88%', once: true };
      }
      gsap.from(chars, vars);
    });

    // Hero：スクロールで中身が奥へ引き込まれる
    if (hero) {
      var hc = $('[class*="hero-content"],[class*="hero-inner"],[class*="hero-text"]', hero);
      if (hc) {
        gsap.to(hc, { y: -90, ease: 'none', scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true } });
      }
    }

    // 写真：下から幕が上がるように現れる
    var isel = (C.images || 'img,[class*="-img"]:not([class*="wrap"]),[class*="photo"],[class*="thumb"]');
    $$(isel).forEach(function (el) {
      if (inHero(el) || el.closest('nav,footer,[class*="logo"]') || el.closest(exclude)) return;
      if (el.offsetWidth < 200 || el.offsetHeight < 140) return;
      gsap.from(el, {
        clipPath: 'inset(0 0 100% 0)', scale: 1.14, duration: 1.5, ease: 'expo.out',
        clearProps: 'clipPath,transform',
        scrollTrigger: { trigger: el, start: 'top 90%', once: true }
      });
    });

    // 価格などの数字：数え上げ
    $$('[class*="price"]').forEach(function (el) {
      if (el.children.length || el.closest(exclude)) return;
      var m = el.textContent.match(/[\d][\d,]*/);
      if (!m) return;
      var target = parseInt(m[0].replace(/,/g, ''), 10);
      if (!(target > 9)) return;
      var tpl = el.textContent;
      var o = { v: 0 };
      gsap.to(o, {
        v: target, duration: 1.6, ease: 'power2.out',
        onUpdate: function () { el.textContent = tpl.replace(m[0], Math.round(o.v).toLocaleString('en-US')); },
        onComplete: function () { el.textContent = tpl; },
        scrollTrigger: { trigger: el, start: 'top 92%', once: true }
      });
    });

    // セクションの奥で光の玉がゆっくり動く
    $$('section').forEach(function (sec, i) {
      if (sec === hero || sec.offsetHeight < 300) return;
      if (getComputedStyle(sec).position === 'static') sec.classList.add('kfx-iso');
      else sec.style.isolation = 'isolate';
      var a = doc.createElement('div'); a.className = 'kfx-blob a';
      var b = doc.createElement('div'); b.className = 'kfx-blob b';
      sec.appendChild(a); sec.appendChild(b);
      gsap.fromTo(a, { y: -80 }, { y: 120, ease: 'none', scrollTrigger: { trigger: sec, start: 'top bottom', end: 'bottom top', scrub: true } });
      gsap.fromTo(b, { y: 100 }, { y: -140, ease: 'none', scrollTrigger: { trigger: sec, start: 'top bottom', end: 'bottom top', scrub: true } });
    });

    // ボタンが指に吸い付く
    if (fine) {
      $$('a[class*="btn"],button[class*="btn"],a[class*="cta"]').forEach(function (el) {
        if (el.closest(exclude)) return;
        el.addEventListener('pointermove', function (e) {
          var r = el.getBoundingClientRect();
          gsap.to(el, { x: (e.clientX - r.left - r.width / 2) * 0.25, y: (e.clientY - r.top - r.height / 2) * 0.4, duration: 0.4, ease: 'power3.out', overwrite: 'auto' });
        });
        el.addEventListener('pointerleave', function () {
          gsap.to(el, { x: 0, y: 0, duration: 0.8, ease: 'elastic.out(1,0.45)', overwrite: 'auto', clearProps: 'x,y' });
        });
      });
    }

    window.addEventListener('load', function () { ScrollTrigger.refresh(); });
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { ScrollTrigger.refresh(); });
  }

  if (window.gsap && window.ScrollTrigger) initGsap();
  else window.addEventListener('load', initGsap);
})();
