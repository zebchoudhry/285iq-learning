from rest_framework import serializers
from .models import Teacher, Classroom, Assignment, StudentAssignmentProgress


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'school_name', 'subject_specialisms', 'is_verified']


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'name', 'subject', 'class_code', 'created_at']
        read_only_fields = ['class_code', 'created_at']


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'topic', 'due_date', 'is_active']


class StudentAssignmentProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAssignmentProgress
        fields = ['id', 'assignment', 'student', 'completed', 'completed_at']
