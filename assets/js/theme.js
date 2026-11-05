/* Theme: light / dark.
   Loaded in <head> WITHOUT defer so the theme is applied before first paint.
   Order of preference: saved choice in localStorage → OS prefers-color-scheme.
   Also sets html.reduce-motion and html.is-preloading before paint. */
(function () {
  var KEY = "plaksha-theme";
  var root = document.documentElement;
  var media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function saved() {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  function preferred() {
    return saved() || (media && media.matches ? "dark" : "light");
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    var btns = document.querySelectorAll("[data-theme-toggle]");
    for (var i = 0; i < btns.length; i++) {
      btns[i].setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      btns[i].setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    }
  }

  function toggle() {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(KEY, next);
    } catch (e) {}
    apply(next);
  }

  apply(preferred());
  root.classList.remove("no-js");

  // Motion preferences + preloader (first page view of the session only)
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    root.classList.add("reduce-motion");
  } else {
    try {
      if (!sessionStorage.getItem("plaksha-seen")) {
        root.classList.add("is-preloading");
        sessionStorage.setItem("plaksha-seen", "1");
      }
    } catch (e) {}
  }

  // Follow OS changes only while the user hasn't chosen explicitly
  if (media && media.addEventListener) {
    media.addEventListener("change", function () {
      if (!saved()) apply(preferred());
    });
  }

  // Toggle button lives in the fetched header, so delegate the click
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest("[data-theme-toggle]")) toggle();
  });
  document.addEventListener("plaksha:components-ready", function () {
    apply(root.getAttribute("data-theme"));
  });

  window.PlakshaTheme = { apply: apply, toggle: toggle };
})();
