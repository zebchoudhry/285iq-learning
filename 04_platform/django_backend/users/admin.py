from django.contrib import admin
from .models import (
    Student, UserProfile, Achievement, UserAchievement,
    StudentTopicPerformance, School, GCSEResult, PrizePool, PrizeWinner
)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'school_name', 'city', 'grade_level', 'date_joined']
    list_filter = ['school_name', 'city', 'grade_level']
    search_fields = ['username', 'email', 'school_name', 'city']
    readonly_fields = ['parent_access_token', 'parent_dashboard_link']
    
    def parent_dashboard_link(self, obj):
        token = obj.parent_access_token
        url = f"/parent/{token}/"
        return f"{url}"
    parent_dashboard_link.short_description = "Parent Dashboard Link"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['student', 'current_level', 'total_xp', 'daily_streak', 'school_rank']
    list_filter = ['current_level']
    search_fields = ['student__username']

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'total_students', 'total_xp', 'average_score', 'rank_national']
    list_filter = ['city']
    search_fields = ['name', 'city']
    actions = ['update_school_stats']
    
    def update_school_stats(self, request, queryset):
        for school in queryset:
            school.update_stats()
        self.message_user(request, f"Updated stats for {queryset.count()} schools!")

@admin.register(GCSEResult)
class GCSEResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'grade', 'exam_year', 'verified', 'prize_awarded']
    list_filter = ['verified', 'grade', 'subject', 'exam_year', 'prize_awarded']
    search_fields = ['student__username', 'student__school_name']
    actions = ['verify_results', 'mark_prize_eligible']
    
    def verify_results(self, request, queryset):
        queryset.update(verified=True)
        self.message_user(request, f"Verified {queryset.count()} results!")
    
    def mark_prize_eligible(self, request, queryset):
        queryset.update(eligible_for_prize=True)
        self.message_user(request, f"Marked {queryset.count()} results as prize eligible!")

@admin.register(PrizePool)
class PrizePoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'competition_type', 'total_prize_pool', 'start_date', 'end_date', 'is_active']
    list_filter = ['competition_type', 'is_active', 'results_announced']

@admin.register(PrizeWinner)
class PrizeWinnerAdmin(admin.ModelAdmin):
    list_display = ['student', 'prize_pool', 'rank', 'prize_amount', 'payment_status']
    list_filter = ['payment_status', 'prize_pool']
    search_fields = ['student__username']