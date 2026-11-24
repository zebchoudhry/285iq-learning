"""
Public pages that search engines and new visitors see: landing page, one page per
subject, robots.txt, sitemap.xml and llms.txt.

Everything shown on these pages comes from the database (topic names, lesson titles, counts,
sample questions), so it stays true as the content grows. Nothing here needs a login.
"""
import json
import random
from datetime import date
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import Lesson, MultipleChoiceOption, Question, Subject, Topic

# slug -> public details. "db_name" is Subject.name in the database.
PUBLIC_SUBJECTS = {
    "gcse-maths": {
        "db_name": "mathematics", "title": "GCSE Maths", "short": "Maths", "icon": "∑",
        "blurb": "Number, algebra, ratio, geometry, probability, statistics and graphs, one short topic at a time.",
        "intro": "Maths is learned by doing. Every topic here ends in practice questions with the working explained, "
                 "and the ones you get wrong come back until you can do them. Revise a calculation skill, check it, "
                 "then move on.",
        "description": "Free GCSE Maths revision: practice questions on every topic with explained answers, flashcards "
                       "and mistake tracking, organised by the AQA topics.",
    },
    "gcse-biology": {
        "db_name": "biology", "title": "GCSE Biology", "short": "Biology", "icon": "🧬",
        "blurb": "Cells to ecology: practice questions and flashcards for every AQA Biology topic.",
        "intro": "Biology is mostly recall and explanation, which is exactly what practice testing trains. Work through "
                 "each topic with questions that explain the right answer, then use flashcards to keep the key terms "
                 "fresh until the exam.",
        "description": "Free GCSE Biology revision: practice questions on every topic, with explained answers, "
                       "flashcards and mistake tracking, organised by the AQA topics.",
    },
    "gcse-chemistry": {
        "db_name": "chemistry", "title": "GCSE Chemistry", "short": "Chemistry", "icon": "⚗️",
        "blurb": "Atomic structure to organic chemistry, including the calculations that lose the most marks.",
        "intro": "Chemistry mixes facts you must remember with calculations you must practise. Here you get both: "
                 "topic questions on the ideas, and fresh numbers every time for moles, concentration, yield and "
                 "balancing equations so you cannot just memorise the answer.",
        "description": "Free GCSE Chemistry revision: practice questions on every topic, unlimited calculation "
                       "practice with fresh numbers, flashcards and mistake tracking.",
    },
    "gcse-physics": {
        "db_name": "physics", "title": "GCSE Physics", "short": "Physics", "icon": "⚡",
        "blurb": "Energy, electricity, forces, waves, magnetism and atomic structure, with equation practice.",
        "intro": "Physics marks come from knowing which equation to use and using it correctly. The calculation questions "
                 "here ask for a different unknown each time, so you practise rearranging as well as substituting.",
        "description": "Free GCSE Physics revision: equation practice with fresh numbers every time, topic questions "
                       "with explained answers, flashcards and mistake tracking.",
    },
}

FAQS = [
    ("Is 285IQ free?", "Yes, you can start free. Free accounts get a daily allowance of practice questions, so you can try every subject before deciding anything else."),
    ("Which exam board is it for?", "The topics follow the AQA GCSE specifications for Maths, Biology, Chemistry and Physics. Much of the science is the same across boards, but the lessons and questions are organised by the AQA topics. 285IQ is independent and is not affiliated with AQA."),
    ("Does it replace my teacher or my textbook?", "No. 285IQ is for practising and remembering. Use it alongside your lessons, and ask your teacher when something does not make sense."),
    ("How is it different from video and notes sites?", "Videos and notes tell you what to learn. 285IQ makes you practise it, keeps track of what you get wrong, and brings it back at the right time so it sticks."),
    ("What happens when I get a question wrong?", "You see why the right answer is right, with a hint for your next try. The question is saved in your mistake bank and comes back later, so one slip does not turn into a gap."),
    ("Can my parent see how I am doing?", "Yes. Each student has a private progress link a parent can open, showing topic-by-topic progress and weekly practice. No separate parent login is needed."),
    ("What do I need to use it?", "Just a web browser on a phone, tablet or computer. There is nothing to install."),
]

PRIVATE_PREFIXES = (
    "/api/", "/admin/", "/parent/", "/billing/", "/settings/", "/onboarding/", "/quiz/", "/practice/",
    "/lessons/", "/flashcards/", "/mistakes/", "/revision/", "/subject/", "/subjects/", "/exam-readiness/",
    "/mock-tests/", "/boss/", "/games/", "/static/admin/",
)


def site_url() -> str:
    return getattr(settings, "SITE_URL", "https://285iq.com").rstrip("/")


def is_canonical_host(request) -> bool:
    """True on the real domain (with or without www). False on previews, vercel.app and localhost."""
    canonical = urlparse(site_url()).hostname or ""
    host = request.get_host().split(":")[0].lower()
    return host in (canonical, "www." + canonical)


def _base_context(request, path, title, description, jsonld, **extra):
    return {
        "site_url": site_url(),
        "path": path,
        "page_title": title,
        "page_description": description,
        # "</" is escaped so the JSON can never close its own script tag
        "jsonld": json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/"),
        "noindex": not is_canonical_host(request),
        "subjects_nav": [(slug, s["title"]) for slug, s in PUBLIC_SUBJECTS.items()],
        **extra,
    }


def landing_jsonld() -> dict:
    url = site_url()
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": f"{url}/#website", "url": f"{url}/", "name": "285IQ", "inLanguage": "en-GB"},
            {
                "@type": "WebApplication", "@id": f"{url}/#app", "name": "285IQ", "url": f"{url}/",
                "applicationCategory": "EducationalApplication", "operatingSystem": "Web",
                "description": "GCSE revision for Maths, Biology, Chemistry and Physics with practice questions, "
                               "flashcards, mistake tracking and a parent progress view.",
                "audience": {"@type": "PeopleAudience", "suggestedMinAge": 14, "suggestedMaxAge": 16},
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "GBP"},
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in FAQS
                ],
            },
        ],
    }


def subject_jsonld(slug, subject) -> dict:
    url = site_url()
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage", "@id": f"{url}/{slug}/#page", "url": f"{url}/{slug}/",
                "name": f"{subject['title']} revision", "description": subject["description"], "inLanguage": "en-GB",
                "isPartOf": {"@id": f"{url}/#website"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "285IQ", "item": f"{url}/"},
                    {"@type": "ListItem", "position": 2, "name": subject["title"], "item": f"{url}/{slug}/"},
                ],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Content from the database
# ---------------------------------------------------------------------------
def content_counts() -> dict:
    """Question, lesson and topic totals for the landing page. Cached for an hour."""
    def build():
        return {
            "questions": Question.objects.filter(
                is_active=True, lesson__is_active=True, lesson__topic__is_active=True).count(),
            "lessons": Lesson.objects.filter(is_active=True, topic__is_active=True).count(),
            "flashcards": _flashcard_count(),
        }
    return cache.get_or_set("public_content_counts", build, 3600)


def _flashcard_count() -> int:
    from .models import Flashcard
    return Flashcard.objects.filter(is_active=True).count()


def round_down(n: int, step: int) -> int:
    """'9,400' becomes '9,000+' so the page stays true between content updates."""
    return (n // step) * step


def subject_stats(db_name: str) -> dict:
    topics = (
        Topic.objects.filter(subject__name=db_name, is_active=True)
        .annotate(lesson_count=Count("lessons", filter=Q(lessons__is_active=True)))
        .order_by("order", "id")
    )
    topic_list = []
    for t in topics:
        titles = list(
            Lesson.objects.filter(topic=t, is_active=True).order_by("order", "id").values_list("title", flat=True)
        )
        topic_list.append({"name": t.name, "lessons": titles, "count": len(titles)})
    questions = Question.objects.filter(
        is_active=True, lesson__is_active=True, lesson__topic__is_active=True,
        lesson__topic__subject__name=db_name,
    ).count()
    return {
        "topics": topic_list,
        "topic_count": len(topic_list),
        "lesson_count": sum(t["count"] for t in topic_list),
        "question_count": questions,
    }


def sample_questions(db_name=None, count=3, seed=None):
    """
    Multiple-choice questions for the 'try one' boxes: active, with an explanation and exactly
    one correct option. The choice is stable for a day, so what a crawler sees matches what a
    visitor sees.
    """
    seed = seed or f"{date.today().isoformat()}-{db_name or 'all'}"

    def build():
        qs = Question.objects.filter(
            is_active=True, question_type="multiple_choice", lesson__is_active=True,
            lesson__topic__is_active=True, is_shared=True,
        ).exclude(explanation="")
        if db_name:
            qs = qs.filter(lesson__topic__subject__name=db_name)
        ids = list(qs.values_list("id", flat=True))
        random.Random(seed).shuffle(ids)
        picked = []
        for qid in ids[: count * 8]:
            q = Question.objects.select_related("lesson__topic").get(id=qid)
            options = list(MultipleChoiceOption.objects.filter(question=q).order_by("order"))
            if len(options) != 4 or sum(o.is_correct for o in options) != 1:
                continue
            if len(q.question_text) > 220 or any(len(o.option_text) > 110 for o in options):
                continue
            picked.append({
                "text": q.question_text,
                "options": [o.option_text for o in options],
                "correct": next(i for i, o in enumerate(options) if o.is_correct),
                "explanation": q.explanation,
                "topic": q.lesson.topic.name,
            })
            if len(picked) == count:
                break
        return picked

    return cache.get_or_set(f"public_samples:{seed}:{count}", build, 3600)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def home(request):
    """Landing page for visitors; the dashboard for signed-in students."""
    if request.user.is_authenticated:
        from .views import frontend_view
        return frontend_view(request)
    counts = content_counts()
    subjects = []
    for slug, s in PUBLIC_SUBJECTS.items():
        stats = subject_stats(s["db_name"])
        subjects.append({**s, "slug": slug, **stats})
    return render(request, "site/landing.html", _base_context(
        request, "/",
        "GCSE Revision App: Maths, Biology, Chemistry, Physics | 285IQ",
        "Free GCSE revision for Maths, Biology, Chemistry and Physics. Practice questions with explained "
        "answers, flashcards, and mistakes that come back until fixed.",
        landing_jsonld(),
        counts={
            "questions": f"{round_down(counts['questions'], 500):,}",
            "lessons": counts["lessons"],
            "flashcards": f"{round_down(counts['flashcards'], 100):,}",
        },
        subjects=subjects,
        samples=sample_questions(None, 1),
        faqs=[{"q": q, "a": a} for q, a in FAQS],
    ))


def subject_page(request, slug):
    subject = PUBLIC_SUBJECTS.get(slug)
    if not subject:
        from django.http import Http404
        raise Http404
    stats = subject_stats(subject["db_name"])
    return render(request, "site/subject.html", _base_context(
        request, f"/{slug}/",
        f"{subject['title']} Revision: Questions, Flashcards, Topics | 285IQ",
        subject["description"],
        subject_jsonld(slug, subject),
        slug=slug, subject=subject, stats=stats,
        samples=sample_questions(subject["db_name"], 3),
        others=[(s, d["title"]) for s, d in PUBLIC_SUBJECTS.items() if s != slug],
    ))


# ---------------------------------------------------------------------------
# robots.txt, sitemap.xml, llms.txt
# ---------------------------------------------------------------------------
def robots_txt(request):
    if not is_canonical_host(request):
        body = "User-agent: *\nDisallow: /\n"
    else:
        lines = ["User-agent: *", "Allow: /"]
        lines += [f"Disallow: {p}" for p in PRIVATE_PREFIXES if p != "/static/admin/"]
        lines += ["", f"Sitemap: {site_url()}/sitemap.xml", ""]
        body = "\n".join(lines)
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    paths = ["/"] + [f"/{slug}/" for slug in PUBLIC_SUBJECTS] + ["/register/"]
    urls = "\n".join(f"  <url><loc>{site_url()}{p}</loc></url>" for p in paths)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n"
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


def llms_txt(request):
    counts = content_counts()
    lines = [
        "# 285IQ",
        "",
        "> GCSE revision for Maths, Biology, Chemistry and Physics, organised by the AQA topics. Practice questions "
        "with explained answers, spaced-repetition flashcards, mistake tracking and a parent progress view. "
        "Free to start.",
        "",
        "285IQ is independent and is not affiliated with or endorsed by AQA.",
        "",
        "## Pages",
        f"- [Home]({site_url()}/): what 285IQ does and how it works",
    ]
    lines += [f"- [{s['title']}]({site_url()}/{slug}/): {s['blurb']}" for slug, s in PUBLIC_SUBJECTS.items()]
    lines += [f"- [Sign up]({site_url()}/register/): create a free account", "",
              f"Content: over {round_down(counts['questions'], 500):,} practice questions across "
              f"{counts['lessons']} lessons.", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
