"""
Aggregate recent MistakeBankItem data and use LLM to produce a plain-English
weakness summary for the student.
"""
import logging

logger = logging.getLogger(__name__)


def build_weakness_digest(student, subject_id=None, top_n=3) -> dict:
    """
    Build a weakness digest for the student, optionally filtered by subject.
    Returns a dict with weaknesses list, summary string, llm_used flag, and top focus topic.
    """
    from learning.models import MistakeBankItem
    from users.models import StudentTopicPerformance
    from learning.services.llm_service import generate as llm_generate

    # Query MistakeBankItems for this student (active), filter by subject if given
    mb_qs = MistakeBankItem.objects.filter(
        student=student,
        status='active',
    ).select_related('question__lesson__topic__subject', 'skill', 'topic__subject')

    if subject_id:
        mb_qs = mb_qs.filter(topic__subject_id=subject_id)

    mb_qs = mb_qs.order_by('-attempts_count')[:10]

    # Query StudentTopicPerformance for weak topics
    perf_qs = StudentTopicPerformance.objects.filter(
        student=student,
        questions_attempted__gte=5,
    ).select_related('topic__subject')

    if subject_id:
        perf_qs = perf_qs.filter(topic__subject_id=subject_id)

    # Filter in Python for ratio < 0.60
    weak_perfs = [p for p in perf_qs if (p.questions_correct / p.questions_attempted) < 0.60]
    weak_perfs.sort(key=lambda p: p.questions_correct / p.questions_attempted)
    weak_perfs = weak_perfs[:5]

    # Build a dict of topic_id -> weakness entry
    topic_map = {}

    # From MistakeBankItems
    for item in mb_qs:
        topic = item.topic
        tid = topic.id
        if tid not in topic_map:
            subject_name = ''
            try:
                subject_name = topic.subject.display_name
            except Exception:
                pass
            topic_map[tid] = {
                'topic_id': tid,
                'topic_name': topic.name,
                'subject_name': subject_name,
                'skill_code': item.skill.code if item.skill else '',
                'wrong_count': 0,
                'success_rate': 0.0,
                'example_question_text': '',
            }
        entry = topic_map[tid]
        entry['wrong_count'] += item.attempts_count
        total = item.attempts_count + item.correct_retries
        if total > 0:
            entry['success_rate'] = round(item.correct_retries / total, 3)
        if not entry['example_question_text'] and item.question:
            entry['example_question_text'] = (item.question.question_text or '')[:120]

    # Merge in StudentTopicPerformance data
    for perf in weak_perfs:
        tid = perf.topic_id
        ratio = perf.questions_correct / perf.questions_attempted
        if tid not in topic_map:
            subject_name = ''
            try:
                subject_name = perf.topic.subject.display_name
            except Exception:
                pass
            topic_map[tid] = {
                'topic_id': tid,
                'topic_name': perf.topic.name,
                'subject_name': subject_name,
                'skill_code': '',
                'wrong_count': perf.questions_attempted - perf.questions_correct,
                'success_rate': round(ratio, 3),
                'example_question_text': '',
            }
        else:
            # Update success rate with more complete data
            topic_map[tid]['success_rate'] = round(ratio, 3)

    # Take top_n by wrong_count
    weaknesses = sorted(topic_map.values(), key=lambda x: x['wrong_count'], reverse=True)[:top_n]

    top_focus_topic_id = weaknesses[0]['topic_id'] if weaknesses else None
    top_focus_topic_name = weaknesses[0]['topic_name'] if weaknesses else None

    # Generate summary
    llm_used = False
    summary = ''

    if weaknesses:
        try:
            import json
            prompt = (
                "You are a GCSE STEM tutor. A student's performance data shows these weaknesses: "
                + json.dumps(weaknesses)
                + "\n\nWrite a friendly, encouraging 3-bullet summary (max 60 words each bullet) of: "
                "1) what the student is struggling with, "
                "2) why it typically trips students up, "
                "3) one concrete revision tip per weakness. "
                "Keep it under 200 words total. Return plain text, no JSON."
            )
            result = llm_generate(prompt, max_tokens=350, temperature=0.4)
            if result and 'mock' not in result.lower()[:20]:
                summary = result
                llm_used = True
        except Exception as exc:
            logger.debug("LLM generate failed in weakness_digest: %s", exc)

    if not summary:
        # Static fallback
        if weaknesses:
            top = weaknesses[0]
            skill_hint = f" Focus on practicing {top['skill_code']} questions" if top['skill_code'] else ""
            parts = [f"• Your weakest area is {top['topic_name']}.{skill_hint} until you score 4/5 or better."]
            for w in weaknesses[1:]:
                parts.append(f"• Also work on {w['topic_name']} — keep drilling until you feel confident.")
            summary = '\n'.join(parts)
        else:
            summary = "Great work! No significant weaknesses detected yet. Keep practising!"

    return {
        'weaknesses': weaknesses,
        'summary': summary,
        'llm_used': llm_used,
        'top_focus_topic_id': top_focus_topic_id,
        'top_focus_topic_name': top_focus_topic_name,
    }
