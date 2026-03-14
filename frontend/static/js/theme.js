/* Theme switcher — light / dark / warm with localStorage persistence */
(function () {
    "use strict";

    var STORAGE_KEY = "aipulse-theme";
    var THEMES = ["light", "dark", "warm"];
    var ICONS = { light: "☀️", dark: "🌙", warm: "🍂" };
    var LABELS = { light: "Light", dark: "Dark", warm: "Warm" };
    var THEME_COLORS = { light: "#6366f1", dark: "#818cf8", warm: "#b45309" };

    function getTheme() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved && THEMES.indexOf(saved) !== -1) return saved;
        } catch (e) { /* ignore */ }
        return "light";
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* ignore */ }

        /* Update toggle button if it exists */
        var btn = document.querySelector(".theme-toggle");
        if (btn) {
            btn.setAttribute("aria-label", "Theme: " + LABELS[theme]);
            var icon = btn.querySelector(".theme-icon");
            var label = btn.querySelector(".theme-label");
            if (icon) icon.textContent = ICONS[theme];
            if (label) label.textContent = LABELS[theme];
        }

        /* Update mobile browser theme-color */
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute("content", THEME_COLORS[theme]);
    }

    function cycleTheme() {
        var current = getTheme();
        var idx = THEMES.indexOf(current);
        var next = THEMES[(idx + 1) % THEMES.length];
        applyTheme(next);
    }

    /* Apply immediately (also called from inline script in <head>) */
    applyTheme(getTheme());

    /* Bind click */
    document.addEventListener("click", function (e) {
        if (e.target.closest(".theme-toggle")) {
            cycleTheme();
        }
    });

    /* Re-apply on DOM ready to update button text */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            applyTheme(getTheme());
        });
    }
})();
