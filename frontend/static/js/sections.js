/* Section expand/collapse — collapsed by default, smooth toggle with state memory */
(function () {
    "use strict";

    var STORAGE_KEY = "aipulse-expanded";

    function getExpandedState() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        } catch (e) {
            return {};
        }
    }

    function saveExpandedState(state) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) { /* ignore */ }
    }

    function initSections() {
        var sections = document.querySelectorAll(".newsletter-section");
        var state = getExpandedState();

        sections.forEach(function (section) {
            var id = section.id;
            if (!id) return;

            /* Default: collapsed. Only expand if explicitly saved as expanded. */
            if (!state[id]) {
                section.classList.add("collapsed");
            }
        });
    }

    /* Delegate click on toggle buttons and section headers */
    document.addEventListener("click", function (e) {
        var toggle = e.target.closest(".section-toggle");
        var header = e.target.closest(".section-header");

        /* Don't toggle if clicking share button or links */
        if (e.target.closest(".share-button")) return;
        if (e.target.closest("a")) return;

        var target = toggle || header;
        if (!target) return;

        var section = target.closest(".newsletter-section");
        if (!section || !section.id) return;

        section.classList.toggle("collapsed");

        /* Persist state — save which sections are EXPANDED */
        var state = getExpandedState();
        if (section.classList.contains("collapsed")) {
            delete state[section.id];
        } else {
            state[section.id] = true;
        }
        saveExpandedState(state);
    });

    /* Init on DOM ready */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSections);
    } else {
        initSections();
    }
})();
