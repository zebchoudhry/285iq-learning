from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command

from learning.models import Lesson, MultipleChoiceOption, Question, Subject, Topic
from learning.services import question_bank as qb
from learning.services.answer_grading import answers_equivalent

BIOLOGY = Path(settings.BASE_DIR) / "question_bank" / "biology"


def write(tmp_path, text, name="sample.txt"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


GOOD = """\
// comment
topic: Cell Biology
lesson: 1.1 - Cell Structure
MC | 1 | Which part of a cell makes proteins? | Ribosomes | Mitochondria | Vacuole | Cytoplasm | Ribosomes join amino acids together to make proteins.
SA | 2 | What substance makes up a plant cell wall? | cellulose | Plant cell walls are made of cellulose fibres.
"""


# ---------------------------------------------------------------------------
# Parsing and validation
# ---------------------------------------------------------------------------
def test_parses_a_valid_file(tmp_path):
    result = qb.parse_file(write(tmp_path, GOOD))
    assert result.errors == []
    mc, sa = result.questions
    assert (mc.kind, mc.answer, mc.wrong) == ("MC", "Ribosomes", ["Mitochondria", "Vacuole", "Cytoplasm"])
    assert (sa.kind, sa.answer, mc.topic, mc.lesson) == ("SA", "cellulose", "Cell Biology", "1.1 - Cell Structure")


@pytest.mark.parametrize("line,expected", [
    ("MC | 1 | Which part makes proteins? | A | B | C | explanation is long enough here", "needs 8 fields"),
    ("SA | 1 | A question that is long enough? | cellulose", "needs 5 fields"),
    ("MC | x | A question that is long enough? | A | B | C | D | An explanation that is long enough.", "difficulty must be a number"),
    ("MC | 9 | A question that is long enough? | A | B | C | D | An explanation that is long enough.", "difficulty must be 1 to 5"),
    ("MC | 1 | A question that is long enough? | A | A | C | D | An explanation that is long enough.", "options must all be different"),
    ("MC | 1 | A question that is long enough? | A | a | C | D | An explanation that is long enough.", "options must all be different"),
    ("MC | 1 | A question that is long enough? | A | B | C | All of the above | An explanation that is long enough.", "not allowed"),
    ("MC | 1 | A question that is long enough? | A | B | C | D | too short", "explanation"),
    ("MC | 1 | short? | A | B | C | D | An explanation that is long enough.", "question must be"),
    ("SA | 1 | A question that is long enough? | one, two | An explanation that is long enough.", "single term"),
    ("SA | 1 | A question that is long enough? | red or blue | An explanation that is long enough.", "single term"),
    ("SA | 1 | A question that is long enough? | a b c d e f | An explanation that is long enough.", "at most"),
    ("XX | 1 | A question that is long enough? | A | An explanation that is long enough.", "must start with"),
])
def test_rejects_bad_lines(tmp_path, line, expected):
    result = qb.parse_file(write(tmp_path, f"topic: T\nlesson: 1.1 - L\n{line}\n"))
    assert any(expected in e for e in result.errors), result.errors


def test_question_before_lesson_is_an_error(tmp_path):
    result = qb.parse_file(write(tmp_path, "MC | 1 | A question that is long enough? | A | B | C | D | An explanation that is long enough.\n"))
    assert any("before a topic" in e for e in result.errors)


def test_a_decimal_short_answer_is_allowed(tmp_path):
    result = qb.parse_file(write(tmp_path, "topic: T\nlesson: 1.1 - L\nSA | 2 | A question that is long enough? | 2.5 | An explanation that is long enough.\n"))
    assert result.errors == []


def test_duplicates_across_files_are_caught(tmp_path):
    write(tmp_path, GOOD, "a.txt")
    write(tmp_path, GOOD, "b.txt")
    result = qb.parse_directory(tmp_path)
    assert sum("duplicate" in e for e in result.errors) == 2


def test_options_are_shuffled_the_same_way_every_time(tmp_path):
    q = qb.parse_file(write(tmp_path, GOOD)).questions[0]
    first = [o["text"] for o in q.options()]
    assert first == [o["text"] for o in q.options()]
    assert sorted(first) == sorted(["Ribosomes", "Mitochondria", "Vacuole", "Cytoplasm"])
    assert sum(o["correct"] for o in q.options()) == 1


def test_review_document_marks_the_correct_answer(tmp_path):
    md = qb.review_markdown(qb.parse_file(write(tmp_path, GOOD)).questions, "Check")
    assert "# Check" in md and "✓ Ribosomes" in md and "✓ cellulose" in md and "### 1.1 - Cell Structure" in md


# ---------------------------------------------------------------------------
# The real biology bank
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def bank():
    return qb.parse_directory(BIOLOGY)


def test_biology_bank_has_no_validation_errors(bank):
    assert bank.errors == []


def test_biology_bank_covers_all_94_lessons_with_at_least_eight_questions(bank):
    lessons = qb.lessons_in(bank.questions)
    assert len(lessons) == 94
    assert min(len(v) for v in lessons.values()) >= 8
    assert len(bank.questions) >= 750


def test_every_lesson_mixes_multiple_choice_and_short_answer(bank):
    for key, questions in qb.lessons_in(bank.questions).items():
        kinds = {q.kind for q in questions}
        assert kinds == {"MC", "SA"}, key
        assert sum(q.kind == "MC" for q in questions) >= 5, key


def test_the_longest_option_is_not_a_giveaway(bank):
    mc = [q for q in bank.questions if q.kind == "MC"]
    longest = sum(len(q.answer) > max(len(w) for w in q.wrong) for q in mc)
    assert longest / len(mc) <= 0.42, "the correct answer is too often the longest option"
    strong = [q for q in mc if len(q.answer) >= 1.4 * max(len(w) for w in q.wrong) and len(q.answer) >= 28]
    assert len(strong) <= 5


def test_short_answers_grade_against_themselves(bank):
    for q in (q for q in bank.questions if q.kind == "SA"):
        assert answers_equivalent(q.answer, q.answer)[0], q.answer


def test_short_answer_questions_do_not_give_the_answer_away(bank):
    for q in (q for q in bank.questions if q.kind == "SA" and not q.answer.replace(".", "").isdigit()):
        assert q.answer.lower() not in q.text.lower(), (q.text, q.answer)


def test_questions_are_spread_across_difficulty(bank):
    counts = {d: sum(q.difficulty == d for q in bank.questions) for d in range(1, 6)}
    assert counts[1] > 0 and counts[2] > 0 and counts[3] > 0


# ---------------------------------------------------------------------------
# The load command
# ---------------------------------------------------------------------------
@pytest.fixture
def lessons(db):
    subject = Subject.objects.create(name="biology", display_name="Biology")
    topic = Topic.objects.create(subject=subject, name="Cell Biology", order=1)
    lesson = Lesson.objects.create(topic=topic, title="1.1 - Cell Structure", content="x", order=1)
    other = Lesson.objects.create(topic=topic, title="1.2 - Kingdoms of Life", content="x", order=2)
    return {"lesson": lesson, "other": other, "subject": subject, "topic": topic}


def run(tmp_path, *args):
    return call_command("load_written_questions", "--subject", "biology", "--dir", str(tmp_path), *args)


def test_load_creates_questions_and_options(tmp_path, lessons):
    write(tmp_path, GOOD)
    run(tmp_path)
    qs = Question.objects.filter(lesson=lessons["lesson"])
    assert qs.count() == 2
    mc = qs.get(question_type="multiple_choice")
    options = list(MultipleChoiceOption.objects.filter(question=mc))
    assert len(options) == 4 and sum(o.is_correct for o in options) == 1
    assert mc.correct_answer == "Ribosomes" and mc.source == "Written for 285IQ (biology)" and mc.is_active
    assert qs.get(question_type="short_answer").correct_answer == "cellulose"


def test_loading_twice_does_not_duplicate(tmp_path, lessons):
    write(tmp_path, GOOD)
    run(tmp_path)
    run(tmp_path)
    assert Question.objects.count() == 2


def test_dry_run_and_inactive(tmp_path, lessons):
    write(tmp_path, GOOD)
    run(tmp_path, "--dry-run")
    assert Question.objects.count() == 0
    run(tmp_path, "--inactive")
    assert Question.objects.count() == 2 and not Question.objects.filter(is_active=True).exists()


def test_nothing_loads_if_any_question_is_invalid(tmp_path, lessons):
    write(tmp_path, GOOD + "MC | 1 | A question that is long enough? | A | A | C | D | An explanation that is long enough.\n")
    with pytest.raises(CommandError):
        run(tmp_path)
    assert Question.objects.count() == 0


def test_nothing_loads_if_a_lesson_is_missing(tmp_path, lessons):
    write(tmp_path, GOOD.replace("1.1 - Cell Structure", "9.9 - No Such Lesson"))
    with pytest.raises(CommandError):
        run(tmp_path)
    assert Question.objects.count() == 0


def test_review_document_is_written(tmp_path, lessons):
    write(tmp_path, GOOD)
    out = tmp_path / "review.md"
    run(tmp_path, "--dry-run", "--markdown", str(out))
    assert "✓ Ribosomes" in out.read_text(encoding="utf-8")


def test_retire_filler_switches_off_repeated_generic_questions_only(tmp_path, lessons):
    topic = lessons["topic"]
    made = []
    for i in range(22):  # the same generic question copied into 22 lessons
        lesson = Lesson.objects.create(topic=topic, title=f"9.{i} - Filler lesson", content="x", order=10 + i)
        made.append(Question.objects.create(lesson=lesson, question_text="What is diffusion?", correct_answer="x"))
    unique = Question.objects.create(lesson=lessons["other"], question_text="Name the organelle that makes ATP.", correct_answer="mitochondria")
    write(tmp_path, GOOD)
    run(tmp_path, "--retire-filler")
    assert not Question.objects.filter(question_text="What is diffusion?", is_active=True).exists()
    unique.refresh_from_db()
    assert unique.is_active
    assert Question.objects.filter(source__startswith="Written for 285IQ", is_active=True).count() == 2


def test_min_lessons_lowers_the_filler_threshold(tmp_path, lessons):
    topic = lessons["topic"]
    for i in range(3):  # copied into only 3 lessons: not filler by default, filler with --min-lessons 2
        lesson = Lesson.objects.create(topic=topic, title=f"8.{i} - Copy lesson", content="x", order=40 + i)
        Question.objects.create(lesson=lesson, question_text="Calculate moles in 18 g of water.", correct_answer="1")
    write(tmp_path, GOOD)
    run(tmp_path, "--retire-filler")
    assert Question.objects.filter(question_text__startswith="Calculate moles", is_active=True).count() == 3
    run(tmp_path, "--retire-filler", "--min-lessons", "2")
    assert not Question.objects.filter(question_text__startswith="Calculate moles", is_active=True).exists()
