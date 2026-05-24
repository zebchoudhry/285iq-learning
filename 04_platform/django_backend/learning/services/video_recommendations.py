from learning.models import SkillVideo


def recommend_skill_video(*, question, skill=None, tier=None, exam_board=None):
    """
    Return the best short intervention video for a stuck point.

    Matching order is deliberately conservative:
    1. exact skill
    2. exact topic
    3. subject-wide fallback
    """
    topic = question.lesson.topic
    subject = topic.subject
    qs = SkillVideo.objects.filter(is_active=True)

    if tier:
        qs = qs.filter(tier__in=[tier, "both"])
    if exam_board:
        qs = qs.filter(exam_board__in=["", exam_board])

    if skill:
        match = qs.filter(skill=skill).select_related("subject", "topic", "skill").first()
        if match:
            return match

    match = qs.filter(topic=topic).select_related("subject", "topic", "skill").first()
    if match:
        return match

    return qs.filter(subject=subject).select_related("subject", "topic", "skill").first()
