"""Public homepage — renders the Cooperative Banking design wired to CMS data.

The Claude-Design template binds to many variables (style strings + data lists).
This view supplies all of them: CMS-backed lists where content exists, and
faithful static design data as a fallback so the page always looks complete.
"""
from django.conf import settings
from django.shortcuts import render
from django.utils.safestring import mark_safe

from apps.banners.models import Banner
from apps.branches.models import Branch
from apps.notices.models import Notice
from apps.schemes.models import Scheme, SchemeType
from apps.sitesettings.models import SiteSetting
from apps.testimonials.models import Testimonial

# ── palette (matches the design tokens) ─────────────────────────────────
ACC, ACC2, NAVY, INK = "#0EA5E9", "#22D3EE", "#06243f", "#0A2540"

# ── reusable inline SVGs ────────────────────────────────────────────────
def _svg(path):
    return mark_safe(
        f'<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')

ICONS = {
    SchemeType.FD: _svg('<rect x="3" y="8" width="18" height="12" rx="2"/><path d="M7 8V6a5 5 0 0110 0v2"/>'),
    SchemeType.RD: _svg('<path d="M3 3v18h18"/><path d="m7 14 4-4 3 3 5-6"/>'),
    SchemeType.SAVINGS: _svg('<path d="M19 5c-1.5 0-2.8 1.4-3 2-3.5-1.5-11-.3-11 5 0 1.8 1 3.3 2.5 4.3V20h3v-2h3v2h3v-2.5c1-.7 1.7-1.6 2-2.5h2v-4h-2c-.3-1.3-1.5-2.7-2.5-3z"/>'),
    SchemeType.LOAN: _svg('<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 015 0c0 1.5-2.5 2-2.5 3.5"/><path d="M12 17h.01"/>'),
}
FEATURE_SVGS = [
    _svg('<path d="M12 2 4 5v6c0 5 3.5 8 8 11 4.5-3 8-6 8-11V5z"/>'),
    _svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    _svg('<path d="M20 6 9 17l-5-5"/>'),
    _svg('<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/>'),
    _svg('<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/>'),
    _svg('<path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>'),
]
STARS = mark_safe(''.join(
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="#f59e0b"><path d="M12 2l3 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.9 21l1.2-6.8-5-4.9 6.9-1z"/></svg>'
    for _ in range(5)))


def _services(schemes):
    glows = ["rgba(14,165,233,.35)", "rgba(34,211,238,.3)", "rgba(3,105,161,.3)"]
    out = []
    for i, s in enumerate(schemes):
        out.append({
            "delay": i * 70, "glow": glows[i % len(glows)],
            "iconBg": "#e8f4fb", "iconInk": "#0369A1",
            "icon": ICONS.get(s.scheme_type, FEATURE_SVGS[0]),
            "name": s.scheme_name, "rate": f"{s.interest_rate}% p.a.",
            "desc": s.description or s.tenure or "Flexible terms with attractive returns.",
        })
    return out


STATIC_SERVICES = [
    {"delay": 0, "glow": "rgba(14,165,233,.35)", "iconBg": "#e8f4fb", "iconInk": "#0369A1",
     "icon": ICONS[SchemeType.FD], "name": "Fixed Deposits", "rate": "up to 8.25%",
     "desc": "Lock in high, guaranteed returns with flexible tenures from 6 months to 5 years."},
    {"delay": 70, "glow": "rgba(34,211,238,.3)", "iconBg": "#e8f4fb", "iconInk": "#0369A1",
     "icon": ICONS[SchemeType.RD], "name": "Recurring Deposits", "rate": "up to 7.75%",
     "desc": "Build savings month by month with disciplined deposits and compounding growth."},
    {"delay": 140, "glow": "rgba(3,105,161,.3)", "iconBg": "#e8f4fb", "iconInk": "#0369A1",
     "icon": ICONS[SchemeType.SAVINGS], "name": "Savings Accounts", "rate": "4% p.a.",
     "desc": "Everyday banking with zero hidden charges and instant access to your money."},
    {"delay": 0, "glow": "rgba(14,165,233,.35)", "iconBg": "#e8f4fb", "iconInk": "#0369A1",
     "icon": ICONS[SchemeType.LOAN], "name": "Personal Loans", "rate": "from 11%",
     "desc": "Quick, fair-rate loans for life's milestones with minimal paperwork."},
    {"delay": 70, "glow": "rgba(34,211,238,.3)", "iconBg": "#e8f4fb", "iconInk": "#0369A1",
     "icon": ICONS[SchemeType.LOAN], "name": "Gold Loans", "rate": "from 9.5%",
     "desc": "Unlock the value of your gold with same-day disbursal and safe custody."},
    {"delay": 140, "glow": "rgba(3,105,161,.3)", "iconBg": "#e8f4fb", "iconInk": "#0369A1",
     "icon": ICONS[SchemeType.LOAN], "name": "Business Loans", "rate": "from 12%",
     "desc": "Working-capital and term loans to help local enterprises grow."},
]

FEATURES = [
    {"delay": 0, "icon": FEATURE_SVGS[0], "title": "Member-owned & secure",
     "desc": "A registered cooperative governed by its members — your deposits, your society."},
    {"delay": 60, "icon": FEATURE_SVGS[1], "title": "Decades of trust",
     "desc": "Serving families and small businesses with transparent, fair banking since 1991."},
    {"delay": 120, "icon": FEATURE_SVGS[2], "title": "Competitive returns",
     "desc": "Some of the best deposit rates in the region, with no hidden charges."},
    {"delay": 0, "icon": FEATURE_SVGS[3], "title": "Quick approvals",
     "desc": "Loans assessed and disbursed fast, with minimal paperwork and friendly staff."},
    {"delay": 60, "icon": FEATURE_SVGS[4], "title": "People over profit",
     "desc": "Surpluses return to members and the community, not distant shareholders."},
    {"delay": 120, "icon": FEATURE_SVGS[5], "title": "Digital + branch",
     "desc": "Manage your account online or visit any of our neighbourhood branches."},
]

FAQS = [
    {"q": "How do I become a member?", "a": "Visit any branch with your ID and address proof, fill a short form, and purchase a nominal share to become a member-owner of the society."},
    {"q": "Are my deposits safe?", "a": "Yes. We are a registered cooperative society operating under cooperative banking regulations, with prudent reserves and transparent member governance."},
    {"q": "What documents do I need for a loan?", "a": "Typically ID proof, address proof, income proof and any collateral documents. Our staff will guide you based on the loan scheme."},
    {"q": "How is interest calculated on FDs?", "a": "Interest is calculated at the published annual rate for your chosen tenure and can be paid out periodically or compounded — your choice at account opening."},
    {"q": "Can I access my account online?", "a": "Yes, members get access to an online portal to view balances, statements and pay instalments, in addition to branch service."},
    {"q": "Where are your branches located?", "a": "We operate neighbourhood branches across the region — see the Branch Locator section above for addresses, phones and hours."},
]


def _rate_cards(schemes):
    """Build up to 3 pricing cards from deposit schemes; middle one featured."""
    deposits = [s for s in schemes if s.scheme_type in (SchemeType.FD, SchemeType.RD, SchemeType.SAVINGS)][:3]
    cards = []
    for i, s in enumerate(deposits):
        featured = (i == 1)
        cards.append(_card(featured, i * 80, s.tenure or s.get_scheme_type_display(),
                            str(s.interest_rate), [b for b in (s.benefit_list or
                            ["Flexible tenure", "Nomination facility", "Easy renewal"])][:3]))
    return cards


def _card(featured, delay, tenure, rate, perks):
    if featured:
        return {"featured": True, "delay": delay,
                "cardStyle": "background:linear-gradient(160deg,#0369A1,#06243f);color:#fff;border-radius:24px;padding:36px;position:relative;box-shadow:0 40px 80px -30px rgba(3,105,161,.6)",
                "tenureInk": "#bcdcef", "tenure": tenure, "rateInk": "#fff", "rate": rate,
                "subInk": "#bcdcef", "perks": perks, "perkInk": "#dbeeff", "tick": ACC2,
                "btnStyle": "display:block;text-align:center;background:#fff;color:#0369A1;font-weight:800;padding:14px;border-radius:12px"}
    return {"featured": False, "delay": delay,
            "cardStyle": "background:#fff;border:1px solid #e6eef5;border-radius:24px;padding:36px;position:relative",
            "tenureInk": "#0369A1", "tenure": tenure, "rateInk": "#0A2540", "rate": rate,
            "subInk": "#5b7185", "perks": perks, "perkInk": "#56697b", "tick": ACC,
            "btnStyle": "display:block;text-align:center;background:#eef6fc;color:#0369A1;font-weight:800;padding:14px;border-radius:12px"}


STATIC_RATE_CARDS = [
    _card(False, 0, "1 Year FD", "7.50", ["Quarterly payout option", "Auto-renewal", "Loan against deposit"]),
    _card(True, 80, "3 Year FD", "8.25", ["Highest return", "Compounding interest", "Nomination facility"]),
    _card(False, 160, "Recurring Deposit", "7.75", ["Monthly savings", "Flexible amount", "Goal-based plans"]),
]

STATIC_RATE_ROWS = [
    {"bg": "#fff", "tenure": "6 – 12 months", "fd": "7.00%", "rd": "6.75%", "sr": "7.50%"},
    {"bg": "#f6fafd", "tenure": "1 – 2 years", "fd": "7.50%", "rd": "7.25%", "sr": "8.00%"},
    {"bg": "#fff", "tenure": "2 – 3 years", "fd": "8.25%", "rd": "7.75%", "sr": "8.75%"},
    {"bg": "#f6fafd", "tenure": "3 – 5 years", "fd": "8.00%", "rd": "7.50%", "sr": "8.50%"},
    {"bg": "#fff", "tenure": "5+ years", "fd": "7.75%", "rd": "7.25%", "sr": "8.25%"},
]

APP_FEATURES = ["Check balances & statements", "Pay loan instalments online",
                "Open FDs & RDs in minutes", "Get instant transaction alerts",
                "Locate branches & support"]

# No fabricated testimonials — the section stays hidden until real ones are
# added via the CMS admin (Testimonials).
STATIC_TESTIMONIALS = []

# Placeholder notices — replaced by real ones added in the CMS admin (Notices).
STATIC_NEWS = [
    {"delay": 0, "badge": "Notice", "badgeBg": "#e8f4fb", "badgeInk": "#0369A1", "date": "Recent",
     "title": "Welcome to Shree Shyam Jan Kalyan", "desc": "Our member-owned co-operative thrift & credit society is now serving members in Kirari Suleman Nagar, Delhi."},
    {"delay": 70, "badge": "Notice", "badgeBg": "#eafaf1", "badgeInk": "#059669", "date": "Recent",
     "title": "Deposit & loan services available", "desc": "Visit the head office for savings, fixed & recurring deposits, and loan schemes."},
    {"delay": 140, "badge": "Notice", "badgeBg": "#fef3e8", "badgeInk": "#d97706", "date": "Recent",
     "title": "Passbook update window", "desc": "Passbooks are updated between the 16th and 30th of each month. Please carry your passbook."},
]

STATIC_BRANCHES = [
    {"head": True, "name": "Head Office",
     "address": "372/10, Beer Bazar, Gaurav Nagar, Kirari Suleman Nagar, Delhi-110086",
     "phone": "9313140202", "hours": "Mon–Sat 10AM–2PM & 3–7PM · Closed Tuesday"},
]


def home(request):
    site = SiteSetting.load()
    schemes = list(Scheme.objects.filter(is_active=True))
    notices = list(Notice.objects.all()[:3])
    testis = list(Testimonial.objects.filter(is_active=True)[:6])
    branches = list(Branch.objects.filter(is_active=True)[:6])
    banners = list(Banner.objects.filter(is_active=True)[:5])

    # Hero layers ← banners (fall back to a gradient image).
    from django.templatetags.static import static as static_url
    if banners:
        hero_layers = [{"op": 1 if i == 0 else 0, "src": b.image.url if b.image else static_url("website/hero-default.jpg"),
                        "kicker": "SSJD Cooperative", "title": b.title} for i, b in enumerate(banners)]
    else:
        hero_layers = [{"op": 1, "src": static_url("website/hero-default.jpg"),
                        "kicker": "SSJD Cooperative", "title": "Banking that belongs to you"}]
    hero_dots = [{"w": "26px" if i == 0 else "8px", "bg": "#fff" if i == 0 else "rgba(255,255,255,.4)"}
                 for i in range(len(hero_layers))]

    services = _services(schemes) if schemes else STATIC_SERVICES
    rate_cards = _rate_cards(schemes) or STATIC_RATE_CARDS
    news = [{"delay": i * 70, "badge": "Important" if n.is_important else "Notice",
             "badgeBg": "#fdeaea" if n.is_important else "#e8f4fb",
             "badgeInk": "#dc2626" if n.is_important else "#0369A1",
             "date": n.publish_date.strftime("%d %b %Y"), "title": n.title,
             "desc": (n.description or "")[:160]} for i, n in enumerate(notices)] or STATIC_NEWS
    testimonials = [{"id": str(t.id), "stars": STARS, "quote": t.review,
                     "name": t.customer_name, "role": t.designation or "Member"} for t in testis] or STATIC_TESTIMONIALS
    branch_list = [{"head": i == 0, "name": b.branch_name, "address": f"{b.address}, {b.city}",
                    "phone": b.phone or site.contact_phone, "hours": "Mon–Sat · 9:30 AM – 6:00 PM"}
                   for i, b in enumerate(branches)] or STATIC_BRANCHES
    # Honest, verifiable facts only — no fabricated member/deposit figures.
    counters = [{"value": "2025", "label": "Registered"},
                {"value": "Delhi", "label": "Head office"},
                {"value": "6% p.a.", "label": "Share money interest"},
                {"value": "₹10", "label": "Flat monthly late fee"}]
    testi_dots = list(range(len(testimonials)))

    portal = settings.PORTAL_URL.rstrip("/")
    ctx = {
        "site": site,
        "portal_url": portal,
        "member_login_url": f"{portal}/login?as=member",
        "admin_login_url": f"{portal}/login?as=admin",
        # ── style strings (resolved design defaults) ──
        "showTopBar": True, "mobileOpen": False,
        "navStyle": "position:sticky;top:0;z-index:50;background:#fff;box-shadow:0 1px 0 rgba(10,37,64,.08)",
        "navInk": INK, "navSub": "#5b7088",
        "linkStyle": "padding:9px 13px;border-radius:10px;font-weight:600;font-size:14.5px;color:#0A2540",
        "dropStyle": "position:absolute;top:100%;left:0;margin-top:8px;background:#fff;border:1px solid #e6eef5;border-radius:14px;box-shadow:0 24px 50px -20px rgba(6,36,63,.35);padding:8px;min-width:230px;display:none",
        "burgerBg": "transparent",
        "heroTagline": mark_safe("Smart savings, fair loans, and a society that puts <strong>members first.</strong>"),
        "footerStyle": "background:#06243f", "footInk": "#fff", "footMute": "#a9c6dc",
        "footChip": "rgba(255,255,255,.08)", "footBorder": "rgba(255,255,255,.12)",
        "testiShift": "translateX(0)", "branchQuery": "", "noBranches": False,
        "contactForm": True, "contactSent": False, "newsForm": True, "newsSent": False,
        # ── data lists ──
        "heroLayers": hero_layers, "heroDots": hero_dots, "counterCards": counters,
        "services": services, "features": FEATURES, "rateCards": rate_cards,
        "rateRows": STATIC_RATE_ROWS, "appFeatures": APP_FEATURES,
        "testimonials": testimonials, "testiDots": testi_dots,
        "news": news, "branchesFiltered": branch_list, "faqs": _faqs(),
    }
    return render(request, "website/index.html", ctx)


def _faqs():
    return [{"q": f["q"], "a": f["a"], "border": "#e6eef5", "shadow": "none",
             "iconBg": "#e8f4fb", "iconInk": "#0369A1", "iconRot": "rotate(45deg)",
             "maxH": "500px", "toggle": ""} for f in FAQS]
