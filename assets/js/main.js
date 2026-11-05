/* Main: shared components (header / footer include) + page UI modules.
   - Includes:  <div data-include="header"></div>  …  <div data-include="footer"></div>
                Fires "plaksha:components-ready" once all includes are in the DOM.
                fetch() needs the site served over http(s); file:// will not load them.
   - Tabs:      [data-tabs] with role="tablist" / role="tab" / role="tabpanel"
   - Accordion: [data-accordion] > .accordion__item > .accordion__trigger + .accordion__panel
   - Filter:    [data-filter-scope] with search, chip groups and [data-filter-item]s
   - Form:      form[data-enquiry-form] — validation, then Formspree (data-endpoint) or mailto */
(function () {
  var BASE = "components/";
  var $$ = function (sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  };

  /* ==========================================================================
     Includes
     ========================================================================== */
  function currentPage() {
    var file = location.pathname.split("/").pop() || "index.html";
    return file.replace(/\.html?$/, "") || "index";
  }

  function markActive() {
    var page = currentPage();
    $$(".nav__item[data-page]").forEach(function (item) {
      var pages = item.getAttribute("data-page").split(" ");
      if (pages.indexOf(page) === -1) return;
      item.classList.add("is-current");
      var link = item.querySelector(":scope > a.nav__link");
      if (link) link.setAttribute("aria-current", "page");
    });
    $$(".footer__links a").forEach(function (a) {
      if (a.getAttribute("href") === page + ".html") a.setAttribute("aria-current", "page");
    });
  }

  /* Footer CTA: a page can replace the default text with
     <body data-cta-title data-cta-text data-cta-href data-cta-label> (or hide it: data-cta="off") */
  function fillFooterCta() {
    var d = document.body.dataset;
    var slot = function (name) { return document.querySelector('[data-cta-slot="' + name + '"]'); };
    if (d.ctaTitle && slot("title")) slot("title").textContent = d.ctaTitle;
    if (d.ctaText && slot("text")) slot("text").textContent = d.ctaText;
    if (d.ctaLabel && slot("label")) slot("label").textContent = d.ctaLabel;
    if (d.ctaHref && slot("link")) slot("link").setAttribute("href", d.ctaHref);
  }

  function load(el) {
    var name = el.getAttribute("data-include");
    return fetch(BASE + name + ".html", { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) throw new Error(res.status + " " + res.statusText);
        return res.text();
      })
      .then(function (html) {
        el.outerHTML = html;
      })
      .catch(function (err) {
        console.error("[include] " + name + ".html failed:", err);
      });
  }

  /* ==========================================================================
     Tabs (ARIA tabs, automatic activation, ←/→/Home/End)
     ========================================================================== */
  function selectTab(tab, focus) {
    var list = tab.closest('[role="tablist"]');
    $$('[role="tab"]', list).forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(t.getAttribute("aria-controls"));
      if (!panel) return;
      panel.hidden = !on;
      if (on) {
        panel.classList.remove("is-entering");
        void panel.offsetWidth;
        panel.classList.add("is-entering");
      }
    });
    if (focus) tab.focus();
  }

  function initTabs() {
    $$('[data-tabs] [role="tablist"]').forEach(function (list) {
      var tabs = $$('[role="tab"]', list);
      tabs.forEach(function (tab, i) {
        tab.addEventListener("click", function () {
          selectTab(tab);
        });
        tab.addEventListener("keydown", function (e) {
          var next = null;
          if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
          else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
          else if (e.key === "Home") next = tabs[0];
          else if (e.key === "End") next = tabs[tabs.length - 1];
          if (next) {
            e.preventDefault();
            selectTab(next, true);
          }
        });
      });
    });
  }

  /* ==========================================================================
     Accordion
     ========================================================================== */
  function initAccordions() {
    $$("[data-accordion]").forEach(function (acc) {
      var single = acc.hasAttribute("data-accordion-single");
      $$(".accordion__trigger", acc).forEach(function (btn) {
        btn.addEventListener("click", function () {
          var item = btn.closest(".accordion__item");
          var open = !item.classList.contains("is-open");
          if (single && open) {
            $$(".accordion__item.is-open", acc).forEach(function (other) {
              other.classList.remove("is-open");
              other.querySelector(".accordion__trigger").setAttribute("aria-expanded", "false");
            });
          }
          item.classList.toggle("is-open", open);
          btn.setAttribute("aria-expanded", open ? "true" : "false");
        });
      });
    });
  }

  /* ==========================================================================
     Filter + search
     Item:  data-filter-item  data-<group>="a b"  (text is searched automatically)
     Chips: [data-filter-group="area"] > button.chip[data-filter="analgesic" | "all"]
     ========================================================================== */
  function initFilters() {
    $$("[data-filter-scope]").forEach(function (scope) {
      var search = scope.querySelector("[data-filter-search]");
      var items = $$("[data-filter-item]", scope);
      var groups = $$("[data-filter-group]", scope);
      var count = scope.querySelector("[data-filter-count]");
      var empty = scope.querySelector("[data-filter-empty]");
      var noun = scope.getAttribute("data-filter-noun") || "items";

      items.forEach(function (it) {
        it._text = it.textContent.replace(/\s+/g, " ").toLowerCase();
      });

      function apply() {
        var q = search ? search.value.trim().toLowerCase() : "";
        var active = groups.map(function (g) {
          var on = g.querySelector('[aria-pressed="true"]');
          return { name: g.getAttribute("data-filter-group"), value: on ? on.getAttribute("data-filter") : "all" };
        });
        var shown = 0;
        items.forEach(function (it) {
          var ok = !q || it._text.indexOf(q) !== -1;
          active.forEach(function (f) {
            if (!ok || f.value === "all") return;
            var tags = (it.getAttribute("data-" + f.name) || "").split(" ");
            ok = tags.indexOf(f.value) !== -1;
          });
          it.hidden = !ok;
          if (ok) shown++;
        });
        if (count) count.textContent = "Showing " + shown + " of " + items.length + " " + noun;
        if (empty) empty.hidden = shown !== 0;
      }

      function press(chip) {
        var group = chip.closest("[data-filter-group]");
        $$(".chip", group).forEach(function (c) {
          c.setAttribute("aria-pressed", c === chip ? "true" : "false");
        });
        apply();
      }

      groups.forEach(function (g) {
        $$(".chip", g).forEach(function (chip) {
          chip.addEventListener("click", function () {
            press(chip);
          });
        });
      });
      if (search) search.addEventListener("input", apply);

      $$("[data-filter-reset]", scope).forEach(function (btn) {
        btn.addEventListener("click", function () {
          if (search) search.value = "";
          groups.forEach(function (g) {
            var all = g.querySelector('[data-filter="all"]');
            if (all) press(all);
          });
          apply();
        });
      });

      // Allow #hash (e.g. products.html#analgesic) to pre-select a chip
      scope._selectByKey = function (key) {
        var chip = scope.querySelector('.chip[data-filter="' + key + '"]');
        if (!chip) return false;
        press(chip);
        return true;
      };

      apply();
    });
  }

  /* ==========================================================================
     #hash routing: open the tab / chip a link points at, then scroll to it
     ========================================================================== */
  function handleHash() {
    var key = decodeURIComponent(location.hash.slice(1));
    if (!key) return;
    var target = document.getElementById(key);
    var scrollTo = target;

    // Element inside a hidden tab panel (or the panel itself) → activate that tab
    var panel = target && (target.matches('[role="tabpanel"]') ? target : target.closest('[role="tabpanel"]'));
    if (panel) {
      var tab = document.querySelector('[role="tab"][aria-controls="' + panel.id + '"]');
      if (tab) selectTab(tab);
      if (target === panel) scrollTo = panel.closest("[data-tabs]") || panel;
    }

    // Key that matches a filter chip → apply it and scroll to the catalogue
    $$("[data-filter-scope]").forEach(function (scope) {
      if (scope._selectByKey && scope._selectByKey(key) && !target) scrollTo = scope;
    });

    if (target && target.matches("tr, [data-filter-item]")) {
      target.classList.remove("is-highlight");
      void target.offsetWidth;
      target.classList.add("is-highlight");
    }
    if (scrollTo) scrollTo.scrollIntoView({ block: "start" });
  }

  /* ==========================================================================
     Enquiry form: validation + Formspree / mailto
     ========================================================================== */
  var RULES = {
    name: function (v) { return v.length >= 2 || "Please enter your name."; },
    email: function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) || "Please enter a valid email address."; },
    phone: function (v) {
      if (!v) return true;
      return /^[+\d][\d\s\-()]{7,}$/.test(v) && v.replace(/\D/g, "").length >= 10 || "Please enter a valid phone number (at least 10 digits).";
    },
    interest: function (v) { return !!v || "Please choose a product interest."; },
    message: function (v) { return v.length >= 10 || "Please tell us a little more (at least 10 characters)."; }
  };

  function validateField(input) {
    var field = input.closest(".field");
    var rule = RULES[input.name];
    var value = input.value.trim();
    var result = true;
    if (input.required && !value) result = (field.querySelector("label").textContent.replace("*", "").trim()) + " is required.";
    else if (rule) result = rule(value);
    var error = field.querySelector(".field__error");
    var ok = result === true;
    field.classList.toggle("is-invalid", !ok);
    input.setAttribute("aria-invalid", ok ? "false" : "true");
    if (error) error.textContent = ok ? "" : result;
    return ok;
  }

  function prefillForm(form) {
    var params = new URLSearchParams(location.search);
    var interest = params.get("interest") || (params.get("enquiry") === "catalogue" ? "catalogue" : "");
    var product = params.get("product");
    var select = form.querySelector('[name="interest"]');
    var message = form.querySelector('[name="message"]');
    if (interest && select && select.querySelector('option[value="' + interest + '"]')) select.value = interest;
    if (product && message && !message.value) message.value = "Enquiry about: " + product + "\n\n";
    if (interest === "catalogue" && message && !message.value) message.value = "Please share your product catalogue.\n\n";
  }

  function initForms() {
    $$("form[data-enquiry-form]").forEach(function (form) {
      var status = form.querySelector(".form__status");
      var fields = $$(".input", form);
      prefillForm(form);

      fields.forEach(function (input) {
        input.addEventListener("blur", function () {
          if (input.value.trim() || input.getAttribute("aria-invalid") === "true") validateField(input);
        });
        input.addEventListener("input", function () {
          if (input.getAttribute("aria-invalid") === "true") validateField(input);
        });
      });

      form.addEventListener("submit", function (e) {
        e.preventDefault();
        status.className = "form__status";
        status.textContent = "";

        var firstBad = null;
        fields.forEach(function (input) {
          if (!validateField(input) && !firstBad) firstBad = input;
        });
        if (firstBad) {
          firstBad.focus();
          status.classList.add("is-error");
          status.textContent = "Please correct the highlighted fields.";
          return;
        }
        if (form.querySelector(".hp-field input").value) return; // bot

        var data = new FormData(form);
        var endpoint = form.getAttribute("data-endpoint");
        var btn = form.querySelector('[type="submit"]');

        if (endpoint) {
          btn.disabled = true;
          fetch(endpoint, { method: "POST", body: data, headers: { Accept: "application/json" } })
            .then(function (res) {
              if (!res.ok) throw new Error(res.status);
              form.reset();
              status.classList.add("is-success");
              status.textContent = "Thank you — your enquiry has been sent. We will get back to you shortly.";
            })
            .catch(function () {
              status.classList.add("is-error");
              status.textContent = "Sorry, the message could not be sent. Please email yogendra@plakshaindustries.com.";
            })
            .finally(function () {
              btn.disabled = false;
            });
          return;
        }

        // No endpoint configured → open the visitor's mail app with the enquiry filled in
        var select = form.querySelector('[name="interest"]');
        var interestLabel = select.options[select.selectedIndex].text;
        var body = [
          "Name: " + data.get("name"),
          "Company: " + (data.get("company") || "-"),
          "Email: " + data.get("email"),
          "Phone: " + (data.get("phone") || "-"),
          "Product interest: " + interestLabel,
          "",
          data.get("message")
        ].join("\n");
        var to = form.getAttribute("data-mailto") || "yogendra@plakshaindustries.com";
        location.href = "mailto:" + to + "?subject=" + encodeURIComponent("Website enquiry: " + interestLabel) +
          "&body=" + encodeURIComponent(body);
        status.classList.add("is-success");
        status.textContent = "Your email app should open with the enquiry ready to send. If it doesn't, email us at " + to + ".";
      });
    });
  }

  /* ==========================================================================
     Boot
     ========================================================================== */
  initTabs();
  initAccordions();
  initFilters();
  initForms();
  window.addEventListener("hashchange", handleHash);

  var slots = $$("[data-include]");
  Promise.all(slots.map(load)).then(function () {
    markActive();
    fillFooterCta();
    $$("[data-year]").forEach(function (el) {
      el.textContent = new Date().getFullYear();
    });
    window.__plakshaComponentsReady = true;
    document.dispatchEvent(new CustomEvent("plaksha:components-ready"));
    // Re-apply #hash now that the header height is known
    handleHash();
  });
})();
