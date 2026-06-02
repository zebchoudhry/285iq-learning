"""
Mastery gate: checks if a student has reached mastery on a topic
before allowing advancement. Mastery = success_rate >= 0.80 over last 10 attempts.
"""

MASTERY_THRESHOLD = 0.80
MIN_ATTEMPTS_FOR_GATE = 5


def topic_mastery_status(student, topic_id) -> dict:
    """
    Returns mastery status for a student on a given topic.
    """
    from users.models import StudentTopicPerformance
    from learning.models import QuizAttempt

    # Get all-time performance
    try:
        perf = StudentTopicPerformance.objects.get(student=student, topic_id=topic_id)
        all_time_attempts = perf.questions_attempted
        all_time_correct = perf.questions_correct
    except StudentTopicPerformance.DoesNotExist:
        return {
            'mastered': False,
            'attempts': 0,
            'success_rate': 0.0,
            'questions_to_mastery': MIN_ATTEMPTS_FOR_GATE,
            'topic_id': topic_id,
        }

    # Get recent QuizAttempts (last 10) for this topic
    recent_attempts = QuizAttempt.objects.filter(
        student=student,
        question__lesson__topic_id=topic_id,
    ).order_by('-attempted_at')[:10]

    recent_total = len(recent_attempts)
    recent_correct = sum(1 for a in recent_attempts if a.is_correct)

    # Use recent if sufficient, else fall back to all-time
    if recent_total >= MIN_ATTEMPTS_FOR_GATE:
        attempts = recent_total
        correct = recent_correct
    else:
        attempts = all_time_attempts
        correct = all_time_correct

    if attempts == 0:
        success_rate = 0.0
    else:
        success_rate = round(correct / attempts, 3)

    mastered = attempts >= MIN_ATTEMPTS_FOR_GATE and success_rate >= MASTERY_THRESHOLD

    # How many more correct answers needed to hit 80% over the next 10 attempts
    if mastered:
        questions_to_mastery = 0
    else:
        # We want: (correct + x) / 10 >= 0.80 => x >= 8 - correct
        # Using a window of 10
        base_correct = recent_correct if recent_total >= MIN_ATTEMPTS_FOR_GATE else correct
        needed = max(0, int(MASTERY_THRESHOLD * 10) - base_correct)
        questions_to_mastery = needed

    return {
        'mastered': mastered,
        'attempts': attempts,
        'success_rate': success_rate,
        'questions_to_mastery': questions_to_mastery,
        'topic_id': topic_id,
    }


def check_mastery_gate(student, topic_id) -> dict:
    """
    Returns gating decision for the student on the given topic.
    """
    from learning.models import StudentExamSettings, Topic

    # Check if mastery gate is enabled for this student's subject
    try:
        topic = Topic.objects.select_related('subject').get(id=topic_id)
        exam_settings = StudentExamSettings.objects.get(
            student=student,
            subject=topic.subject,
        )
        if not exam_settings.mastery_gate_enabled:
            return {'gated': False, 'reason': 'gate_disabled'}
    except (Topic.DoesNotExist, StudentExamSettings.DoesNotExist):
        pass  # Default: gate is enabled

    status = topic_mastery_status(student, topic_id)

    if status['attempts'] < MIN_ATTEMPTS_FOR_GATE:
        return {
            'gated': False,
            'reason': 'insufficient_data',
            'status': status,
        }

    if status['success_rate'] >= MASTERY_THRESHOLD:
        return {
            'gated': False,
            'reason': 'mastered',
            'status': status,
        }

    return {
        'gated': True,
        'reason': 'below_threshold',
        'status': status,
        'message': (
            f"Keep drilling! You need {status['questions_to_mastery']} more correct answers "
            f"to master this topic."
        ),
    }
