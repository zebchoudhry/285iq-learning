from rest_framework import serializers
from .models import (
    Subject,
    Topic,
    Lesson,
    Flashcard,
    Question,
    MultipleChoiceOption,
    StudentProgress,
    QuizAttempt,
    TopicStrengthSnapshot,
    QuestionStep,
    StudentSkillState,
    MistakeBankItem,
    StruggleEvent,
    SkillVideo,
)
from django.utils import timezone
from users.models import StudentTopicPerformance

from learning.services.answer_grading import answers_equivalent


def _bump_single_skill_for_question(user, question, is_correct):
    """
    Attribute one question attempt to the weakest linked skill (one bump per question).
    """
    steps = list(
        QuestionStep.objects.filter(question=question)
        .select_related("skill")
        .order_by("step_order")
    )
    if not steps:
        return
    candidates = []
    for step in steps:
        skill_state, _ = StudentSkillState.objects.get_or_create(
            student=user,
            skill=step.skill,
            defaults={
                "attempts": 0,
                "failures": 0,
                "rolling_accuracy": 0.0,
                "mastery_score": 0.0,
            },
        )
        candidates.append((step.step_order, skill_state))
    _, skill_state = min(candidates, key=lambda x: (x[1].rolling_accuracy, x[0]))

    skill_state.attempts += 1
    if not is_correct:
        skill_state.failures += 1
    if skill_state.attempts > 0:
        skill_state.rolling_accuracy = (
            (skill_state.attempts - skill_state.failures) / skill_state.attempts
        ) * 100.0
    else:
        skill_state.rolling_accuracy = 0.0
    skill_state.mastery_score = skill_state.rolling_accuracy
    skill_state.last_attempt_at = timezone.now()
    if skill_state.attempts < 3:
        skill_state.status = "NEW"
    elif skill_state.rolling_accuracy < 60:
        skill_state.status = "LEARNING"
    elif skill_state.rolling_accuracy < StudentSkillState.MASTERY_MIN_ACCURACY:
        skill_state.status = "IMPROVING"
    elif (
        skill_state.rolling_accuracy >= StudentSkillState.MASTERY_MIN_ACCURACY
        and skill_state.attempts >= StudentSkillState.MASTERY_MIN_ATTEMPTS
    ):
        skill_state.status = "MASTERED"
    else:
        skill_state.status = "IMPROVING"
    skill_state.save()


def _infer_wrong_category(raw_answer, is_correct, selected_option_id, error_type):
    if is_correct:
        return "none"
    if error_type and error_type != "none":
        return error_type
    if selected_option_id:
        return "misread_options"
    text = (raw_answer or "").strip()
    if not text:
        return "blank_or_timeout"
    if len(text) <= 2:
        return "guess"
    return "method_error"


def _estimate_partial_marks(question, is_correct, raw_answer):
    marks_total = int(getattr(question, "marks_available", 1) or 1)
    if is_correct:
        return marks_total
    if question.question_type == "multiple_choice":
        return 0
    answer = (raw_answer or "").strip().lower()
    correct = (question.correct_answer or "").strip().lower()
    if not answer or not correct:
        return 0

    # Lightweight lexical overlap to grant partial credit for method-bearing answers.
    answer_tokens = [t for t in answer.replace(",", " ").split() if t]
    correct_tokens = [t for t in correct.replace(",", " ").split() if t]
    if not answer_tokens or not correct_tokens:
        return 0
    overlap = len(set(answer_tokens).intersection(set(correct_tokens)))
    ratio = overlap / max(1, len(set(correct_tokens)))
    if ratio >= 0.6:
        return min(marks_total - 1, max(1, int(round(marks_total * 0.5))))
    if ratio >= 0.35:
        return 1 if marks_total > 1 else 0
    return 0


def _first_failed_skill(question):
    step = (
        QuestionStep.objects.filter(question=question)
        .select_related("skill")
        .order_by("step_order")
        .first()
    )
    if not step:
        return None
    return {
        "skill_code": step.skill.code,
        "step_order": step.step_order,
        "hint_level_1": step.hint_level_1 or "",
    }


def _remediation_tip(wrong_category, failed_skill):
    skill_code = failed_skill.get("skill_code") if failed_skill else None
    if wrong_category in ("blank_or_timeout", "guess"):
        return "Use a 20-second plan: identify knowns, target, and one valid method before answering."
    if wrong_category in ("conceptual", "method_error", "structural"):
        return (
            f"Rebuild the method for {skill_code} with one worked example, then retry a similar question."
            if skill_code
            else "Rebuild the method with one worked example, then retry a similar question."
        )
    if wrong_category == "misread_options":
        return "Read every option fully and eliminate two clearly wrong options before selecting."
    return "Review the explanation, then attempt one more question on the same skill."

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'display_name', 'description', 'tier', 'is_active']

class TopicSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.display_name', read_only=True)
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'subject', 'subject_name', 'order', 'is_active']

class LessonSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.display_name', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'topic', 'topic_name', 'subject_name',
                 'lesson_type', 'difficulty_level', 'estimated_duration', 'video_url']


class FlashcardSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.display_name', read_only=True)

    class Meta:
        model = Flashcard
        fields = ['id', 'front', 'back', 'topic', 'topic_name', 'subject_name', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'difficulty_level', 
                 'marks_available', 'correct_answer', 'explanation', 'lesson', 'lesson_title']


class QuestionForQuizSerializer(serializers.ModelSerializer):
    """Question payload for quiz UI - excludes correct_answer until after submit."""
    options = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'difficulty_level', 'marks_available', 'options']
    
    def get_options(self, obj):
        if obj.question_type != 'multiple_choice':
            return []
        return list(
            obj.options.order_by('order').values('id', 'option_text')
        )


class MistakeBankItemSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    marks_available = serializers.IntegerField(source='question.marks_available', read_only=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.display_name', read_only=True)
    skill_code = serializers.CharField(source='skill.code', read_only=True, allow_null=True)

    class Meta:
        model = MistakeBankItem
        fields = [
            'id',
            'question',
            'question_text',
            'question_type',
            'marks_available',
            'topic',
            'topic_name',
            'subject_name',
            'skill_code',
            'reason',
            'wrong_category',
            'last_student_answer',
            'remediation_tip',
            'attempts_count',
            'correct_retries',
            'status',
            'first_seen_at',
            'last_seen_at',
            'next_review_at',
        ]


class StruggleEventSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.display_name', read_only=True)
    skill_code = serializers.CharField(source='skill.code', read_only=True, allow_null=True)

    class Meta:
        model = StruggleEvent
        fields = [
            'id',
            'question',
            'question_text',
            'topic',
            'topic_name',
            'subject_name',
            'skill_code',
            'trigger',
            'stuck_point',
            'mistake_type',
            'confidence_level',
            'time_to_first_action_ms',
            'time_spent_ms',
            'diagnostic_message',
            'recommended_intervention',
            'created_at',
        ]


class SkillVideoSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.display_name', read_only=True, allow_null=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True, allow_null=True)
    skill_code = serializers.CharField(source='skill.code', read_only=True, allow_null=True)

    class Meta:
        model = SkillVideo
        fields = [
            'id',
            'title',
            'subject',
            'subject_name',
            'topic',
            'topic_name',
            'skill_code',
            'exam_board',
            'tier',
            'duration_seconds',
            'video_url',
            'thumbnail_url',
            'intervention_goal',
        ]


# ---------------------------------------------------------------------
# AttemptSerializer - minimal endpoint to record a student attempt
# ---------------------------------------------------------------------
class AttemptSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option_id = serializers.IntegerField(required=False, allow_null=True)
    answer = serializers.CharField(required=False, allow_blank=True)
    time_spent_ms = serializers.IntegerField(required=False, default=0)
    time_to_first_action_ms = serializers.IntegerField(required=False, allow_null=True)
    error_type = serializers.ChoiceField(
        choices=[c[0] for c in QuizAttempt.ERROR_TYPE_CHOICES],
        required=False,
        default='none'
    )
    confidence_level = serializers.ChoiceField(
        choices=['guessed', 'unsure', 'confident'],
        required=False,
        default='unsure',
    )

    def validate(self, attrs):
        try:
            question = Question.objects.get(id=attrs['question_id'])
        except Question.DoesNotExist:
            raise serializers.ValidationError({"question_id": "Question not found"})
        attrs['question'] = question
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Authentication required"})

        question = validated_data['question']
        selected_option_id = validated_data.get('selected_option_id')
        raw_answer = validated_data.get("answer") or ""
        is_correct = False

        llm_mark_result = None
        if selected_option_id:
            try:
                opt = MultipleChoiceOption.objects.get(id=selected_option_id, question=question)
                is_correct = opt.is_correct
            except MultipleChoiceOption.DoesNotExist:
                is_correct = False
        elif question.question_type in ("calculation", "extended"):
            from learning.services.answer_grading import llm_mark_calculation
            marks_avail = int(getattr(question, "marks_available", 1) or 1)
            llm_mark_result = llm_mark_calculation(question, raw_answer, marks_avail)
            is_correct = llm_mark_result["is_correct"]
        else:
            is_correct, _ = answers_equivalent(raw_answer, question.correct_answer or "")

        attempt = QuizAttempt.objects.create(
            student=user,
            question=question,
            is_correct=is_correct,
            error_type=validated_data.get('error_type', 'none'),
            time_spent_ms=validated_data.get('time_spent_ms') or 0,
            time_to_first_action_ms=validated_data.get('time_to_first_action_ms'),
        )
        # Flag for review if 3+ consecutive wrong answers on this question
        if not is_correct:
            recent_attempts = QuizAttempt.objects.filter(
                student=user,
                question=question,
            ).order_by('-attempted_at')[:3]
            if (
                recent_attempts.count() >= 3
                and all(not a.is_correct for a in recent_attempts)
            ):
                QuizAttempt.objects.filter(
                    student=user,
                    question=question,
                ).update(needs_review=True)

        try:
            _bump_single_skill_for_question(user, question, is_correct)
        except Exception:
            pass

        # Record study activity for parent dashboard (one session per day per subject)
        try:
            from learning.services.study_activity import record_study_activity
            record_study_activity(
                student=user,
                subject=question.lesson.topic.subject,
                topic=question.lesson.topic,
                questions_attempted=1,
                questions_correct=1 if is_correct else 0,
            )
        except Exception:
            pass

        # Update per-topic performance (best-effort, ignore failures)
        try:
            stp, _ = StudentTopicPerformance.objects.get_or_create(student=user, topic=question.lesson.topic)
            stp.questions_attempted = stp.questions_attempted + 1
            if is_correct:
                stp.questions_correct = stp.questions_correct + 1
            stp.save()
        except Exception:
            pass

        # Update XP, streak, and check achievements (best-effort)
        try:
            profile = getattr(user, 'profile', None)
            if profile is not None:
                profile.total_xp = profile.total_xp + (10 if is_correct else 2)
                profile.save(update_fields=['total_xp'])
                profile.update_streak()
                from users.achievements import check_and_award_achievements
                check_and_award_achievements(user)
        except Exception:
            pass

        # Daily topic strength snapshot (best-effort)
        try:
            topic = question.lesson.topic
            attempts_qs = QuizAttempt.objects.filter(
                student=user,
                question__lesson__topic=topic,
            ).order_by('-attempted_at')
            total_attempts = attempts_qs.count()
            if total_attempts > 0:
                total_correct = attempts_qs.filter(is_correct=True).count()
                recent = list(attempts_qs[:5])
                recent_correct = sum(1 for a in recent if a.is_correct)
                TopicStrengthSnapshot.objects.update_or_create(
                    student=user,
                    topic=topic,
                    date=timezone.now().date(),
                    defaults={
                        'accuracy_rate': total_correct / total_attempts,
                        'recent_accuracy': (recent_correct / len(recent)) if recent else 0.0,
                        'questions_attempted': total_attempts,
                    }
                )
        except Exception:
            pass

        wrong_category = _infer_wrong_category(
            raw_answer=raw_answer,
            is_correct=is_correct,
            selected_option_id=selected_option_id,
            error_type=validated_data.get("error_type", "none"),
        )
        if llm_mark_result is not None:
            partial_marks = llm_mark_result["marks_awarded"]
            llm_mark_feedback = llm_mark_result.get("feedback", "")
        else:
            partial_marks = _estimate_partial_marks(question, is_correct, raw_answer)
            llm_mark_feedback = ""
        failed_skill = None if is_correct else _first_failed_skill(question)
        remediation_tip = llm_mark_feedback or _remediation_tip(wrong_category, failed_skill)

        try:
            from learning.services.mistake_bank import record_attempt_learning_signals
            record_attempt_learning_signals(
                student=user,
                attempt=attempt,
                question=question,
                raw_answer=raw_answer,
                is_correct=is_correct,
                wrong_category=wrong_category,
                failed_skill=failed_skill,
                remediation_tip=remediation_tip,
                confidence_level=validated_data.get("confidence_level", "unsure"),
            )
        except Exception:
            pass

        # Attach transient analysis fields for response payload construction.
        attempt.partial_marks = partial_marks
        attempt.marks_available = int(getattr(question, "marks_available", 1) or 1)
        attempt.wrong_category = wrong_category
        attempt.failed_skill = failed_skill
        attempt.remediation_tip = remediation_tip

        return attempt
