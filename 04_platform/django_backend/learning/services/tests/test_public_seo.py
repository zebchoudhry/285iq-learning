import json
import re
import struct
import uuid
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, override_settings

from learning import seo_views
from learning.models import Lesson, MultipleChoiceOption, Question, Subject, Topic

SITE = settings.SITE_URL.rstrip("/")


class Page(HTMLParser):
    """Collects the head tags, links, headings and scripts of a page."""

    def __init__(self):
        super().__init__()
        self.title = self.description = self.canonical = self.robots = None
        self.hrefs, self.h1, self.scripts, self.ld = [], [], [], []
        self._tag = None
        self._buf = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._tag, self._buf = tag, ""
        if tag == "meta" and a.get("name") == "description":
            self.description = a.get("content")
        if tag == "meta" and a.get("name") == "robots":
            self.robots = a.get("content")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if tag == "script":
            self.scripts.append(a)
            self._ld = a.get("type") == "application/ld+json"

    def handle_data(self, data):
        self._buf += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.title = self._buf
        if tag == "h1":
            self.h1.append(self._buf.strip())
        if tag == "script" and getattr(self, "_ld", False):
            self.ld.append(self._buf)
            self._ld = False


def parse(response) -> Page:
    p = Page()
    p.feed(response.content.decode("utf-8"))
    return p


@pytest.fixture(autouse=True)
def fresh_cache():
    cache.clear()
    yield
    cache.clear()


def make_mcq(lesson, text, options, correct=0, explanation="Because of the reason.", **kw):
    q = Question.objects.create(lesson=lesson, question_text=text, correct_answer=options[correct],
                                question_type="multiple_choice", explanation=explanation, **kw)
    for i, o in enumerate(options):
        MultipleChoiceOption.objects.create(question=q, option_text=o, is_correct=(i == correct), order=i)
    return q


@pytest.fixture
def content(db):
    out = {}
    for slug, s in seo_views.PUBLIC_SUBJECTS.items():
        subject = Subject.objects.create(name=s["db_name"], display_name=s["title"])
        topic = Topic.objects.create(subject=subject, name=f"{s['short']} Topic A", order=1)
        Topic.objects.create(subject=subject, name=f"{s['short']} Old Duplicate", order=2, is_active=False)
        lesson = Lesson.objects.create(topic=topic, title="1.1 - First Lesson", content="x", order=1)
        for i in range(4):
            make_mcq(lesson, f"{s['short']} question {i}?", ["Right", "Wrong A", "Wrong B", "Wrong C"], correct=i % 4)
        make_mcq(lesson, f"{s['short']} hidden question?", ["A", "B", "C", "D"], is_active=False)
        out[slug] = {"subject": subject, "topic": topic, "lesson": lesson}
    return out


@pytest.fixture
def client():
    # tests act as a visitor on the real domain; the test client's default host is not canonical
    return Client(HTTP_HOST=urlparse(SITE).netloc)


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------
def test_landing_is_public_and_well_formed(client, content):
    r = client.get("/")
    assert r.status_code == 200
    p = parse(r)
    assert len(p.h1) == 1 and len(p.h1[0]) > 20
    assert 30 <= len(p.title) <= 65, p.title
    assert 100 <= len(p.description) <= 165, len(p.description)
    assert p.canonical == f"{SITE}/"
    assert "noindex" not in p.robots
    html = r.content.decode()
    assert "{{" not in html and "{%" not in html and "None" not in html.replace("None of", "")


def test_landing_has_no_external_scripts_or_fonts(client, content):
    html = client.get("/").content.decode()
    assert not re.search(r"<script[^>]+src=", html)
    assert "fonts.googleapis" not in html
    assert len(html) < 60000, "the landing page should stay light"


def test_landing_structured_data_is_valid_and_honest(client, content):
    p = parse(client.get("/"))
    data = json.loads(p.ld[0])
    types = {n["@type"] for n in data["@graph"]}
    assert types == {"WebSite", "WebApplication", "FAQPage"}
    app = next(n for n in data["@graph"] if n["@type"] == "WebApplication")
    assert app["offers"]["price"] == "0" and app["offers"]["priceCurrency"] == "GBP"
    assert "aggregateRating" not in json.dumps(data) and "review" not in json.dumps(data).lower()
    faq = next(n for n in data["@graph"] if n["@type"] == "FAQPage")
    assert len(faq["mainEntity"]) == len(seo_views.FAQS)


def test_faq_on_page_matches_structured_data(client, content):
    html = client.get("/").content.decode()
    for q, a in seo_views.FAQS:
        assert q in html and a.split(".")[0][:40] in html


def test_json_ld_cannot_close_its_script_tag(client, rf=None):
    ctx = seo_views._base_context(
        type("R", (), {"get_host": lambda self: "285iq.com"})(), "/", "t", "d", {"x": "</script><b>"})
    assert "</script>" not in ctx["jsonld"] and json.loads(ctx["jsonld"].replace("<\\/", "</"))["x"] == "</script><b>"


def test_counts_come_from_active_content_only(client, content):
    r = client.get("/")
    assert r.context["counts"]["lessons"] == 4
    assert r.context["counts"]["questions"] == "0"  # 16 real questions rounds down; hidden ones never count


def test_landing_sample_question_is_a_valid_active_question(client, content):
    r = client.get("/")
    sample = r.context["samples"][0]
    assert len(sample["options"]) == 4 and 0 <= sample["correct"] < 4
    assert "hidden question" not in r.content.decode()


def test_every_internal_link_on_public_pages_resolves(client, content):
    seen = set()
    for path in ["/"] + [f"/{s}/" for s in seo_views.PUBLIC_SUBJECTS]:
        for href in parse(client.get(path)).hrefs:
            if href.startswith("/") and not href.startswith("//") and href not in seen:
                seen.add(href)
                assert client.get(href.split("#")[0]).status_code in (200, 301, 302), href
    assert {"/register/", "/login/", "/gcse-maths/"} <= seen


def test_signed_in_students_still_get_the_dashboard(db):
    user = get_user_model().objects.create_user(username="kid", password="x-test-pass")
    c = Client()
    c.force_login(user)
    r = c.get("/")
    assert r.status_code == 302 and r["Location"] == "/onboarding/exam-dates/"  # not the landing page


# ---------------------------------------------------------------------------
# Subject pages
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("slug", list(seo_views.PUBLIC_SUBJECTS))
def test_subject_pages(client, content, slug):
    s = seo_views.PUBLIC_SUBJECTS[slug]
    r = client.get(f"/{slug}/")
    assert r.status_code == 200
    p = parse(r)
    assert p.canonical == f"{SITE}/{slug}/" and len(p.h1) == 1 and s["title"] in p.h1[0]
    assert 30 <= len(p.title) <= 70 and 100 <= len(p.description) <= 165
    html = r.content.decode()
    assert f"{s['short']} Topic A" in html and "Old Duplicate" not in html
    assert "1.1 - First Lesson" in html and "hidden question" not in html
    graph = json.loads(p.ld[0])["@graph"]
    crumbs = next(n for n in graph if n["@type"] == "BreadcrumbList")
    assert [i["name"] for i in crumbs["itemListElement"]] == ["285IQ", s["title"]]
    assert r.context["stats"]["topic_count"] == 1 and r.context["stats"]["question_count"] == 4


def test_unknown_subject_is_404(client, content):
    assert client.get("/gcse-art/").status_code == 404


def test_sample_questions_are_stable_within_a_day(content):
    a = seo_views.sample_questions("biology", 3)
    cache.clear()
    assert a == seo_views.sample_questions("biology", 3)


def test_sample_questions_skip_awkward_ones(db):
    subject = Subject.objects.create(name="biology", display_name="Biology")
    lesson = Lesson.objects.create(topic=Topic.objects.create(subject=subject, name="T", order=1), title="1.1 - L", content="x")
    make_mcq(lesson, "x" * 300, ["A", "B", "C", "D"])                      # too long
    make_mcq(lesson, "No explanation?", ["A", "B", "C", "D"], explanation="")
    q = make_mcq(lesson, "Fine question here?", ["A", "B", "C", "D"])
    assert [s["text"] for s in seo_views.sample_questions("biology", 3)] == ["Fine question here?"]


# ---------------------------------------------------------------------------
# robots.txt, sitemap, llms.txt
# ---------------------------------------------------------------------------
def test_robots_txt_blocks_private_areas_and_points_to_the_sitemap(client, db):
    text = client.get("/robots.txt").content.decode()
    for prefix in ("/api/", "/admin/", "/parent/", "/billing/", "/settings/", "/lessons/", "/boss/", "/games/"):
        assert f"Disallow: {prefix}" in text
    assert "Allow: /" in text and f"Sitemap: {SITE}/sitemap.xml" in text
    assert "Disallow: /\n" not in text


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["*"])
def test_robots_txt_blocks_everything_off_the_real_domain(client, db):
    text = client.get("/robots.txt", HTTP_HOST="my-preview-abc.vercel.app").content.decode()
    assert "Disallow: /" in text and "Sitemap" not in text


@override_settings(ALLOWED_HOSTS=["*"])
def test_previews_are_not_indexed(client, content):
    r = client.get("/", HTTP_HOST="my-preview-abc.vercel.app")
    assert parse(r).robots == "noindex, nofollow"
    assert parse(client.get("/", HTTP_HOST="www.285iq.com")).robots != "noindex, nofollow"


def test_sitemap_is_valid_xml_with_canonical_urls(client, db):
    r = client.get("/sitemap.xml")
    assert r["Content-Type"].startswith("application/xml")
    root = ET.fromstring(r.content)
    locs = [e.text for e in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert locs == [f"{SITE}/", *[f"{SITE}/{s}/" for s in seo_views.PUBLIC_SUBJECTS], f"{SITE}/register/"]
    assert all(l.startswith("https://") for l in locs)


def test_every_sitemap_url_is_publicly_reachable(client, content):
    root = ET.fromstring(client.get("/sitemap.xml").content)
    for e in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        assert client.get(e.text.replace(SITE, "")).status_code == 200, e.text


def test_llms_txt(client, content):
    text = client.get("/llms.txt").content.decode()
    assert text.startswith("# 285IQ") and "not affiliated with or endorsed by AQA" in text
    assert all(f"/{slug}/" in text for slug in seo_views.PUBLIC_SUBJECTS)


# ---------------------------------------------------------------------------
# Private pages are never indexed
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", [
    f"/parent/{uuid.uuid4()}/", "/api/gamification/me/", "/login/", "/lessons/", "/quiz/", "/boss/1/",
    "/games/", "/billing/success/", "/settings/", "/flashcards/",
])
def test_private_pages_send_noindex(client, db, path):
    assert client.get(path)["X-Robots-Tag"] == "noindex, nofollow"


@pytest.mark.parametrize("path", ["/", "/gcse-maths/", "/register/", "/robots.txt", "/sitemap.xml"])
def test_public_pages_do_not_send_noindex(client, content, path):
    assert "X-Robots-Tag" not in client.get(path)


# ---------------------------------------------------------------------------
# Social share image
# ---------------------------------------------------------------------------
def test_share_image_exists_and_is_1200_by_630():
    path = Path(settings.BASE_DIR) / "static" / "og-image.png"
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", header[16:24]) == (1200, 630)
    assert path.stat().st_size < 150_000


def test_no_template_folder_is_named_public():
    """Vercel treats a folder called "public" as static output and leaves it out of the Python
    function, so templates in it deploy fine but raise TemplateDoesNotExist in production
    (this took the homepage down on 2026-11-24)."""
    templates = Path(settings.BASE_DIR) / "templates"
    assert not [p for p in templates.rglob("*") if p.is_dir() and p.name == "public"]


def test_landing_lists_every_real_game(client, content):
    from learning.services.games import GAMES

    html = client.get("/").content.decode()
    assert 'id="games"' in html and "Revision that feels like a game" in html
    for g in GAMES:
        assert g.title in html and g.blurb in html
    assert len(client.get("/").context["games"]) == len(GAMES)


def test_samples_never_repeat_the_same_wording(db):
    """Production has the same question copied into several topics; a page must not show it twice."""
    subject = Subject.objects.create(name="chemistry", display_name="GCSE Chemistry")
    for n in range(3):
        topic = Topic.objects.create(subject=subject, name=f"Topic {n}", order=n)
        lesson = Lesson.objects.create(topic=topic, title=f"{n}.1 - L", content="x")
        make_mcq(lesson, "What products form when an acid reacts with a base?", ["Salt and water", "A", "B", "C"])
    texts = [s["text"] for s in seo_views.sample_questions("chemistry", 3)]
    assert texts == ["What products form when an acid reacts with a base?"]


def test_landing_speaks_to_parents(client, content):
    html = client.get("/").content.decode()
    assert 'id="parents"' in html and 'href="/#parents"' in html and 'href="#parents"' in html
    assert "Parent actions this week" in html and "Example data" in html


def test_landing_explains_the_gym_analogy_to_parents(client, content):
    html = client.get("/").content.decode()
    parents = html[html.index('id="parents"'):html.index('id="how"')]
    assert "personal trainer" in parents and "Progressive overload" in parents
    for rung in ("Basics", "Guided practice", "Drills", "Mixed practice", "Exam-level"):
        assert rung in parents
