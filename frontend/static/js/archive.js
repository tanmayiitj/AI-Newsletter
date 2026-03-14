/* Archive page — live search + custom themed year/month dropdowns */
(function () {
    "use strict";

    var searchInput = document.getElementById("archive-search");
    var yearSelect = document.getElementById("year-filter");
    var monthSelect = document.getElementById("month-filter");
    var resultsContainer = document.getElementById("archive-results");
    var pagination = document.getElementById("archive-pagination");
    var statusEl = document.getElementById("search-status");
    var debounceTimer = null;

    if (!searchInput || !yearSelect || !monthSelect) return;

    /* ---- Custom dropdown logic ---- */
    function initCustomSelects() {
        document.querySelectorAll(".custom-select").forEach(function (sel) {
            var trigger = sel.querySelector(".select-trigger");
            var menu = sel.querySelector(".select-menu");
            var label = sel.querySelector(".select-label");

            trigger.addEventListener("click", function (e) {
                e.stopPropagation();
                document.querySelectorAll(".custom-select.open").forEach(function (s) {
                    if (s !== sel) s.classList.remove("open");
                });
                sel.classList.toggle("open");
            });

            menu.addEventListener("click", function (e) {
                var opt = e.target.closest(".select-option");
                if (!opt) return;
                menu.querySelectorAll(".select-option").forEach(function (o) {
                    o.classList.remove("selected");
                });
                opt.classList.add("selected");
                sel.setAttribute("data-value", opt.getAttribute("data-value"));
                label.textContent = opt.textContent;
                sel.classList.remove("open");
                onFilterChange();
            });
        });

        document.addEventListener("click", function () {
            document.querySelectorAll(".custom-select.open").forEach(function (s) {
                s.classList.remove("open");
            });
        });
    }

    function getFilterValue(selectEl) {
        return selectEl.getAttribute("data-value") || "";
    }

    /* ---- Search logic ---- */
    function formatDate(dateStr) {
        var d = new Date(dateStr);
        return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
    }

    function highlightText(text, query) {
        if (!query) return text;
        var escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        return text.replace(new RegExp("(" + escaped + ")", "gi"), "<mark>$1</mark>");
    }

    function renderResults(results, query) {
        if (results.length === 0) {
            resultsContainer.innerHTML =
                '<div class="empty-state"><h2>No newsletters found</h2>' +
                '<p>Try a different search term or adjust the filters.</p></div>';
            return;
        }
        var html = "";
        results.forEach(function (ed) {
            var headline = highlightText(ed.headline || "", query);
            var summary = ed.executive_summary || "";
            if (summary.length > 200) summary = summary.substring(0, 200) + "...";
            summary = highlightText(summary, query);
            var date = ed.created_at ? formatDate(ed.created_at) : "";
            html +=
                '<a href="/edition/' + ed.id + '" class="archive-item">' +
                '<h2 class="archive-item-title">' + headline + '</h2>' +
                '<p class="archive-item-summary">' + summary + '</p>' +
                '<p class="archive-item-meta">Edition #' + ed.edition_number + ' &middot; ' + date + '</p></a>';
        });
        resultsContainer.innerHTML = html;
    }

    function showStatus(text) {
        statusEl.textContent = text;
        statusEl.style.display = text ? "block" : "none";
    }

    function doSearch() {
        var q = searchInput.value.trim();
        var year = getFilterValue(yearSelect);
        var month = getFilterValue(monthSelect);

        if (pagination) pagination.style.display = "none";
        showStatus("Searching...");

        var url = "/api/v1/newsletter/search?limit=20";
        if (q) url += "&q=" + encodeURIComponent(q);
        if (year) url += "&year=" + encodeURIComponent(year);
        if (month) url += "&month=" + encodeURIComponent(month);

        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var results = data.results || [];
                var total = data.total || 0;
                var monthNames = ["", "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"];
                var statusText = total + " newsletter" + (total !== 1 ? "s" : "") + " found";
                if (q) statusText += ' for "' + q + '"';
                if (month) statusText += " in " + monthNames[parseInt(month, 10)];
                if (year) statusText += " " + year;
                showStatus(statusText);
                renderResults(results, q);
            })
            .catch(function () {
                showStatus("Search failed. Please try again.");
            });
    }

    function onFilterChange() {
        clearTimeout(debounceTimer);
        doSearch();
    }

    searchInput.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(doSearch, 400);
    });

    searchInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            clearTimeout(debounceTimer);
            doSearch();
        }
    });

    initCustomSelects();
})();
