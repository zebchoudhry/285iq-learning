"""
Serializers for user authentication and profile
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'grade_level')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(student=user)
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'grade_level', 'profile')
        read_only_fields = ('id', 'username')
    
    def get_profile(self, obj):
        """Get user profile data"""
        try:
            profile = obj.profile
            from .models import UserAchievement
            achievements = list(
                UserAchievement.objects.filter(user_profile=profile)
                .select_related('achievement')
                .values_list('achievement__name', 'achievement__icon')
            )
            return {
                'total_xp': profile.total_xp,
                'current_level': profile.current_level,
                'daily_streak': profile.daily_streak,
                'school_rank': profile.school_rank,
                'achievements': [{'name': n, 'icon': i} for n, i in achievements],
                'achievement_count': len(achievements),
            }
        except UserProfile.DoesNotExist:
            return {
                'total_xp': 0,
                'current_level': 1,
                'daily_streak': 0,
                'school_rank': 0,
                'achievements': [],
                'achievement_count': 0,
            }


class LoginSerializer(serializers.Serializer):
    """Serializer for login"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset"""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with token"""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class ExamDateEntrySerializer(serializers.Serializer):
    """One exam date (e.g. Paper 1, Paper 2)."""
    exam_date = serializers.DateField()
    paper_label = serializers.CharField(max_length=50, default='Paper 1')


class OnboardingSubjectSerializer(serializers.Serializer):
    """One subject with target grade and list of exam dates."""
    subject_id = serializers.IntegerField()
    target_grade = serializers.IntegerField(min_value=1, max_value=9, default=5)
    exam_dates = ExamDateEntrySerializer(many=True)

    def validate_exam_dates(self, value):
        if not value:
            raise serializers.ValidationError('At least one exam date is required per subject.')
        return value


class OnboardingExamDatesSerializer(serializers.Serializer):
    """Payload for POST onboarding/exam-dates: list of subjects with exam dates."""
    subjects = OnboardingSubjectSerializer(many=True)

    def validate_subjects(self, value):
        if not value:
            raise serializers.ValidationError('At least one subject with exam dates is required.')
        return value
