# learning_flow_structure.py
# 285IQ - Complete Learning Flow Architecture
# This shows how your student journey will work technically

from datetime import datetime, timedelta
import json

class LearningFlowManager:
    """Manages the complete student learning journey"""
    
    def __init__(self):
        self.session_data = {
            "student_id": None,
            "current_subject": None,
            "current_topic": None,
            "session_start": None,
            "activities_completed": [],
            "xp_earned": 0,
            "questions_attempted": 0,
            "questions_correct": 0
        }
    
    def start_learning_session(self, student_id, subject, topic):
        """Initialize a new learning session"""
        self.session_data = {
            "student_id": student_id,
            "current_subject": subject,
            "current_topic": topic,
            "session_start": datetime.now(),
            "activities_completed": [],
            "xp_earned": 0,
            "questions_attempted": 0,
            "questions_correct": 0
        }
        
        print(f"🎯 Starting {subject} session: {topic}")
        return self.get_topic_overview()
    
    def get_topic_overview(self):
        """Show topic overview and learning path"""
        return {
            "topic_info": {
                "title": "Quadratic Equations: The Basketball Story",
                "estimated_time": "15-20 minutes",
                "difficulty": "Higher Tier",
                "prerequisite_check": True
            },
            "learning_path": [
                {"step": 1, "activity": "📺 Watch Video", "duration": "5-7 min", "status": "available"},
                {"step": 2, "activity": "❓ Practice Questions", "duration": "5-10 min", "status": "locked"},
                {"step": 3, "activity": "🃏 Flashcards", "duration": "3-5 min", "status": "locked"},
                {"step": 4, "activity": "📊 Review Progress", "duration": "1-2 min", "status": "locked"}
            ],
            "motivation": "🏀 Learn the secret behind every basketball shot!"
        }
    
    def check_prerequisites(self, topic_id):
        """Check if student is ready for this topic"""
        # This would check their progress on prerequisite topics
        prerequisites = {
            "quadratic_equations": ["linear_equations", "basic_algebra", "factoring"],
            "forces_physics": ["basic_math", "units_measurement"],
            "cell_biology": ["basic_chemistry", "microscopes"]
        }
        
        # Mock check - in real system, query database
        student_completed = ["linear_equations", "basic_algebra"]  # From database
        required = prerequisites.get(topic_id, [])
        missing = [req for req in required if req not in student_completed]
        
        if missing:
            return {
                "ready": False,
                "missing_topics": missing,
                "suggestion": f"Complete {', '.join(missing)} first for best results!"
            }
        else:
            return {"ready": True, "message": "You're all set to learn this topic! 🚀"}
    
    def watch_video_activity(self, video_duration_watched):
        """Track video watching progress"""
        activity = {
            "type": "video",
            "completed_at": datetime.now(),
            "duration_watched": video_duration_watched,
            "xp_earned": 20 if video_duration_watched >= 300 else 10  # Full video = more XP
        }
        
        self.session_data["activities_completed"].append(activity)
        self.session_data["xp_earned"] += activity["xp_earned"]
        
        return {
            "xp_earned": activity["xp_earned"],
            "message": "Great! Video complete! Time for some practice! 🎯",
            "next_activity": "questions",
            "unlocked": ["questions"]
        }
    
    def practice_questions_activity(self):
        """Manage the question practice session"""
        return {
            "session_type": "adaptive_practice",
            "instructions": "Answer as many questions as you like! We'll adapt to your level.",
            "question_flow": {
                "start_level": "easy",
                "progression_rules": {
                    "easy_to_medium": "3 correct in a row",
                    "medium_to_hard": "2 correct in a row", 
                    "hard_to_challenge": "1 correct",
                    "step_down": "2 wrong in a row"
                }
            },
            "encouragement_triggers": {
                "first_correct": "Great start! 🌟",
                "streak_3": "You're on fire! 🔥",
                "streak_5": "Amazing streak! You're getting this! 💪",
                "wrong_after_streak": "No worries! Let's try a different approach.",
                "persistent_wrong": "Let's watch that video section again!"
            }
        }
    
    def submit_question_answer(self, question_id, student_answer, time_spent):
        """Process a single question answer"""
        # This would check against secure database
        question_data = self.get_question_data(question_id)
        is_correct = self.check_answer(question_data, student_answer)
        
        # Calculate XP based on difficulty and performance
        base_xp = question_data["difficulty_xp"]
        time_bonus = max(0, 10 - (time_spent // 30))  # Bonus for quick answers
        total_xp = base_xp + (time_bonus if is_correct else 5)  # Participation XP
        
        # Update session stats
        self.session_data["questions_attempted"] += 1
        if is_correct:
            self.session_data["questions_correct"] += 1
        self.session_data["xp_earned"] += total_xp
        
        # Determine next question difficulty
        accuracy = self.session_data["questions_correct"] / self.session_data["questions_attempted"]
        next_difficulty = self.suggest_next_difficulty(accuracy, is_correct)
        
        return {
            "correct": is_correct,
            "xp_earned": total_xp,
            "explanation": question_data["explanation"] if is_correct else question_data["hint"],
            "encouragement": self.get_encouragement_message(is_correct, accuracy),
            "next_difficulty": next_difficulty,
            "session_stats": {
                "attempted": self.session_data["questions_attempted"],
                "correct": self.session_data["questions_correct"],
                "accuracy": f"{accuracy*100:.0f}%",
                "total_xp": self.session_data["xp_earned"]
            }
        }
    
    def flashcards_activity(self):
        """Manage flashcard practice session"""
        return {
            "card_types": [
                {
                    "type": "definition",
                    "front": "What is a quadratic equation?",
                    "back": "An equation with x² as the highest power, shaped like a U-curve!"
                },
                {
                    "type": "example", 
                    "front": "Factor: x² + 5x + 6",
                    "back": "(x + 2)(x + 3) because 2×3=6 and 2+3=5"
                },
                {
                    "type": "visual",
                    "front": "What shape does y = x² make?",
                    "back": "🏀 A parabola - like a basketball shot!"
                }
            ],
            "study_method": "spaced_repetition",
            "success_criteria": "See each card 3 times correctly",
            "xp_per_card": 5
        }
    
    def complete_session(self):
        """Wrap up the learning session and log to calendar"""
        session_duration = datetime.now() - self.session_data["session_start"]
        
        calendar_entry = {
            "date": datetime.now().date(),
            "subject": self.session_data["current_subject"],
            "topic": self.session_data["current_topic"],
            "activities": [activity["type"] for activity in self.session_data["activities_completed"]],
            "duration_minutes": int(session_duration.total_seconds() / 60),
            "xp_earned": self.session_data["xp_earned"],
            "questions_stats": {
                "attempted": self.session_data["questions_attempted"],
                "correct": self.session_data["questions_correct"],
                "accuracy": self.session_data["questions_correct"] / max(1, self.session_data["questions_attempted"])
            },
            "completion_level": self.calculate_completion_level()
        }
        
        # Schedule review reminder
        review_date = datetime.now().date() + timedelta(days=3)
        reminder = {
            "date": review_date,
            "type": "review_reminder",
            "topic": self.session_data["current_topic"],
            "message": f"🔄 Time to review {self.session_data['current_topic']} for better retention!"
        }
        
        return {
            "session_summary": calendar_entry,
            "achievements_unlocked": self.check_achievements(),
            "review_scheduled": reminder,
            "next_suggestions": self.suggest_next_topics(),
            "celebration": self.get_celebration_message()
        }
    
    def calculate_completion_level(self):
        """Calculate how well the student completed this topic"""
        activities = len(self.session_data["activities_completed"])
        accuracy = self.session_data["questions_correct"] / max(1, self.session_data["questions_attempted"])
        
        if activities >= 3 and accuracy >= 0.8:
            return "mastered"
        elif activities >= 2 and accuracy >= 0.6:
            return "good_progress"
        elif activities >= 1:
            return "started"
        else:
            return "incomplete"
    
    def get_calendar_view(self, student_id, days=7):
        """Generate student's learning calendar"""
        # Mock calendar data - in real system, query database
        calendar_data = []
        
        for i in range(days):
            date = datetime.now().date() - timedelta(days=i)
            
            # Mock some data
            if i < 3:  # Recent activity
                calendar_data.append({
                    "date": date,
                    "activities": [
                        {
                            "subject": "Mathematics",
                            "topic": "Quadratic Equations", 
                            "completion": "mastered",
                            "xp_earned": 85,
                            "time_spent": 18
                        }
                    ],
                    "daily_total_xp": 85,
                    "streak_day": True
                })
            else:
                calendar_data.append({
                    "date": date,
                    "activities": [],
                    "daily_total_xp": 0,
                    "streak_day": False
                })
        
        return {
            "calendar_entries": calendar_data,
            "current_streak": 3,
            "total_topics_completed": 12,
            "average_daily_xp": 75,
            "next_review_reminders": [
                {"date": datetime.now().date() + timedelta(days=1), "topic": "Linear Equations"},
                {"date": datetime.now().date() + timedelta(days=3), "topic": "Quadratic Equations"}
            ]
        }
    
    # Helper methods
    def get_question_data(self, question_id):
        """Get question data from secure database"""
        # Mock data - in real system, query database securely
        return {
            "question": "Solve: x² + 5x + 6 = 0",
            "correct_answer": "x = -2 or x = -3",
            "hint": "Find two numbers that multiply to 6 and add to 5",
            "explanation": "2×3=6 and 2+3=5, so (x+2)(x+3)=0",
            "difficulty_xp": 25
        }
    
    def check_answer(self, question_data, student_answer):
        """Securely check if answer is correct"""
        # Normalize and compare answers
        correct = question_data["correct_answer"].lower().replace(" ", "")
        student = student_answer.lower().replace(" ", "")
        return correct == student
    
    def suggest_next_difficulty(self, accuracy, last_correct):
        """Suggest next question difficulty based on performance"""
        if accuracy >= 0.8 and last_correct:
            return "harder"
        elif accuracy < 0.5 and not last_correct:
            return "easier" 
        else:
            return "same"
    
    def get_encouragement_message(self, is_correct, accuracy):
        """Get encouraging message based on performance"""
        if is_correct and accuracy >= 0.8:
            return "Fantastic! You're really mastering this! 🌟"
        elif is_correct:
            return "Great work! Keep it up! 💪"
        else:
            return "Good try! Learning from mistakes makes you stronger! 🚀"
    
    def check_achievements(self):
        """Check for any achievements unlocked this session"""
        achievements = []
        
        if self.session_data["questions_correct"] >= 5:
            achievements.append({"name": "Quick Learner", "icon": "⚡", "xp": 50})
        
        if self.session_data["xp_earned"] >= 100:
            achievements.append({"name": "XP Hunter", "icon": "💎", "xp": 25})
            
        return achievements
    
    def suggest_next_topics(self):
        """Suggest what to study next"""
        return [
            {"topic": "Graphing Quadratics", "reason": "Build on what you just learned"},
            {"topic": "Simultaneous Equations", "reason": "Similar problem-solving skills"},
            {"topic": "Forces in Physics", "reason": "Cross-subject connection opportunity"}
        ]
    
    def get_celebration_message(self):
        """Get celebration message based on session performance"""
        completion = self.calculate_completion_level()
        
        messages = {
            "mastered": "🎉 AMAZING! You've mastered quadratic equations! You're ready for anything!",
            "good_progress": "🌟 Excellent progress! You're well on your way to mastering this topic!",
            "started": "💪 Great start! Come back anytime to continue learning!",
            "incomplete": "🚀 Every expert was once a beginner! Keep going!"
        }
        
        return messages.get(completion, "Great effort today! 🌟")

# Example usage and testing
def test_learning_flow():
    """Test the complete learning flow"""
    print("🎓 285IQ Learning Flow Test")
    print("=" * 40)
    
    # Initialize learning manager
    flow = LearningFlowManager()
    
    # Start session
    overview = flow.start_learning_session("student123", "Mathematics", "Quadratic Equations")
    print("📚 Topic Overview:")
    print(f"Title: {overview['topic_info']['title']}")
    print(f"Time: {overview['topic_info']['estimated_time']}")
    print(f"Motivation: {overview['motivation']}")
    
    # Simulate video watching
    print("\n🎬 Watching video...")
    video_result = flow.watch_video_activity(350)  # 5 min 50 sec
    print(f"✅ {video_result['message']}")
    print(f"🎯 XP Earned: {video_result['xp_earned']}")
    
    # Simulate question practice
    print("\n❓ Starting question practice...")
    for i in range(3):
        question_result = flow.submit_question_answer(
            question_id=f"q{i+1}",
            student_answer="x = -2 or x = -3" if i < 2 else "wrong answer",
            time_spent=45
        )
        print(f"Question {i+1}: {'✅' if question_result['correct'] else '❌'} (+{question_result['xp_earned']} XP)")
        print(f"   {question_result['encouragement']}")
    
    # Complete session
    print("\n📊 Completing session...")
    summary = flow.complete_session()
    print(f"🎉 {summary['celebration']}")
    print(f"📅 Session logged to calendar")
    print(f"🔄 Review scheduled for {summary['review_scheduled']['date']}")
    
    # Show calendar
    print("\n📅 Your Learning Calendar (Last 7 days):")
    calendar = flow.get_calendar_view("student123")
    for entry in calendar["calendar_entries"][:3]:
        status = "🔥" if entry["streak_day"] else "⭕"
        print(f"{status} {entry['date']}: {entry['daily_total_xp']} XP")
    
    print(f"\n🔥 Current Streak: {calendar['current_streak']} days")
    print("✅ Learning flow test complete!")

if __name__ == "__main__":
    test_learning_flow()