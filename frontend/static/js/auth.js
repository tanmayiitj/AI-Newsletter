/*
 * Auth UI — Google login/logout, profile avatar dropdown,
 * and "Send to My Email" button handler.
 */
(function () {
    "use strict";

    var TOAST_DURATION = 4000;
    var STORAGE_KEY = "aipulse-user";

    /* ---- Instant restore from cache (no flash) ---- */
    try {
        var cached = localStorage.getItem(STORAGE_KEY);
        if (cached) {
            var user = JSON.parse(cached);
            if (user && user.email) applyLoggedInUI(user);
        }
    } catch (e) { /* ignore */ }

    /* ---- State check on page load ---- */
    document.addEventListener("DOMContentLoaded", function () {
        checkAuthState();
        bindDropdownToggle();
        bindLogout();
        bindSendToSelf();
    });

    function checkAuthState() {
        fetch("/auth/me", { credentials: "same-origin" })
            .then(function (res) {
                if (!res.ok) throw new Error("Not logged in");
                return res.json();
            })
            .then(function (user) {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
                showLoggedIn(user);
            })
            .catch(function () {
                localStorage.removeItem(STORAGE_KEY);
                showLoggedOut();
            });
    }

    /* ---- UI toggling ---- */

    function applyLoggedInUI(user) {
        var loginBtn = document.getElementById("auth-login-btn");
        var profile = document.getElementById("auth-profile");
        var avatar = document.getElementById("auth-avatar-img");
        var emailEl = document.getElementById("auth-dropdown-email");

        if (loginBtn) loginBtn.style.display = "none";
        if (profile) profile.style.display = "block";
        if (avatar) {
            avatar.src = user.picture || "";
            avatar.alt = user.name || "Profile";
        }
        if (emailEl) emailEl.textContent = user.email || "";
    }

    function showLoggedIn(user) {
        applyLoggedInUI(user);

        /* Show send button only on pages that have an edition */
        var sendBtn = document.getElementById("auth-send-btn");
        var edition = document.querySelector("[data-edition-id]");
        if (sendBtn && edition) sendBtn.style.display = "block";
    }

    function showLoggedOut() {
        var loginBtn = document.getElementById("auth-login-btn");
        var profile = document.getElementById("auth-profile");
        var sendBtn = document.getElementById("auth-send-btn");

        if (loginBtn) loginBtn.style.display = "inline-flex";
        if (profile) profile.style.display = "none";
        if (sendBtn) sendBtn.style.display = "none";
    }

    /* ---- Dropdown ---- */

    function bindDropdownToggle() {
        document.addEventListener("click", function (e) {
            var avatarBtn = document.getElementById("auth-avatar-btn");
            var dropdown = document.getElementById("auth-dropdown");
            if (!avatarBtn || !dropdown) return;

            if (avatarBtn.contains(e.target)) {
                dropdown.classList.toggle("open");
                e.stopPropagation();
            } else if (!dropdown.contains(e.target)) {
                dropdown.classList.remove("open");
            }
        });
    }

    /* ---- Logout ---- */

    function bindLogout() {
        document.addEventListener("click", function (e) {
            if (!e.target.closest("#auth-logout-btn")) return;
            fetch("/auth/logout", {
                method: "POST",
                credentials: "same-origin",
            }).then(function () {
                localStorage.removeItem(STORAGE_KEY);
                showLoggedOut();
                var dropdown = document.getElementById("auth-dropdown");
                if (dropdown) dropdown.classList.remove("open");
                showToast("Logged out", "success");
            });
        });
    }

    /* ---- Send to self ---- */

    function bindSendToSelf() {
        document.addEventListener("click", function (e) {
            var btn = e.target.closest("#auth-send-btn");
            if (!btn) return;

            var edition = document.querySelector("[data-edition-id]");
            var editionId = edition ? edition.getAttribute("data-edition-id") : "";
            if (!editionId) return;

            btn.disabled = true;
            btn.textContent = "Sending…";

            /* Close dropdown while sending */
            var dropdown = document.getElementById("auth-dropdown");
            if (dropdown) dropdown.classList.remove("open");

            fetch("/api/v1/share/send-to-self", {
                method: "POST",
                credentials: "same-origin",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ edition_id: editionId }),
            })
                .then(function (res) {
                    if (res.ok) return res.json();
                    return res.json()
                        .catch(function () {
                            throw new Error("Something went wrong. Please try again.");
                        })
                        .then(function (data) {
                            throw new Error(data.detail || "Something went wrong.");
                        });
                })
                .then(function (data) {
                    showToast(data.message || "Sent!", "success");
                })
                .catch(function (err) {
                    showToast(err.message, "error");
                })
                .finally(function () {
                    btn.disabled = false;
                    btn.textContent = "Send Newsletter";
                });
        });
    }

    /* ---- Toast ---- */

    function showToast(message, type) {
        var existing = document.getElementById("auth-toast");
        if (existing) existing.remove();

        var toast = document.createElement("div");
        toast.id = "auth-toast";
        toast.className = "auth-toast auth-toast--" + (type || "success");
        toast.setAttribute("role", "status");
        toast.setAttribute("aria-live", "polite");
        toast.textContent = message;
        document.body.appendChild(toast);

        /* Force reflow for transition */
        toast.offsetHeight; // eslint-disable-line no-unused-expressions
        toast.classList.add("auth-toast--visible");

        setTimeout(function () {
            toast.classList.remove("auth-toast--visible");
            setTimeout(function () { toast.remove(); }, 300);
        }, TOAST_DURATION);
    }
})();
