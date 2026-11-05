/* Menu: sticky header shrink, desktop dropdown + mega menu, mobile drawer + accordion.
   Keyboard: Enter/Space toggle · ↓/↑ open and move through links · ←/→ move between
   top-level items (desktop) · Home/End · Esc closes and returns focus. */
(function () {
  var DESKTOP = window.matchMedia("(min-width: 1100px)");
  var HOVER_CLOSE_DELAY = 180;

  function init() {
    var header = document.getElementById("site-header");
    var nav = document.getElementById("primary-nav");
    if (!header || !nav) return;

    var overlay = header.querySelector("[data-nav-overlay]");
    var burger = header.querySelector("[data-nav-open]");
    var closeBtn = nav.querySelector("[data-nav-close]");
    var items = Array.prototype.slice.call(nav.querySelectorAll(".has-dropdown"));
    var topLinks = Array.prototype.slice.call(nav.querySelectorAll(".nav__list > .nav__item > .nav__link"));

    /* ---------- Header shrink on scroll ---------- */
    var ticking = false;
    function onScroll() {
      // two thresholds so tiny scrolls around one point don't flap the header
      var y = window.scrollY;
      var shrunk = header.classList.contains("is-scrolled");
      if (!shrunk && y > 48) header.classList.add("is-scrolled");
      else if (shrunk && y < 16) header.classList.remove("is-scrolled");
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) {
        requestAnimationFrame(onScroll);
        ticking = true;
      }
    }, { passive: true });
    onScroll();

    /* ---------- Dropdowns ---------- */
    function parts(item) {
      return { btn: item.querySelector(".nav__toggle"), panel: item.querySelector(".dropdown") };
    }

    function panelLinks(item) {
      return Array.prototype.slice.call(parts(item).panel.querySelectorAll("a[href]"));
    }

    function open(item) {
      items.forEach(function (other) {
        if (other !== item) close(other);
      });
      item.classList.add("is-open");
      parts(item).btn.setAttribute("aria-expanded", "true");
    }

    function close(item) {
      clearTimeout(item._closeTimer);
      item.classList.remove("is-open");
      item._hoverOpened = false;
      parts(item).btn.setAttribute("aria-expanded", "false");
    }

    function closeAll() {
      items.forEach(close);
    }

    function isOpen(item) {
      return item.classList.contains("is-open");
    }

    items.forEach(function (item) {
      var p = parts(item);

      // Click / tap toggles (desktop + mobile accordion)
      p.btn.addEventListener("click", function () {
        if (DESKTOP.matches && item._hoverOpened) {
          // already opened by hover: a click should keep it open, not flicker shut
          item._hoverOpened = false;
          return;
        }
        isOpen(item) ? close(item) : open(item);
      });

      // Hover (desktop, real mouse only)
      item.addEventListener("pointerenter", function (e) {
        if (!DESKTOP.matches || e.pointerType !== "mouse") return;
        clearTimeout(item._closeTimer);
        if (!isOpen(item)) {
          open(item);
          item._hoverOpened = true;
        }
      });
      item.addEventListener("pointerleave", function (e) {
        if (!DESKTOP.matches || e.pointerType !== "mouse") return;
        item._closeTimer = setTimeout(function () {
          close(item);
        }, HOVER_CLOSE_DELAY);
      });

      // Keyboard on the toggle button
      p.btn.addEventListener("keydown", function (e) {
        var links;
        if (e.key === "ArrowDown") {
          e.preventDefault();
          open(item);
          links = panelLinks(item);
          if (links[0]) requestAnimationFrame(function () { links[0].focus(); });
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          open(item);
          links = panelLinks(item);
          if (links.length) requestAnimationFrame(function () { links[links.length - 1].focus(); });
        }
      });

      // Keyboard inside the panel
      p.panel.addEventListener("keydown", function (e) {
        var links = panelLinks(item);
        var i = links.indexOf(document.activeElement);
        if (i === -1) return;
        var next = null;
        if (e.key === "ArrowDown") next = links[(i + 1) % links.length];
        else if (e.key === "ArrowUp") next = links[(i - 1 + links.length) % links.length];
        else if (e.key === "Home") next = links[0];
        else if (e.key === "End") next = links[links.length - 1];
        if (next) {
          e.preventDefault();
          next.focus();
        }
      });

      // Tabbing out of an open desktop panel closes it
      item.addEventListener("focusout", function (e) {
        if (!DESKTOP.matches) return;
        if (e.relatedTarget && item.contains(e.relatedTarget)) return;
        close(item);
      });
    });

    // ←/→ between top-level items on desktop
    topLinks.forEach(function (link, i) {
      link.addEventListener("keydown", function (e) {
        if (!DESKTOP.matches) return;
        var dir = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!dir) return;
        e.preventDefault();
        closeAll();
        topLinks[(i + dir + topLinks.length) % topLinks.length].focus();
      });
    });

    // Click outside closes desktop panels
    document.addEventListener("click", function (e) {
      if (DESKTOP.matches && !nav.contains(e.target)) closeAll();
    });

    /* ---------- Mobile drawer ---------- */
    function focusables() {
      return Array.prototype.slice.call(
        nav.querySelectorAll('a[href], button:not([disabled])')
      ).filter(function (el) {
        return el.offsetParent !== null && getComputedStyle(el).visibility !== "hidden";
      });
    }

    function openDrawer() {
      nav.classList.add("is-open");
      overlay.classList.add("is-visible");
      burger.setAttribute("aria-expanded", "true");
      burger.setAttribute("aria-label", "Close menu");
      document.body.classList.add("is-locked");
      nav.setAttribute("role", "dialog");
      nav.setAttribute("aria-modal", "true");
      setTimeout(function () { closeBtn.focus(); }, 60);
    }

    function closeDrawer(returnFocus) {
      if (!nav.classList.contains("is-open")) return;
      closeAll();
      nav.classList.remove("is-open");
      overlay.classList.remove("is-visible");
      burger.setAttribute("aria-expanded", "false");
      burger.setAttribute("aria-label", "Open menu");
      document.body.classList.remove("is-locked");
      nav.removeAttribute("role");
      nav.removeAttribute("aria-modal");
      if (returnFocus !== false) burger.focus();
    }

    burger.addEventListener("click", function () {
      nav.classList.contains("is-open") ? closeDrawer() : openDrawer();
    });
    closeBtn.addEventListener("click", function () { closeDrawer(); });
    overlay.addEventListener("click", function () { closeDrawer(); });

    // Following a link (incl. same-page #anchors) closes the drawer
    nav.addEventListener("click", function (e) {
      if (!DESKTOP.matches && e.target.closest("a[href]")) closeDrawer(false);
    });

    // Focus trap while the drawer is open
    nav.addEventListener("keydown", function (e) {
      if (e.key !== "Tab" || !nav.classList.contains("is-open")) return;
      var f = focusables();
      if (!f.length) return;
      var first = f[0];
      var last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    });

    /* ---------- Esc ---------- */
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (nav.classList.contains("is-open")) {
        closeDrawer();
        return;
      }
      var openItem = DESKTOP.matches && items.filter(isOpen)[0];
      if (openItem) {
        close(openItem);
        parts(openItem).btn.focus();
      }
    });

    // Switching between layouts resets state
    var onBreakpoint = function () {
      closeAll();
      closeDrawer(false);
    };
    DESKTOP.addEventListener ? DESKTOP.addEventListener("change", onBreakpoint) : DESKTOP.addListener(onBreakpoint);
  }

  if (window.__plakshaComponentsReady) init();
  else document.addEventListener("plaksha:components-ready", init, { once: true });
})();
