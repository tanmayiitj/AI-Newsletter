/* Archive page pagination interactions */
(function () {
    "use strict";

    /* Highlight current page link on load */
    var paginationLinks = document.querySelectorAll(".pagination a");
    paginationLinks.forEach(function (link) {
        link.addEventListener("click", function () {
            /* Add loading state feedback */
            link.style.opacity = "0.6";
            link.style.pointerEvents = "none";
        });
    });
})();
