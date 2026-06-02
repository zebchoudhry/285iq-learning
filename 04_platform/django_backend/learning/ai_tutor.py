import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.utils import timezone
from .models import Topic, Subject, Question
from users.models import StudentTopicPerformance

logger = logging.getLogger(__name__)

User = get_user_model()

class PersonalizedAITutor:
    def __init__(self, student_id=1):
        try:
            self.student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            self.student = User.objects.first()  # Fallback to first user
    
    def analyze_message(self, message):
        """Analyze student's message for subject content and learning indicators"""
        message_lower = message.lower()
        
        # Check for subject mentions
        subjects = Subject.objects.all()
        mentioned_subject = None
        for subject in subjects:
            if subject.name in message_lower or subject.display_name.lower() in message_lower:
                mentioned_subject = subject
                break
        
        # Check for learning indicators
        struggle_words = ['difficult', 'hard', 'confused', 'don\'t understand', 'stuck', 'help']
        confidence_words = ['easy', 'understand', 'got it', 'clear', 'makes sense']
        question_words = ['how', 'what', 'why', 'when', 'where']
        
        is_struggling = any(word in message_lower for word in struggle_words)
        is_confident = any(word in message_lower for word in confidence_words)
        is_asking_question = any(word in message_lower for word in question_words) or '?' in message
        
        return {
            'subject': mentioned_subject,
            'is_struggling': is_struggling,
            'is_confident': is_confident,
            'is_asking_question': is_asking_question,
            'message_length': len(message.split())
        }
    
    def get_student_weak_areas(self):
        """Get topics where student is struggling"""
        weak_performances = StudentTopicPerformance.objects.filter(
            student=self.student,
            questions_attempted__gte=3  # At least 3 attempts
        ).filter(
            questions_correct__lt=models.F('questions_attempted') * 0.7  # Less than 70% success
        ).order_by('questions_correct')[:3]  # Top 3 weakest areas
        
        return [perf.topic for perf in weak_performances]
    
    def get_student_strong_areas(self):
        """Get topics where student is doing well"""
        strong_performances = StudentTopicPerformance.objects.filter(
            student=self.student,
            questions_attempted__gte=3
        ).filter(
            questions_correct__gte=models.F('questions_attempted') * 0.8  # 80%+ success
        ).order_by('-questions_correct')[:2]
        
        return [perf.topic for perf in strong_performances]
    
    def generate_response(self, message):
        """Generate personalized AI tutor response"""
        analysis = self.analyze_message(message)
        weak_areas = self.get_student_weak_areas()
        strong_areas = self.get_student_strong_areas()
        
        # Build personalized response
        if analysis['subject']:
            return self.generate_subject_response(message, analysis, weak_areas, strong_areas)
        elif analysis['is_struggling']:
            return self.generate_help_response(weak_areas)
        elif analysis['is_asking_question']:
            return self.generate_question_response(message, analysis)
        else:
            return self.generate_general_encouragement(strong_areas, weak_areas)
    
    def generate_subject_response(self, message, analysis, weak_areas, strong_areas):
        """Generate response for subject-specific messages"""
        subject = analysis['subject']
        subject_topics = Topic.objects.filter(subject=subject, is_active=True)[:3]
        
        # Check if mentioned subject is in weak areas
        is_weak_subject = any(topic.subject == subject for topic in weak_areas)
        
        if is_weak_subject:
            response = f"I see you're working on {subject.display_name}! This is actually an area where you could improve. "
            response += f"Let's focus on the fundamentals first:\n\n"
            for topic in subject_topics:
                response += f"• {topic.name}\n"
            response += f"\nWould you like me to suggest some specific {subject.display_name} practice questions?"
        else:
            response = f"Great to see you exploring {subject.display_name}! "
            if strong_areas and any(topic.subject == subject for topic in strong_areas):
                response += f"You've been doing really well in this subject. "
            response += f"Key areas in {subject.display_name} include:\n\n"
            for topic in subject_topics:
                response += f"• {topic.name}\n"
            response += f"\nWhat specific aspect interests you most?"
        
        return response
    
    def generate_help_response(self, weak_areas):
        """Generate response when student indicates they're struggling"""
        if weak_areas:
            topic = weak_areas[0]  # Focus on weakest area
            response = f"I understand you're finding things challenging. Based on your recent work, "
            response += f"let's focus on {topic.name} in {topic.subject.display_name}.\n\n"
            response += f"Here's my recommended approach:\n"
            response += f"1. Review the basic concepts\n"
            response += f"2. Try some foundation-level questions\n"
            response += f"3. Build up to more complex problems\n\n"
            response += f"Remember, everyone learns at their own pace. You've got this!"
        else:
            response = "I can see you're looking for help! What specific topic or concept would you like to work on? "
            response += "I'm here to guide you through any STEM subject step by step."
        
        return response
    
    def generate_question_response(self, message, analysis):
        """Generate response for questions"""
        if analysis['subject']:
            subject = analysis['subject']
            response = f"That's a great {subject.display_name} question! "
            response += f"Questions like this show you're thinking critically about the material. "
            response += f"Let me help you work through this step by step..."
        else:
            response = "Excellent question! Asking questions is the key to deep learning. "
            response += "Can you tell me which subject area this relates to so I can give you the most helpful guidance?"
        
        return response
    
    def generate_general_encouragement(self, strong_areas, weak_areas):
        """Generate general encouraging response"""
        if strong_areas:
            strong_subject = strong_areas[0].subject.display_name
            response = f"You're making solid progress! I've noticed you're particularly strong in {strong_subject}. "
        else:
            response = "Great to see your enthusiasm for learning! "
        
        if weak_areas:
            weak_topic = weak_areas[0]
            response += f"To boost your overall performance, consider spending some extra time on {weak_topic.name}. "
        
        response += "What would you like to explore today?"
        return response


def _message_indicates_stuck(message):
    """Return True if the message suggests the student is stuck on a question."""
    m = (message or "").lower().strip()
    stuck_phrases = [
        "stuck", "don't know", "dont know", "can't", "cant", "help me",
        "no idea", "confused", "lost", "unclear", "what do i do",
        "how do i", "where do i start", "i'm stuck", "im stuck",
    ]
    return any(p in m for p in stuck_phrases)


def generate_tutor_response(student_id, message, topic_id=None, question_id=None, student_answers=None):
    """LLM-backed tutor response with fallback to legacy personalized tutor."""
    context_parts = []
    try:
        student = User.objects.get(id=student_id)
    except User.DoesNotExist:
        student = None

    if student is not None:
        weak = StudentTopicPerformance.objects.filter(
            student=student,
            questions_attempted__gte=3,
        ).order_by("questions_correct")[:3]
        weak_topics = [w.topic.name for w in weak]
        if weak_topics:
            context_parts.append("Weak topics: " + ", ".join(weak_topics))

    if topic_id:
        try:
            topic = Topic.objects.select_related("subject").get(id=topic_id, is_active=True)
            context_parts.append(f"Current topic: {topic.name} ({topic.subject.display_name})")
        except Topic.DoesNotExist:
            pass

    # When student is stuck and provides question context, run step-level diagnostic
    if question_id and _message_indicates_stuck(message):
        try:
            from learning.services.llm_diagnostic import diagnose_stuck_step
            diag = diagnose_stuck_step(
                question_id=int(question_id),
                student_answers=student_answers or [],
                student_said_stuck=True,
            )
            parts = []
            if diag.get("stuck_at_step"):
                parts.append(f"Student is stuck at step {diag['stuck_at_step']}.")
            if diag.get("reason"):
                parts.append(f"Reason: {diag['reason']}")
            if diag.get("skill_code"):
                parts.append(f"Skill: {diag['skill_code']}")
            if diag.get("recommendation"):
                parts.append(f"Recommendation: {diag['recommendation']}")
            if parts:
                context_parts.append("Step-level diagnosis: " + " ".join(parts))
        except Exception:
            pass

    context = " | ".join(context_parts) if context_parts else "No extra context."
    prompt = (
        f"You are a GCSE tutor. Student asks: {message}\n"
        f"Context: {context}\n"
        "Respond concisely with practical learning guidance."
    )

    use_llm = bool(getattr(settings, "LLM_USE_TUTOR", True))
    if use_llm:
        try:
            from learning.services.llm_service import generate as llm_generate

            return llm_generate(prompt=prompt, max_tokens=400, temperature=0.3)
        except Exception:
            pass

    return PersonalizedAITutor(student_id=student_id).generate_response(message)


def generate_wrong_answer_explanation(question_id, student_answer, correct_answer, skill_code):
    """
    Generate a structured explanation for a wrong answer using the LLM.
    Result is cached on the Question row so the same question never hits the LLM twice.
    Falls back to Question.explanation on LLM failure.
    """
    question = None
    fallback = ""
    try:
        question = Question.objects.select_related("lesson__topic__subject").get(id=question_id)
        fallback = question.explanation or ""
    except Question.DoesNotExist:
        pass

    # Return cached explanation if present
    if question and question.llm_explanation_cache:
        logger.debug("LLM explanation cache hit for question %s", question_id)
        return question.llm_explanation_cache

    prompt = _build_wrong_answer_prompt(
        question=question,
        student_answer=student_answer or "",
        correct_answer=correct_answer or "",
        skill_code=skill_code or "",
    )

    use_llm = bool(getattr(settings, "LLM_USE_TUTOR", True))
    if use_llm:
        try:
            from learning.services.llm_service import generate as llm_generate
            explanation = llm_generate(prompt=prompt, max_tokens=600, temperature=0.3)
            if question and explanation:
                question.llm_explanation_cache = explanation
                question.llm_explanation_cached_at = timezone.now()
                question.save(update_fields=["llm_explanation_cache", "llm_explanation_cached_at"])
                logger.info("Cached LLM explanation for question %s", question_id)
            return explanation
        except Exception:
            logger.warning("LLM explanation generation failed for question %s", question_id, exc_info=True)

    return fallback


def _build_wrong_answer_prompt(question, student_answer, correct_answer, skill_code):
    """Build the LLM prompt for wrong-answer explanation."""
    q_text = question.question_text if question else "[Question text not available]"
    subject = ""
    if question and question.lesson and question.lesson.topic and question.lesson.topic.subject:
        subject = question.lesson.topic.subject.display_name
    if not subject:
        subject = "GCSE"

    parts = [
        f"You are a GCSE tutor. A student answered a question incorrectly. Provide a structured explanation.",
        "",
        f"**Question:** {q_text}",
        f"**Student's answer:** {student_answer}",
        f"**Correct answer:** {correct_answer}",
    ]
    if skill_code:
        parts.append(f"**Skill/topic:** {skill_code}")
    parts.extend([
        "",
        "Your response MUST:",
        "1. Explain why the student's answer is incorrect.",
        "2. Break down the correct reasoning step-by-step.",
        "3. Identify the likely misconception the student has.",
        "4. Use GCSE-level terminology appropriate for " + subject + ".",
        "5. Stay focused on this question only; do not add unrelated information.",
        "",
        "Provide the explanation in clear paragraphs. Be concise and helpful.",
    ])
    return "\n".join(parts)