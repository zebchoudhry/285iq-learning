"""
Base utilities for question import: resolve_lesson, create_question_from_dict.
"""
from learning.models import Subject, Topic, Lesson, Question, MultipleChoiceOption, SkillNode, QuestionStep


def resolve_subject(name):
    """Resolve subject by name (case-insensitive). Returns Subject or None."""
    if not name:
        return None
    name_clean = str(name).strip()
    return Subject.objects.filter(name__iexact=name_clean).first()


def resolve_topic(subject, topic_name):
    """Resolve topic by name within subject. Tries exact then icontains."""
    if not subject or not topic_name:
        return None
    tn = str(topic_name).strip()
    topic = Topic.objects.filter(subject=subject, name__iexact=tn).first()
    if topic:
        return topic
    return Topic.objects.filter(subject=subject, name__icontains=tn).first()


def resolve_lesson(subject, topic_name, lesson_title):
    """
    Resolve lesson by subject, topic, and lesson title.
    Returns (subject, topic, lesson). Tries all subjects matching name (case-insensitive)
    since DB may have both 'mathematics' and 'Mathematics'.
    """
    name_clean = str(subject or "").strip()
    if not name_clean:
        return None, None, None
    subjects = list(Subject.objects.filter(name__iexact=name_clean))
    lt = str(lesson_title).strip() if lesson_title else ""
    for subject_obj in subjects:
        topic_obj = resolve_topic(subject_obj, topic_name)
        if not topic_obj:
            continue
        if not lt:
            return subject_obj, topic_obj, None
        lesson = Lesson.objects.filter(
            topic=topic_obj,
        ).filter(title__iexact=lt).first()
        if not lesson:
            lesson = Lesson.objects.filter(
                topic=topic_obj,
            ).filter(title__icontains=lt).first()
        if lesson:
            return subject_obj, topic_obj, lesson
    if subjects:
        topic_obj = resolve_topic(subjects[0], topic_name)
        return subjects[0], topic_obj, None
    return None, None, None


def create_question_from_dict(lesson, d, skip_duplicates=True):
    """
    Create a Question from a dict. If multiple_choice, create MultipleChoiceOption records.
    Returns (question, created) or (None, False) if skipped/error.
    """
    question_text = d.get("question_text", "").strip()
    if not question_text:
        return None, False
    if skip_duplicates and Question.objects.filter(lesson=lesson, question_text=question_text).exists():
        return None, False
    question_type = d.get("question_type", "short_answer")
    if question_type not in ["short_answer", "multiple_choice", "calculation", "extended"]:
        question_type = "short_answer"
    options = d.get("options")
    if question_type == "multiple_choice" and (not options or not isinstance(options, list)):
        question_type = "short_answer"
        options = None
    difficulty = d.get("difficulty_level", 2)
    try:
        difficulty = int(difficulty)
        if difficulty < 1 or difficulty > 5:
            difficulty = 2
    except (TypeError, ValueError):
        difficulty = 2
    marks = d.get("marks_available", 1)
    try:
        marks = int(marks)
        if marks < 1:
            marks = 1
    except (TypeError, ValueError):
        marks = 1
    question = Question.objects.create(
        lesson=lesson,
        question_text=question_text,
        correct_answer=(d.get("correct_answer") or "").strip(),
        question_type=question_type,
        difficulty_level=difficulty,
        marks_available=marks,
        explanation=(d.get("explanation") or "").strip(),
        marking_scheme=(d.get("marking_scheme") or "").strip(),
        source=(d.get("source") or "").strip()[:100],
        is_active=True,
    )
    if question_type == "multiple_choice" and options:
        for i, opt in enumerate(options):
            if isinstance(opt, dict) and opt.get("text"):
                MultipleChoiceOption.objects.create(
                    question=question,
                    option_text=str(opt["text"])[:500],
                    is_correct=bool(opt.get("correct")),
                    order=i,
                )
    
    # Handle skill metadata
    skills = d.get("skills")
    if skills and isinstance(skills, list):
        for skill_code in skills:
            if skill_code and isinstance(skill_code, str):
                skill_code_clean = str(skill_code).strip()
                if skill_code_clean:
                    SkillNode.objects.get_or_create(
                        code=skill_code_clean,
                        defaults={
                            "subject": "Maths",
                            "difficulty_weight": 1.0,
                        }
                    )
    
    # Handle step metadata
    steps = d.get("steps")
    if steps and isinstance(steps, list):
        for step_data in steps:
            if not isinstance(step_data, dict):
                continue
            skill_code = step_data.get("skill")
            if not skill_code:
                continue
            skill_code_clean = str(skill_code).strip()
            if not skill_code_clean:
                continue
            # Get or create the skill node
            skill_node, _ = SkillNode.objects.get_or_create(
                code=skill_code_clean,
                defaults={
                    "subject": "Maths",
                    "difficulty_weight": 1.0,
                }
            )
            # Create QuestionStep (use update_or_create to prevent duplicates)
            step_order = step_data.get("step_order", 0)
            try:
                step_order = int(step_order)
            except (TypeError, ValueError):
                step_order = 0
            QuestionStep.objects.update_or_create(
                question=question,
                step_order=step_order,
                defaults={
                    "skill": skill_node,
                    "expected_expression": (step_data.get("expected_expression") or "").strip(),
                    "hint_level_1": (step_data.get("hint_level_1") or "").strip(),
                    "hint_level_2": (step_data.get("hint_level_2") or "").strip(),
                }
            )
    
    return question, True
