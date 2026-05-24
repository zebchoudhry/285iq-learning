# secure_test.py - Demonstrate secure architecture

class SecureContentManager:
    """Simulates secure server-side content management"""
    
    def __init__(self):
        # This would be in your database, never sent to browser
        self._secure_answers = {
            "q1": "x = -2 or x = -3",
            "q2": "F = 2000N", 
            "q3": "glucose + oxygen"
        }
        
        # This is what students see
        self.public_questions = {
            "q1": {
                "question": "Solve: x² + 5x + 6 = 0",
                "hint": "Look for two numbers that multiply to 6 and add to 5",
                "subject": "mathematics",
                "xp_reward": 25
            },
            "q2": {
                "question": "What force is needed to accelerate a 1000kg car at 2m/s²?",
                "hint": "Use F = ma",
                "subject": "physics", 
                "xp_reward": 20
            }
        }
    
    def get_question(self, question_id):
        """What the student's browser receives (NO ANSWERS!)"""
        if question_id in self.public_questions:
            return self.public_questions[question_id]
        return None
    
    def check_answer(self, question_id, student_answer):
        """Secure server-side answer checking"""
        if question_id not in self._secure_answers:
            return {"error": "Question not found"}
        
        correct_answer = self._secure_answers[question_id].lower().strip()
        student_cleaned = student_answer.lower().strip()
        
        is_correct = correct_answer == student_cleaned
        
        if is_correct:
            return {
                "correct": True,
                "feedback": "🎉 Excellent work! You got it right!",
                "xp_earned": self.public_questions[question_id]["xp_reward"],
                "explanation": "Here's the step-by-step solution..."
            }
        else:
            return {
                "correct": False, 
                "feedback": "Not quite right. " + self.public_questions[question_id]["hint"],
                "xp_earned": 5,  # Participation points
                "explanation": ""  # Only show solution when correct
            }

# Simulate the secure student experience
def simulate_student_experience():
    content_manager = SecureContentManager()
    student_xp = 0
    
    print("🔒 285IQ Secure Learning Demo")
    print("=" * 40)
    print("This shows how students interact with content")
    print("WITHOUT ever seeing the answers!\n")
    
    # Show available questions (like a real platform would)
    print("📚 Available Questions:")
    for q_id, question in content_manager.public_questions.items():
        print(f"{q_id}: {question['question']} ({question['xp_reward']} XP)")
    
    print("\n" + "="*40)
    
    while True:
        question_id = input("\nWhich question? (q1, q2, or 'quit'): ").strip()
        
        if question_id == 'quit':
            break
            
        # Get question (this is what browser receives)
        question_data = content_manager.get_question(question_id)
        
        if not question_data:
            print("Question not found!")
            continue
            
        print(f"\n📝 Question: {question_data['question']}")
        print(f"💡 Hint: {question_data['hint']}")
        print(f"🎯 Reward: {question_data['xp_reward']} XP")
        
        # Student submits answer
        student_answer = input("\nYour answer: ")
        
        # Server checks answer securely
        result = content_manager.check_answer(question_id, student_answer)
        
        print(f"\n{result['feedback']}")
        
        if result['correct']:
            student_xp += result['xp_earned']
            print(f"✨ +{result['xp_earned']} XP! Total: {student_xp} XP")
            print(f"📊 Level: {student_xp // 100}")
        else:
            student_xp += result['xp_earned']
            print(f"🔄 +{result['xp_earned']} XP for trying! Total: {student_xp} XP")
            print("💪 Keep trying - you'll get it!")
    
    print(f"\n🎓 Final Stats: {student_xp} XP, Level {student_xp // 100}")
    print("Thanks for learning with 285IQ! 🚀")

if __name__ == "__main__":
    simulate_student_experience()