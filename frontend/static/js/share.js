/* Share section link — Clipboard API with visual feedback */
(function () {
    "use strict";

    document.addEventListener("click", function (e) {
        var button = e.target.closest(".share-button");
        if (!button) return;

        /* Find the parent section's ID for the anchor link */
        var section = button.closest(".newsletter-section");
        var sectionId = section ? section.id : "";
        if (!sectionId) return;

        var url = window.location.origin + window.location.pathname + "#" + sectionId;

        navigator.clipboard.writeText(url).then(function () {
            showFeedback(button, "Copied!");
        }).catch(function () {
            /* Fallback for older browsers */
            fallbackCopy(url);
            showFeedback(button, "Copied!");
        });
    });

    function showFeedback(button, message) {
        var feedback = button.querySelector(".share-feedback");
        if (!feedback) return;

        feedback.textContent = message;
        button.classList.add("share-copied");

        setTimeout(function () {
            feedback.textContent = "";
            button.classList.remove("share-copied");
        }, 2000);
    }

    function fallbackCopy(text) {
        var textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
    }
})();
