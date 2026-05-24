from rest_framework import serializers
from .models import Subject, Topic, Lesson, Question, MultipleChoiceOption, StudentProgress

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'display_name', 'description', 'icon', 'color_code', 'is_active']

class TopicSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.display_name', read_only=True)
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'subject', 'subject_name', 'tier', 'exam_weight', 'order']

class LessonSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.display_name', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'topic', 'topic_name', 'subject_name', 
                 'lesson_type', 'difficulty_level', 'estimated_duration', 'exam_board']

class QuestionSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'difficulty_level', 
                 'marks_available', 'correct_answer', 'explanation', 'lesson', 'lesson_title']