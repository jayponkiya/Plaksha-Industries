/* Animations: scroll reveals, counters, progress bar, light hero parallax, back-to-top,
   page fade transitions, button ripple, magnetic CTAs and in-page section highlighting.
   Pure JS (IntersectionObserver + one rAF-throttled scroll handler). Everything that
   moves is skipped when the visitor prefers reduced motion.

   Reveal markup:
     data-reveal                → fade-up (default)
     data-reveal="left|right"   → slide in from that side
     data-reveal="zoom"         → zoom-in
     data-reveal="clip"         → image wipe (clip-path)
     data-reveal-delay="120"    → delay in ms
     data-stagger (on a parent) → children reveal one after another, 100ms apart
   Plain data-reveal is upgraded automatically: split columns slide in from their side,
   images/illustrations wipe in, grid children stagger. */
(function () {
  var root = document.documentElement;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var $$ = function (sel, ctx) {
    return Array.prototype.slice.call((ctx || document).querySelectorAll(sel));
  };

  /* ==========================================================================
     Reveal on scroll
     ========================================================================== */
  var STAGGER_PARENTS = ".grid--cards, .area-list, .steps, .vmv-values__list, .reason-list, [data-stagger]";
  var MEDIA = ".illus, .hero__media, .media-frame, .map-frame, .hub";

  function upgrade(el) {
    if (el._upgraded) return;
    el._upgraded = true;
    if (el.getAttribute("data-reveal")) return; // explicit variant wins

    if (el.matches(MEDIA)) {
      el.setAttribute("data-reveal", "clip");
      return;
    }
    var parent = el.parentElement;
    if (parent && parent.matches(".vmv-values__list")) {
      el.setAttribute("data-reveal", "zoom");
    } else if (parent && parent.matches(".split, .reason") && window.innerWidth >= 900) {
      var box = el.getBoundingClientRect();
      var mid = parent.getBoundingClientRect().left + parent.offsetWidth / 2;
      el.setAttribute("data-reveal", box.left + box.width / 2 < mid ? "left" : "right");
    }
    if (parent && parent.matches(STAGGER_PARENTS)) {
      var i = Array.prototype.indexOf.call(parent.children, el);
      var step = parent.children.length > 6 ? i % 4 : Math.min(i, 5); // long grids: per row
      el.style.setProperty("--reveal-delay", step * 100 + "ms");
      el._staggered = true;
    }
  }

  function initReveal() {
    // children of [data-stagger] containers become reveal items
    $$("[data-stagger]").forEach(function (box) {
      Array.prototype.forEach.call(box.children, function (child) {
        if (!child.hasAttribute("data-reveal")) child.setAttribute("data-reveal", "");
      });
    });

    var els = $$("[data-reveal]:not(.is-revealed)");
    if (!els.length) return;

    if (reduce || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("is-revealed"); });
      return;
    }

    function reveal(watched) {
      var targets = watched._revealTargets || [];
      if (watched.hasAttribute("data-reveal") && targets.indexOf(watched) === -1) targets.push(watched);
      watched._revealTargets = null;
      io.unobserve(watched);
      watching.delete(watched);
      targets.forEach(function (el) {
        el.classList.add("is-revealed");
        // Once played, drop the reveal styles so hover lifts etc. use their own transitions
        var delay = parseFloat(getComputedStyle(el).getPropertyValue("--reveal-delay")) || 0;
        setTimeout(function () { el.removeAttribute("data-reveal"); }, delay + 950);
      });
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) reveal(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });

    var watching = new Set();
    els.forEach(function (el) {
      upgrade(el);
      var d = el.getAttribute("data-reveal-delay");
      if (d && !el._staggered) el.style.setProperty("--reveal-delay", d + "ms");
      var watched = el;
      if (el.getAttribute("data-reveal") === "clip") {
        // A fully clipped element has zero visible area, so the observer would never
        // report it. Watch an unclipped stand-in (its parent) and reveal the element from there.
        watched = el.parentElement;
        (watched._revealTargets = watched._revealTargets || []).push(el);
      }
      watching.add(watched);
      io.observe(watched);
    });

    // Safety sweep: a very fast scroll (or a busy main thread) can carry an element past the
    // viewport between two observer checks. Reveal anything the visitor has already reached.
    var sweepTimer = null;
    function sweep() {
      sweepTimer = null;
      var limit = window.innerHeight;
      watching.forEach(function (w) {
        if (w.getBoundingClientRect().top < limit) reveal(w);
      });
      if (!watching.size) window.removeEventListener("scroll", onScroll);
    }
    function onScroll() {
      if (!sweepTimer) sweepTimer = setTimeout(sweep, 200);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ==========================================================================
     Stat counters: <span data-count="25" data-suffix="+" data-pad="2">25+</span>
     The final value is in the markup, so no-JS / reduced-motion users see it as-is.
     ========================================================================== */
  function format(el, n) {
    var pad = parseInt(el.getAttribute("data-pad") || "0", 10);
    var s = String(Math.round(n));
    while (s.length < pad) s = "0" + s;
    return (el.getAttribute("data-prefix") || "") + s + (el.getAttribute("data-suffix") || "");
  }

  function countUp(el) {
    var to = parseFloat(el.getAttribute("data-count"));
    var from = parseFloat(el.getAttribute("data-from") || (to > 1000 ? to - 20 : 0));
    var dur = 1400;
    var start = null;
    function frame(t) {
      if (start === null) start = t;
      var p = Math.min((t - start) / dur, 1);
      el.textContent = format(el, from + (to - from) * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  function initCounters() {
    var els = $$("[data-count]");
    if (!els.length || reduce || !("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.unobserve(entry.target);
        countUp(entry.target);
      });
    }, { threshold: 0.6 });
    els.forEach(function (el) {
      var to = parseFloat(el.getAttribute("data-count"));
      el.textContent = format(el, parseFloat(el.getAttribute("data-from") || (to > 1000 ? to - 20 : 0)));
      io.observe(el);
    });
  }

  /* ==========================================================================
     Scroll-driven: progress bar, hero parallax, back-to-top (one rAF handler)
     ========================================================================== */
  function initScroll() {
    var bar = document.createElement("div");
    bar.className = "scroll-progress";
    bar.setAttribute("aria-hidden", "true");
    document.body.appendChild(bar);

    var top = document.createElement("button");
    top.type = "button";
    top.className = "to-top";
    top.setAttribute("aria-label", "Back to top");
    top.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg>';
    top.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
      var skip = document.querySelector(".skip-link");
      if (skip) skip.focus({ preventScroll: true });
    });
    document.body.appendChild(top);

    var hero = !reduce && document.querySelector(".hero, .page-banner");
    var ticking = false;

    function update() {
      var y = window.scrollY;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.setProperty("--progress", max > 0 ? Math.min(y / max, 1) : 0);
      top.classList.toggle("is-visible", y > 600);
      if (hero && y < hero.offsetHeight + 200) {
        hero.style.setProperty("--parallax", (y * 0.25).toFixed(1) + "px");
      }
      ticking = false;
    }

    window.addEventListener("scroll", function () {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }, { passive: true });
    window.addEventListener("resize", update, { passive: true });
    update();
  }

  /* ==========================================================================
     Page transition: fade out before following an internal link
     ========================================================================== */
  function initPageTransitions() {
    if (reduce) return;
    document.addEventListener("click", function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest && e.target.closest("a[href]");
      if (!a || a.target === "_blank" || a.hasAttribute("download")) return;
      var url = new URL(a.href, location.href);
      if (url.origin !== location.origin || !/(\.html?|\/)$/.test(url.pathname)) return;
      if (url.pathname === location.pathname && url.search === location.search) return; // same page / #anchor
      e.preventDefault();
      root.classList.add("is-leaving");
      setTimeout(function () { location.href = url.href; }, 180);
    });
    // Back/forward cache restores the faded page; undo it
    window.addEventListener("pageshow", function () {
      root.classList.remove("is-leaving");
    });
  }

  /* ==========================================================================
     Micro-interactions: ripple on buttons, magnetic CTAs
     ========================================================================== */
  function initRipple() {
    if (reduce) return;
    document.addEventListener("pointerdown", function (e) {
      var btn = e.target.closest && e.target.closest(".btn");
      if (!btn) return;
      var r = btn.getBoundingClientRect();
      var dot = document.createElement("span");
      dot.className = "ripple";
      dot.style.left = e.clientX - r.left + "px";
      dot.style.top = e.clientY - r.top + "px";
      dot.style.setProperty("--ripple-scale", Math.ceil(Math.max(r.width, r.height) / 8) + 2);
      btn.appendChild(dot);
      dot.addEventListener("animationend", function () { dot.remove(); });
    });
  }

  function initMagnetic() {
    if (reduce || !finePointer) return;
    $$(".hero__actions .btn--primary, .footer-cta__actions .btn--light, .header__cta").forEach(function (el) {
      el.setAttribute("data-magnetic", "");
      el.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width / 2) / (r.width / 2);
        var y = (e.clientY - r.top - r.height / 2) / (r.height / 2);
        el.style.transform = "translate(" + (x * 6).toFixed(1) + "px," + (y * 4).toFixed(1) + "px)";
      });
      el.addEventListener("pointerleave", function () {
        el.style.transform = "";
      });
    });
  }

  /* ==========================================================================
     Active section highlight: dropdown links to sections of this page (e.g.
     About → Vision & Mission) light up while that section is in view.
     ========================================================================== */
  function initSectionSpy() {
    if (!("IntersectionObserver" in window)) return;
    var page = location.pathname.split("/").pop() || "index.html";
    var map = {};
    $$(".primary-nav a[href*='#']").forEach(function (a) {
      var parts = a.getAttribute("href").split("#");
      if (parts[0] !== page) return;
      var target = document.getElementById(parts[1]);
      if (!target) return;
      (map[parts[1]] = map[parts[1]] || { el: target, links: [] }).links.push(a);
    });
    var ids = Object.keys(map);
    if (!ids.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        map[entry.target.id].links.forEach(function (a) {
          a.classList.toggle("is-active", entry.isIntersecting);
        });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    ids.forEach(function (id) { io.observe(map[id].el); });
  }

  /* ==========================================================================
     Boot
     ========================================================================== */
  initReveal();
  initCounters();
  initScroll();
  initPageTransitions();
  initRipple();

  function afterIncludes() {
    initReveal(); // anything injected with the header/footer
    initMagnetic();
    initSectionSpy();
  }
  if (window.__plakshaComponentsReady) afterIncludes();
  else document.addEventListener("plaksha:components-ready", afterIncludes, { once: true });

  // Preloader is CSS-timed (max ~1s); drop the class once it has played
  setTimeout(function () { root.classList.remove("is-preloading"); }, 1000);
})();
