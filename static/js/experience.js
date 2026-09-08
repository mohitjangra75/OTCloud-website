/* OTCloud — interactive experience layer.
   Intro curtains, parallax play objects, card tilt, nav + scroll polish.
   Every effect is opt-out under prefers-reduced-motion and trimmed on small screens. */
(function () {
    'use strict';

    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    var desktop = function () { return window.innerWidth > 900; };

    /* ---------- Intro: logo, then the curtains open ---------- */
    (function intro() {
        var el = document.getElementById('intro');
        if (!el) return;
        var done = false;

        function finish() {
            if (done) return;
            done = true;
            document.body.classList.remove('intro-running');
            if (el.parentNode) el.parentNode.removeChild(el);
            document.dispatchEvent(new CustomEvent('otc:intro-done'));
        }

        if (reduced) { finish(); return; }

        document.body.classList.add('intro-running');
        // Hold on the logo, then part the curtains and hand over to the hero.
        setTimeout(function () { el.classList.add('open'); }, 1250);
        setTimeout(finish, 2450);
        // Never let a stalled animation trap the visitor
        setTimeout(finish, 4500);
    })();

    /* ---------- Header: scrolled state + reading progress ---------- */
    (function header() {
        var head = document.querySelector('.site-header');
        var bar = document.querySelector('.scroll-progress');
        if (!head && !bar) return;
        var ticking = false;

        function update() {
            ticking = false;
            var y = window.pageYOffset || document.documentElement.scrollTop;
            if (head) head.classList.toggle('scrolled', y > 24);
            if (bar) {
                var doc = document.documentElement;
                var max = (doc.scrollHeight - window.innerHeight) || 1;
                bar.style.width = Math.min(100, Math.max(0, (y / max) * 100)) + '%';
            }
        }
        window.addEventListener('scroll', function () {
            if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
        }, { passive: true });
        window.addEventListener('resize', update);
        update();
    })();

    /* ---------- Hero headings reveal word by word ---------- */
    (function words() {
        if (reduced) return;
        document.querySelectorAll('.hb-slide h1').forEach(function (h) {
            var walker = document.createTreeWalker(h, NodeFilter.SHOW_TEXT, null);
            var nodes = [];
            while (walker.nextNode()) nodes.push(walker.currentNode);
            var i = 0;
            nodes.forEach(function (node) {
                if (!node.textContent.trim()) return;
                var frag = document.createDocumentFragment();
                node.textContent.split(/(\s+)/).forEach(function (part) {
                    if (!part) return;
                    if (!part.trim()) { frag.appendChild(document.createTextNode(part)); return; }
                    var s = document.createElement('span');
                    s.className = 'w';
                    s.style.setProperty('--i', i++);
                    s.textContent = part;
                    frag.appendChild(s);
                });
                node.parentNode.replaceChild(frag, node);
            });
        });
    })();

    /* ---------- Play objects: cursor parallax + scroll drift ---------- */
    (function parallax() {
        var objs = Array.prototype.slice.call(document.querySelectorAll('.po'));
        if (!objs.length || reduced) return;

        var pointerX = 0, pointerY = 0, curX = 0, curY = 0, running = false;

        objs.forEach(function (o) {
            o._depth = parseFloat(o.dataset.depth) || 0.05;
            o._layer = o.closest('.play-layer') || o.parentNode;
        });

        function frame() {
            curX += (pointerX - curX) * 0.06;
            curY += (pointerY - curY) * 0.06;
            var scrollY = window.pageYOffset || 0;
            var moving = Math.abs(pointerX - curX) > 0.2 || Math.abs(pointerY - curY) > 0.2;

            var mid = scrollY + window.innerHeight / 2;
            objs.forEach(function (o) {
                if (o.offsetParent === null) return;                    // hidden on small screens
                var r = o._layer.getBoundingClientRect();
                // Zero drift when the object's section is centred in view; it drifts
                // gently as the section travels up or down the viewport.
                var drift = (mid - (r.top + scrollY + r.height / 2)) * o._depth * 0.14;
                drift = Math.max(-70, Math.min(70, drift));
                o.style.transform = 'translate3d(' + (curX * o._depth * 70).toFixed(2) + 'px,' +
                    (curY * o._depth * 70 + drift).toFixed(2) + 'px,0)';
            });

            if (moving || scrolling) { window.requestAnimationFrame(frame); }
            else { running = false; }
            scrolling = false;
        }
        var scrolling = false;
        function kick() { if (!running) { running = true; window.requestAnimationFrame(frame); } }

        if (fine) {
            window.addEventListener('pointermove', function (e) {
                if (!desktop()) return;
                pointerX = (e.clientX / window.innerWidth - 0.5) * 2;   // -1 … 1
                pointerY = (e.clientY / window.innerHeight - 0.5) * 2;
                kick();
            }, { passive: true });
        }
        window.addEventListener('scroll', function () { scrolling = true; kick(); }, { passive: true });
        window.addEventListener('resize', kick);
        kick();
    })();

    /* ---------- Cards: soft 3D tilt towards the cursor ---------- */
    (function tilt() {
        if (reduced) return;
        var SEL = '.sign8-card, .diff-card, .svcv-card, .ic-card, .tsl-card, .topic-card, .blog-card, .prog-card';
        var cards = Array.prototype.slice.call(document.querySelectorAll(SEL));
        if (!cards.length) return;

        cards.forEach(function (card) {
            card.setAttribute('data-tilt', '');
            card.addEventListener('pointerenter', function (e) {
                if (desktop() && e.pointerType !== 'touch') card.classList.add('tilting');
            });
            card.addEventListener('pointermove', function (e) {
                if (!desktop() || e.pointerType === 'touch') return;
                var r = card.getBoundingClientRect();
                var px = (e.clientX - r.left) / r.width - 0.5;
                var py = (e.clientY - r.top) / r.height - 0.5;
                card.style.transform = 'perspective(900px) rotateX(' + (-py * 5).toFixed(2) + 'deg) rotateY(' +
                    (px * 5).toFixed(2) + 'deg) translateY(-6px) scale(1.012)';
            });
            card.addEventListener('pointerleave', function () {
                card.classList.remove('tilting');
                card.style.transform = '';
            });
        });
    })();

    /* ---------- Reveal safety net ----------
       The page's IntersectionObserver handles reveals; this scroll-based check
       is a fallback so no section can ever stay invisible if IO misbehaves. */
    (function revealFallback() {
        var pending = Array.prototype.slice.call(document.querySelectorAll('.reveal'));
        if (!pending.length) return;
        var queued = false;

        function check() {
            queued = false;
            var vh = window.innerHeight;
            pending = pending.filter(function (el) {
                if (el.classList.contains('in')) return false;
                var r = el.getBoundingClientRect();
                if (r.top < vh * 0.94 && r.bottom > -40) { el.classList.add('in'); return false; }
                return true;
            });
        }
        function queue() { if (!queued) { queued = true; window.requestAnimationFrame(check); } }

        window.addEventListener('scroll', queue, { passive: true });
        window.addEventListener('resize', queue);
        window.addEventListener('load', check);
        document.addEventListener('otc:intro-done', check);
        setTimeout(check, 300);
        setTimeout(check, 1500);
        check();
    })();
})();
