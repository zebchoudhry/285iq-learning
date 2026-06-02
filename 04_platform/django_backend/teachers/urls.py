from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='teacher-dashboard'),
    path('classrooms/', views.create_classroom, name='create-classroom'),
    path('classrooms/<int:classroom_id>/students/', views.classroom_students, name='classroom-students'),
    path('classrooms/<int:classroom_id>/assign/', views.create_assignment, name='create-assignment'),
    path('classrooms/<int:classroom_id>/at-risk/', views.at_risk_students, name='at-risk-students'),
    path('classrooms/<int:classroom_id>/join/', views.join_classroom, name='join-classroom'),
]
