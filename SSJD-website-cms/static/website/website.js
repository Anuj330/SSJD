/* Public homepage interactivity (no framework). */
(function () {
  "use strict";

  // 1) Generic hover effects from data-hover="css;css" (mirrors the design's style-hover).
  document.querySelectorAll("[data-hover]").forEach(function (el) {
    var hover = el.getAttribute("data-hover");
    var base = el.getAttribute("style") || "";
    el.addEventListener("mouseenter", function () { el.setAttribute("style", base + ";" + hover); });
    el.addEventListener("mouseleave", function () { el.setAttribute("style", base); });
  });

  // 1b) Mobile menu open/close.
  var overlay = document.querySelector("[data-mobile-overlay]");
  var burger = document.querySelector("[data-hamburger]");
  if (overlay && burger) {
    var openMenu = function () { overlay.style.display = "block"; };
    var closeMenu = function () { overlay.style.display = "none"; };
    burger.addEventListener("click", openMenu);
    overlay.addEventListener("click", closeMenu);                       // backdrop click
    var panel = overlay.querySelector("[data-mobile-panel]");
    if (panel) panel.addEventListener("click", function (e) { e.stopPropagation(); });
    var closeBtn = overlay.querySelector('[aria-label="Close"]');
    if (closeBtn) closeBtn.addEventListener("click", closeMenu);
    overlay.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", closeMenu); });
  }

  // 2) Smooth in-page anchor scrolling.
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener("click", function (e) {
      var id = a.getAttribute("href");
      if (id.length > 1) {
        var t = document.querySelector(id);
        if (t) { e.preventDefault(); t.scrollIntoView({ behavior: "smooth" }); }
      }
    });
  });

  // 3) Reveal-on-scroll for [data-reveal] (template defaults them visible; this animates).
  if ("IntersectionObserver" in window) {
    document.querySelectorAll("[data-reveal]").forEach(function (el) {
      el.style.opacity = "0";
      el.style.transform = "translateY(18px)";
      el.style.transition = "opacity .6s ease, transform .6s ease";
      el.style.transitionDelay = (el.getAttribute("data-reveal-delay") || 0) + "ms";
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.style.opacity = "1";
          en.target.style.transform = "none";
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll("[data-reveal]").forEach(function (el) { io.observe(el); });
  }

  // 4) AJAX-submit the contact + newsletter forms to the CMS API.
  function wireForm(form, url, build) {
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var payload = build(form);
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then(function (r) {
        if (r.ok) { form.reset(); alert("Thank you! We have received your message."); }
        else { alert("Sorry, something went wrong. Please try again."); }
      }).catch(function () { alert("Network error. Please try again."); });
    });
  }

  var contact = document.querySelector("#contact form");
  wireForm(contact, "/api/v1/contacts/", function (f) {
    var g = function (n) { var el = f.querySelector('[name="' + n + '"]'); return el ? el.value : ""; };
    return { name: g("name"), phone: g("phone"), email: g("email"),
             message: g("message") || "Website enquiry", inquiry_type: "general" };
  });
})();
