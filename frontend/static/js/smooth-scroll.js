/* Smooth scroll to anchor on page load and on anchor link click */
(function () {
    "use strict";

    /* Scroll to hash on page load */
    if (window.location.hash) {
        var target = document.querySelector(window.location.hash);
        if (target) {
            /* Small delay to let the page render first */
            setTimeout(function () {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }, 100);
        }
    }

    /* Smooth scroll for in-page anchor clicks */
    document.addEventListener("click", function (e) {
        var link = e.target.closest('a[href^="#"]');
        if (!link) return;

        var hash = link.getAttribute("href");
        var target = document.querySelector(hash);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
            history.pushState(null, "", hash);
        }
    });
})();
