"""Quality checks for the hand-written chemistry bank (the same bar as the biology bank)."""
import importlib
from pathlib import Path

import pytest
from django.conf import settings

from learning.services import question_bank as qb
from learning.services.answer_grading import answers_equivalent

CHEMISTRY = Path(settings.BASE_DIR) / "question_bank" / "chemistry"

# Every live chemistry lesson in production on 2026-11-25, as topic -> number of lessons.
EXPECTED_TOPICS = {
    "Atomic Structure": 12, "Bonding": 11, "Quantitative Chemistry": 9, "Chemical Changes": 10,
    "Energy Changes": 4, "Rates & Equilibrium": 5, "Organic Chemistry": 12,
}


@pytest.fixture(scope="module")
def bank():
    return qb.parse_directory(CHEMISTRY)


def test_no_validation_errors(bank):
    assert bank.errors == []


def test_covers_all_63_lessons_with_eight_questions(bank):
    lessons = qb.lessons_in(bank.questions)
    assert len(lessons) == 63 and len(bank.questions) == 504
    per_topic = {}
    for topic, _ in lessons:
        per_topic[topic] = per_topic.get(topic, 0) + 1
    assert per_topic == EXPECTED_TOPICS
    assert min(len(v) for v in lessons.values()) >= 8


def test_every_lesson_mixes_multiple_choice_and_short_answer(bank):
    for key, questions in qb.lessons_in(bank.questions).items():
        assert {q.kind for q in questions} == {"MC", "SA"}, key
        assert sum(q.kind == "MC" for q in questions) >= 5, key


def test_the_longest_option_is_not_a_giveaway(bank):
    mc = [q for q in bank.questions if q.kind == "MC"]
    longest = sum(len(q.answer) > max(len(w) for w in q.wrong) for q in mc)
    assert longest / len(mc) <= 0.42
    strong = [q for q in mc if len(q.answer) >= 1.4 * max(len(w) for w in q.wrong) and len(q.answer) >= 28]
    assert strong == []


def test_short_answers_grade_against_themselves_and_are_not_in_the_question(bank):
    for q in (q for q in bank.questions if q.kind == "SA"):
        assert answers_equivalent(q.answer, q.answer)[0], q.answer
        if not q.answer.replace(".", "").isdigit():
            assert q.answer.lower() not in q.text.lower(), (q.text, q.answer)


def test_spread_across_difficulty(bank):
    counts = {d: sum(q.difficulty == d for q in bank.questions) for d in range(1, 4)}
    assert all(c >= 50 for c in counts.values()), counts


def test_no_written_question_reuses_old_filler_wording(bank):
    """If it did, the loader would skip it as already present and then retire the filler copy."""
    filler = {
        "what is the ph of a neutral solution?", "what products are formed when an acid reacts with a base?",
        "what happens to the temperature in an exothermic reaction?", "what is the general formula for alkanes?",
        "what type of bond forms between a metal and a non-metal?", "balance the equation: h₂ + o₂ → h₂o",
        "what type of bond is formed when atoms share pairs of electrons?",
        "at which electrode do negatively charged ions (anions) move to?",
        "what happens to reactivity as you go down group 1 (alkali metals)?",
    }
    assert not [q.text for q in bank.questions if q.text.lower() in filler]


def test_load_migration_does_nothing_on_an_empty_database(db):
    migration = importlib.import_module("learning.migrations.0022_load_chemistry_question_bank")
    from django.apps import apps
    from learning.models import Question
    migration.load(apps, None)
    assert not Question.objects.exists()


# The live chemistry lessons in production on 2026-11-25 (topic / title), copied from the database.
PRODUCTION_LESSONS = """\
Atomic Structure / 1.1 - Atoms
Atomic Structure / 1.2 - Elements, Isotopes & Relative Atomic Mass
Atomic Structure / 1.3 - Compounds, Molecules & Mixtures
Atomic Structure / 1.4 - Balancing Chemical Equations
Atomic Structure / 1.5 - Filtration & Crystallisation
Atomic Structure / 1.6 - Distillation
Atomic Structure / 1.7 - The History of the Atom
Atomic Structure / 1.8 - Electronic Structure
Atomic Structure / 1.9 - Development of the Periodic Table
Atomic Structure / 1.10 - Metals & Non-metals
Atomic Structure / 1.11 - Group 1 (Alkali Metals)
Atomic Structure / 1.12 - Group 7 & Group 0 (Halogens & Noble Gases)
Bonding / 2.1 - Formation of Ions
Bonding / 2.2 - Ionic Bonding
Bonding / 2.3 - Ionic Compounds
Bonding / 2.4 - Molecular & Empirical Formulas
Bonding / 2.5 - Covalent Bonding
Bonding / 2.6 - Types of Covalent Structures
Bonding / 2.7 - Diamond & Graphite
Bonding / 2.8 - Graphene & Fullerenes
Bonding / 2.9 - Metallic Bonding
Bonding / 2.10 - States of Matter
Bonding / 2.11 - Nanoparticles
Quantitative Chemistry / 3.1 - Relative Formula Mass
Quantitative Chemistry / 3.2 - Moles & Mass
Quantitative Chemistry / 3.3 - Calculating Mass in Reactions
Quantitative Chemistry / 3.4 - Conservation of Mass
Quantitative Chemistry / 3.5 - Limiting Reactants
Quantitative Chemistry / 3.6 - Concentration Calculations (grams/dm³)
Quantitative Chemistry / 3.7 - Gas Calculations
Quantitative Chemistry / 3.8 - Atom Economy
Quantitative Chemistry / 3.9 - Percentage Yield
Chemical Changes / 4.1 - Acids & Bases
Chemical Changes / 4.2 - Titration Practical
Chemical Changes / 4.3 - Strong Acids & Weak Acids
Chemical Changes / 4.4 - Neutralisation Reactions
Chemical Changes / 4.5 - The Reactivity Series & Displacement Reactions
Chemical Changes / 4.6 - Separating Metals from Metal Oxides
Chemical Changes / 4.7 - Redox Reactions
Chemical Changes / 4.8 - Electrolysis 1 - Introduction
Chemical Changes / 4.9 - Electrolysis 2 - Aluminium Oxide
Chemical Changes / 4.10 - Electrolysis 3 - Aqueous Solutions
Energy Changes / 5.1 - Exothermic & Endothermic Reactions
Energy Changes / 5.2 - Bond Energies
Energy Changes / 5.3 - Cells & Batteries
Energy Changes / 5.4 - Fuel Cells
Rates & Equilibrium / 6.1 - Rates of Reaction
Rates & Equilibrium / 6.2 - Factors Affecting Rates of Reaction & Collision Theory
Rates & Equilibrium / 6.3 - Measuring Rates of Reaction from a Graph
Rates & Equilibrium / 6.4 - Reversible Reactions & Dynamic Equilibrium
Rates & Equilibrium / 6.5 - Le Chatelier's Principle
Organic Chemistry / 7.1 - Hydrocarbons
Organic Chemistry / 7.2 - Alkanes - Properties & Combustion
Organic Chemistry / 7.3 - Fractional Distillation
Organic Chemistry / 7.4 - Cracking & Alkenes
Organic Chemistry / 7.5 - Reaction of Alkenes
Organic Chemistry / 7.6 - Addition Polymers
Organic Chemistry / 7.7 - Alcohols
Organic Chemistry / 7.8 - Production of Ethanol
Organic Chemistry / 7.9 - Carboxylic Acids
Organic Chemistry / 7.10 - Esters
Organic Chemistry / 7.11 - Condensation Polymers
Organic Chemistry / 7.12 - Naturally Occurring Polymers"""


def production_lessons():
    return [tuple(line.split(" / ", 1)) for line in PRODUCTION_LESSONS.splitlines()]


def test_bank_lessons_match_production_exactly(bank):
    assert set(qb.lessons_in(bank.questions)) == set(production_lessons())


def test_migration_loads_the_bank_and_retires_only_pasted_copies(db):
    from django.apps import apps
    from learning.models import Lesson, Question, Subject, Topic

    migration = importlib.import_module("learning.migrations.0022_load_chemistry_question_bank")
    subject = Subject.objects.create(name="chemistry", display_name="GCSE Chemistry")
    topics, lessons = {}, []
    for n, (topic_name, title) in enumerate(production_lessons()):
        topic = topics.get(topic_name) or Topic.objects.create(subject=subject, name=topic_name, order=len(topics) + 1)
        topics[topic_name] = topic
        lessons.append(Lesson.objects.create(topic=topic, title=title, content="x", order=n))
    for lesson in lessons[:30]:  # a generic question pasted into 30 lessons
        Question.objects.create(lesson=lesson, question_text="What type of bond forms between a metal and a non-metal?",
                                correct_answer="ionic")
    for lesson in lessons[:3]:  # a calculation pasted into 3 lessons
        Question.objects.create(lesson=lesson, question_text="Calculate the number of moles in 18 g of a substance with Mr = 18.",
                                correct_answer="1")
    unique = Question.objects.create(lesson=lessons[5], question_text="A one-off question that belongs here?", correct_answer="x")

    migration.load(apps, None)

    written = Question.objects.filter(source="Written for 285IQ (chemistry)", is_active=True)
    assert written.count() == 504
    assert not Question.objects.filter(question_text__startswith="What type of bond forms", is_active=True).exists()
    assert not Question.objects.filter(question_text__startswith="Calculate the number of moles", is_active=True).exists()
    unique.refresh_from_db()
    assert unique.is_active
    assert all(Question.objects.filter(lesson=l, is_active=True).count() >= 8 for l in lessons)

    migration.load(apps, None)  # running again changes nothing
    assert Question.objects.filter(source="Written for 285IQ (chemistry)").count() == 504

    migration.unload(apps, None)
    assert not Question.objects.filter(source="Written for 285IQ (chemistry)", is_active=True).exists()
    assert Question.objects.filter(question_text__startswith="What type of bond forms", is_active=True).count() == 30
