# quadratics_content.py
# 285IQ - Child-Friendly Quadratic Equations Content (FINAL VERSION)
# Universal content that works for ALL exam boards (AQA, Edexcel, OCR)

import json
import random

class QuadraticsContentCreator:
    """Creates amazing child-friendly content for quadratic equations"""
    
    def __init__(self):
        self.topic_info = {
            "id": "math_algebra_quadratic_equations",
            "subject": "mathematics",
            "section": "algebra", 
            "topic_name": "Quadratic Equations",
            "display_title": "Quadratic Equations: The Basketball Story",
            "difficulty_level": 2,  # Higher tier
            "estimated_time_minutes": 20,
            "exam_boards": ["AQA", "Edexcel", "OCR", "WJEC"],
            "prerequisites": ["Linear Equations", "Basic Algebra", "Factoring"]
        }
    
    def create_story_hook(self):
        """Create the engaging story that hooks students"""
        return """
🏀 **Imagine you're the next basketball superstar!**

You're standing at the free-throw line, ball in hand, crowd cheering. As you shoot that perfect shot, something magical happens - the ball traces a beautiful curved path through the air.

UP, UP, UP it goes... then DOWN, DOWN, DOWN into the net! 

That curved path your basketball makes? That's EXACTLY what a quadratic equation looks like when we draw it! Every time you throw a ball, skip a stone, or watch a firework explode, you're seeing quadratic equations in action!

Today, we're going to become quadratic detectives and learn the secret language of curves! 🕵️‍♀️✨
        """
    
    def create_simple_explanation(self):
        """Main explanation using child-friendly language"""
        return """
🎯 **What's a Quadratic Equation? (The Simple Truth!)**

A quadratic equation is just a special math recipe that creates U-shaped curves! It looks like this:

**ax² + bx + c = 0**

Don't panic! Let's break this down like we're following a cooking recipe:

🥄 **The Recipe Ingredients:**
- **'a'** = How wide or narrow your U-shape is (like how curvy your basketball shot is)
- **'b'** = Which direction your curve leans (left or right)
- **'c'** = How high up or down your curve starts (how tall you are when shooting)

🎪 **Think of it Like This:**
- If 'a' is big → Your curve is narrow (like shooting from close up)
- If 'a' is small → Your curve is wide (like shooting from far away)
- The x² part is what makes it curved instead of straight!

**Real-World Magic:**
Every bridge you drive under, every satellite dish you see, every fountain in the park - they all use quadratic curves because they're the strongest and most beautiful shapes in nature! 🌉📡⛲

**The Secret Detective Trick:**
When we "solve" a quadratic equation, we're finding out WHERE the ball lands! It's like being a basketball fortune-teller! 🔮
        """
    
    def create_worked_examples(self):
        """Step-by-step examples with encouraging language"""
        return [
            {
                "title": "🌟 Super Easy Example (Perfect for Beginners!)",
                "problem": "x² - 4 = 0",
                "story_context": "A ball is shot straight up and lands 4 meters away. Where did it cross the ground?",
                "solution_steps": [
                    "🎯 Step 1: Look at our equation: x² - 4 = 0",
                    "🧠 Step 2: Add 4 to both sides: x² = 4", 
                    "💡 Step 3: Think: 'What number times itself equals 4?'",
                    "✨ Step 4: That's 2 × 2 = 4, so x = 2 or x = -2",
                    "🏆 Answer: The ball crosses the ground at 2 meters and -2 meters!"
                ],
                "encouragement": "See how easy that was? You just solved your first quadratic! You're already becoming a math superhero! 🦸‍♀️",
                "memory_trick": "Remember: x² = 4 means 'find the square root!' Like finding the side of a square with area 4!"
            },
            {
                "title": "🚀 The Classic Basketball Shot",
                "problem": "x² + 5x + 6 = 0",
                "story_context": "Jamie shoots a basketball. The equation shows the ball's path. When does it hit the ground?",
                "solution_steps": [
                    "🎯 Step 1: We need two mystery numbers that:",
                    "   • Multiply together to make 6",
                    "   • Add together to make 5",
                    "🕵️ Step 2: Let's be detectives! What two numbers work?",
                    "   • Try 1 and 6: 1×6=6 ✓, but 1+6=7 ✗", 
                    "   • Try 2 and 3: 2×3=6 ✓, and 2+3=5 ✓ Perfect!",
                    "✨ Step 3: So we can write: (x + 2)(x + 3) = 0",
                    "🏆 Step 4: This means x = -2 or x = -3"
                ],
                "encouragement": "Brilliant detective work! You found the secret numbers! This is exactly how mathematicians think - like puzzle solvers! 🧩",
                "memory_trick": "Factor Finder: Look for two numbers that MULTIPLY to the last number and ADD to the middle number!"
            },
            {
                "title": "🎢 The Roller Coaster Challenge",
                "problem": "x² - 6x + 8 = 0",
                "story_context": "A roller coaster car follows this path. Find where it touches the ground!",
                "solution_steps": [
                    "🎯 Step 1: Mystery number hunt! We need two numbers that:",
                    "   • Multiply to make 8",
                    "   • Add to make -6 (notice the minus!)",
                    "🤔 Step 2: Hmm, we need negatives... Let's try:",
                    "   • -2 and -4: (-2)×(-4)=8 ✓, and (-2)+(-4)=-6 ✓",
                    "✨ Step 3: Perfect! So: (x - 2)(x - 4) = 0",
                    "🏆 Step 4: Therefore x = 2 or x = 4"
                ],
                "encouragement": "You conquered the negative numbers! That makes you officially ready for ANY quadratic challenge! 🎢",
                "memory_trick": "Negative hunt: When the middle number is negative, look for two negative factors!"
            }
        ]
    
    def create_practice_questions(self):
        """Practice questions with hints and encouragement"""
        return [
            {
                "level": "beginner",
                "question": "x² - 9 = 0",
                "hint": "What number times itself equals 9? Think of 3 × 3!",
                "answer": "x = 3 or x = -3",
                "encouragement": "Perfect! You're getting the hang of square roots! 🌟",
                "story": "A ball lands 9 meters from where you started. Where did it cross the line?"
            },
            {
                "level": "beginner", 
                "question": "x² - 16 = 0",
                "hint": "This is like x² = 16. What's the square root of 16?",
                "answer": "x = 4 or x = -4", 
                "encouragement": "Excellent! You're becoming a square root detective! 🕵️‍♀️",
                "story": "A basketball bounces and lands 16 units away. Find the crossing points!"
            },
            {
                "level": "intermediate",
                "question": "x² + 7x + 12 = 0",
                "hint": "Find two numbers that multiply to 12 and add to 7. Try 3 and 4!",
                "answer": "x = -3 or x = -4",
                "encouragement": "Amazing! You're mastering the factor-finding technique! 🎯",
                "story": "A rocket follows this path. When does it return to ground level?"
            },
            {
                "level": "intermediate",
                "question": "x² + 8x + 15 = 0", 
                "hint": "Which two numbers multiply to 15 and add to 8? Think 3 and 5!",
                "answer": "x = -3 or x = -5",
                "encouragement": "Brilliant work! You're thinking like a mathematician! 🧠",
                "story": "A fountain's water arc follows this equation. Find where it lands!"
            },
            {
                "level": "challenging",
                "question": "x² - 5x + 6 = 0",
                "hint": "Two numbers that multiply to 6 and add to -5... try -2 and -3!",
                "answer": "x = 2 or x = 3", 
                "encouragement": "Outstanding! You handled negative coefficients like a pro! 🏆",
                "story": "A bridge's arch follows this curve. Find the support points!"
            },
            {
                "level": "challenging",
                "question": "2x² + 7x + 3 = 0",
                "hint": "This one's trickier! Try the quadratic formula: x = (-b ± √(b²-4ac)) / 2a",
                "answer": "x = -3 or x = -1/2",
                "encouragement": "Incredible! You've mastered advanced quadratics! You're ready for anything! 🚀",
                "story": "An advanced satellite orbit follows this path. Calculate the key positions!"
            }
        ]
    
    def create_memory_tricks(self):
        """Fun memory aids and mnemonics"""
        return [
            {
                "concept": "Quadratic Formula",
                "trick": "🎵 'x equals negative b, plus or minus the square root, b squared minus 4ac, all over 2a!' (Sing it like pop goes the weasel!)",
                "visual": "Draw a basketball shooting through a hoop - the formula gives you the exact path!"
            },
            {
                "concept": "Factoring", 
                "trick": "🕵️ Be a Factor Detective: Find two numbers that are 'MULTIPLICATION FRIENDS' and 'ADDITION BUDDIES'",
                "visual": "Two numbers holding hands (adding) while doing a secret handshake (multiplying)!"
            },
            {
                "concept": "Parabola Shape",
                "trick": "🏀 Para-BALL-a: Every parabola looks like a basketball shot!",
                "visual": "Draw a U and put a basketball going through it!"
            },
            {
                "concept": "Discriminant",
                "trick": "🔮 The Crystal Ball: b² - 4ac tells you how many solutions you'll get! Positive = 2, Zero = 1, Negative = 0 real solutions",
                "visual": "A magic crystal ball showing you the future of your equation!"
            }
        ]
    
    def create_real_world_connections(self):
        """Show where quadratics appear in real life"""
        return [
            {
                "category": "Sports",
                "examples": [
                    "🏀 Basketball shots and free throws",
                    "⚽ Soccer ball kicks and goals", 
                    "🏐 Volleyball serves and spikes",
                    "🎾 Tennis ball trajectories",
                    "🥎 Baseball home runs"
                ],
                "explanation": "Any ball thrown through the air follows a quadratic path due to gravity!"
            },
            {
                "category": "Architecture", 
                "examples": [
                    "🌉 Bridge arches (strongest shape!)",
                    "🏛️ Dome roofs and ceilings",
                    "🎪 Circus tent supports",
                    "🏗️ Suspension bridge cables",
                    "🎢 Roller coaster tracks"
                ],
                "explanation": "Quadratic curves distribute weight perfectly - that's why they're used in construction!"
            },
            {
                "category": "Technology",
                "examples": [
                    "📡 Satellite dishes (focus radio waves)",
                    "🔦 Flashlight and headlight reflectors", 
                    "🚗 Car headlight shapes",
                    "📱 Phone antenna designs",
                    "🛰️ Space satellite orbits"
                ],
                "explanation": "Parabolic shapes focus energy perfectly - from light to radio waves to heat!"
            }
        ]
    
    def create_quick_motivation_section(self):
        """Brief motivational context - part of main content"""
        return {
            "title": "🌟 Why This Matters",
            "brief_examples": [
                "🏀 Every sports shot you take",
                "🎮 Every game you play", 
                "📱 Every app animation you see",
                "🌉 Every bridge you cross"
            ],
            "encouragement": "Quadratics aren't just school math - they're the hidden language that makes our world work beautifully!"
        }
    
    def create_optional_career_exploration(self):
        """Optional career section - accessed via 'Learn More' button"""
        return {
            "section_title": "💼 Where Will You Use This? Career Explorer",
            "section_description": "Curious about how quadratics appear in real jobs? Click to explore!",
            "careers": [
                {
                    "career": "🎮 Video Game Designer",
                    "daily_use": "Creating realistic ball physics, jumping animations, and projectile weapons",
                    "real_example": "When Mario jumps in Super Mario Bros, his arc follows a quadratic equation!",
                    "cool_fact": "Every time a character throws something or jumps in a game, programmers use quadratics!"
                },
                {
                    "career": "🏗️ Civil Engineer", 
                    "daily_use": "Designing bridge arches, calculating load distribution, and planning road curves",
                    "real_example": "The Millennium Bridge in London uses quadratic curves to distribute weight perfectly",
                    "cool_fact": "Quadratic arches can hold 50x more weight than straight beams!"
                },
                {
                    "career": "🚀 Aerospace Engineer",
                    "daily_use": "Calculating rocket trajectories, satellite orbits, and spacecraft re-entry paths",
                    "real_example": "SpaceX uses quadratics to land rockets precisely on floating platforms",
                    "cool_fact": "Without quadratics, we couldn't send anything to space accurately!"
                },
                {
                    "career": "🎬 Special Effects Artist",
                    "daily_use": "Creating realistic explosions, water splashes, and flying objects in movies",
                    "real_example": "Every explosion in Marvel movies uses quadratic equations for realistic debris",
                    "cool_fact": "The water in Moana and fire in Frozen 2 all use quadratic mathematics!"
                },
                {
                    "career": "📱 App Developer",
                    "daily_use": "Creating smooth animations, bounce effects, and gesture recognition",
                    "real_example": "The satisfying bounce when you pull down to refresh Instagram? That's quadratics!",
                    "cool_fact": "Every swipe, bounce, and animation on your phone uses quadratic equations!"
                }
            ],
            "daily_life_right_now": [
                {
                    "situation": "📱 Your Phone Apps",
                    "quadratic_use": "Smooth scrolling and bounce-back effects when you reach the end of a page"
                },
                {
                    "situation": "🎮 Video Games",
                    "quadratic_use": "Every jump, throw, and projectile follows quadratic physics"
                },
                {
                    "situation": "🏀 Sports You Play",
                    "quadratic_use": "Every ball you throw, kick, or hit follows a quadratic path"
                },
                {
                    "situation": "🎢 Theme Parks",
                    "quadratic_use": "Roller coaster loops and water slide curves use quadratic safety calculations"
                }
            ],
            "future_tech": [
                {
                    "technology": "🤖 AI & Robotics",
                    "impact": "Robots planning movement paths and catching objects"
                },
                {
                    "technology": "🚗 Self-Driving Cars", 
                    "impact": "Safe turning curves and optimal braking distances"
                },
                {
                    "technology": "🥽 Virtual Reality",
                    "impact": "Realistic physics and smooth motion tracking"
                }
            ]
        }
    
    def create_video_script(self):
        """Complete script for video recording"""
        return """
🎬 VIDEO SCRIPT: "Quadratic Equations - The Basketball Story"
📏 Duration: 5-7 minutes
🎯 Audience: GCSE students (any exam board)

[SCENE 1: Hook - 0:00-0:30]
[You're holding a basketball, standing in front of a whiteboard]

"Hey there, future mathematicians! I'm going to show you something absolutely incredible today. Watch this!"

[Throw basketball in a gentle arc]

"Did you see that beautiful curved path? That, my friends, is a quadratic equation in action! Every single time you throw a ball, shoot a basketball, or even skip a stone - you're creating one of the most important mathematical shapes in the universe!"

[SCENE 2: The Big Reveal - 0:30-1:30]
[Draw a U-shape on the whiteboard]

"This is called a parabola, and it's everywhere! Look around you right now - I guarantee you'll see this shape. Bridge arches, satellite dishes, even the McDonald's golden arches - they're all quadratics!"

[Write: ax² + bx + c = 0]

"Now, this might look scary, but I promise you - by the end of this video, you'll see this equation and think 'basketball shot!' instead of 'impossible math problem.'"

[SCENE 3: Breaking it Down - 1:30-3:00]
[Point to each part of the equation]

"Let's decode this like secret agents:
- This 'a' tells us how narrow or wide our basketball shot is
- This 'b' tells us which direction we're aiming
- This 'c' tells us how tall we are when we shoot

It's literally that simple!"

[SCENE 4: Detective Work - 3:00-4:30]
[Write: x² + 5x + 6 = 0]

"Now comes the fun part - we become math detectives! We need to find two mystery numbers that:
1. Multiply together to make 6
2. Add together to make 5

Let's investigate! Could it be 1 and 6? Let's check:
1 × 6 = 6 ✓ But 1 + 6 = 7 ✗ Nope!

How about 2 and 3?
2 × 3 = 6 ✓ And 2 + 3 = 5 ✓ Perfect!"

[Write: (x + 2)(x + 3) = 0]

"So our basketball lands at x = -2 and x = -3!"

[SCENE 5: Real World Magic - 4:30-5:30]
[Show pictures/props of bridges, fountains, etc.]

"This isn't just classroom math - this is the math that builds our world! Engineers use quadratics to design bridges that won't fall down, architects use them to create beautiful domes, and NASA uses them to send rockets to space!"

[SCENE 6: Wrap-up & Encouragement - 5:30-7:00]
[Back to the basketball]

"So next time you shoot a basketball, remember - you're not just playing a game, you're demonstrating one of the most beautiful mathematical concepts ever discovered!"

[Throw basketball again]

"And remember, every expert was once a beginner. You've got this! Practice these steps, think like a detective, and soon you'll be solving quadratics like a pro!"

[Write on board: "YOU ARE A QUADRATIC DETECTIVE! 🕵️‍♀️"]

"Keep practicing, keep questioning, and I'll see you in the next video where we'll explore even more amazing mathematical adventures!"

[END]

📝 PROPS NEEDED:
- Basketball
- Whiteboard and markers
- Pictures of bridges, arches, satellite dishes
- Calculator (optional)

🎥 EDITING NOTES:
- Add animated parabola graphics when explaining curves
- Include real footage of basketball shots in slow motion
- Add sound effects for 'detective work' sections
- Include inspirational music during real-world examples
        """
    
    def generate_complete_content_package(self):
        """Generate the complete content package for the database"""
        return {
            # CORE LEARNING CONTENT (always visible)
            "topic_info": self.topic_info,
            "story_hook": self.create_story_hook(),
            "explanation": self.create_simple_explanation(),
            "worked_examples": self.create_worked_examples(),
            "practice_questions": self.create_practice_questions(),
            "memory_tricks": self.create_memory_tricks(),
            "real_world_connections": self.create_real_world_connections(),
            "quick_motivation": self.create_quick_motivation_section(),  # Brief context
            "video_script": self.create_video_script(),
            
            # OPTIONAL ENRICHMENT CONTENT (behind "Learn More" button)
            "optional_content": {
                "career_exploration": self.create_optional_career_exploration()
            },
            
            # ASSESSMENT AND STRUCTURE
            "assessment_criteria": {
                "foundation_skills": [
                    "Recognize quadratic equations",
                    "Solve simple quadratics by factoring",
                    "Understand the parabola shape"
                ],
                "higher_skills": [
                    "Use the quadratic formula",
                    "Complete the square",
                    "Interpret real-world quadratic problems"
                ]
            },
            "common_mistakes": [
                {
                    "mistake": "Forgetting the ± in square roots",
                    "correction": "Remember: x² = 4 gives x = +2 OR x = -2",
                    "tip": "Both positive and numbers work!"
                },
                {
                    "mistake": "Wrong signs when factoring",
                    "correction": "Check your factor pairs carefully",
                    "tip": "Use the detective method: multiply first, then add!"
                }
            ]
        }

# Interactive content tester
def test_quadratics_content():
    """Test the content with interactive questions"""
    creator = QuadraticsContentCreator()
    content = creator.generate_complete_content_package()
    
    print("🏀 285IQ - Quadratic Equations Content Test")
    print("=" * 50)
    
    # Show the story hook
    print("\n📖 STORY HOOK:")
    print(content["story_hook"])
    
    # Show one example
    print("\n📝 SAMPLE WORKED EXAMPLE:")
    example = content["worked_examples"][0]
    print(f"✨ {example['title']}")
    print(f"Problem: {example['problem']}")
    print(f"Story: {example['story_context']}")
    for step in example['solution_steps']:
        print(f"  {step}")
    print(f"💪 {example['encouragement']}")
    
    # Show brief motivation (part of core content)
    print("\n🌟 QUICK MOTIVATION:")
    motivation = content["quick_motivation"]
    print(motivation["encouragement"])
    for example in motivation["brief_examples"]:
        print(f"  {example}")
    
    # Interactive practice
    print("\n🎯 PRACTICE TIME!")
    practice_questions = content["practice_questions"]
    
    for i, question in enumerate(practice_questions[:3], 1):
        print(f"\n📚 Question {i} ({question['level'].title()}):")
        print(f"Story: {question['story']}")
        print(f"Solve: {question['question']}")
        
        user_answer = input("Your answer (or 'hint' for help): ").strip()
        
        if user_answer.lower() == 'hint':
            print(f"💡 Hint: {question['hint']}")
            user_answer = input("Now try: ").strip()
        
        print(f"✅ Correct answer: {question['answer']}")
        print(f"🎉 {question['encouragement']}")
        
        continue_quiz = input("\nContinue to next question? (y/n): ").strip().lower()
        if continue_quiz != 'y':
            break
    
    # Show memory tricks
    print("\n🧠 MEMORY TRICKS:")
    for trick in content["memory_tricks"]:
        print(f"🎯 {trick['concept']}: {trick['trick']}")
    
    # Show optional content preview
    print("\n💡 OPTIONAL 'LEARN MORE' CONTENT AVAILABLE:")
    career_content = content["optional_content"]["career_exploration"]
    print(f"📚 {career_content['section_title']}")
    print(f"   {career_content['section_description']}")
    print(f"   Contains: {len(career_content['careers'])} career examples")
    print(f"   Plus: Daily life applications and future tech")
    
    print("\n🎓 Content test complete!")
    print("📍 Core content: Focused on learning")
    print("🔍 Optional content: Available when students want to explore more")
    return content

# Save content to file for database import
def save_content_for_database():
    """Save the content in format ready for database import"""
    creator = QuadraticsContentCreator()
    content = creator.generate_complete_content_package()
    
    # Save as JSON for easy database import
    with open('quadratics_database_content.json', 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    
    print("💾 Content saved to 'quadratics_database_content.json'")
    print("📤 Ready for secure database import!")
    return content

# Main execution
if __name__ == "__main__":
    print("🏀 285IQ Quadratics Content Creator")
    print("🎯 Creating child-friendly content for ALL exam boards")
    print("=" * 60)
    
    choice = input("""
What would you like to do?
1. Test the interactive content
2. Save content for database
3. Show video script
4. Exit

Enter choice (1-4): """).strip()
    
    creator = QuadraticsContentCreator()
    
    if choice == '1':
        test_quadratics_content()
    elif choice == '2':
        save_content_for_database()
    elif choice == '3':
        content = creator.generate_complete_content_package()
        print("\n🎬 VIDEO SCRIPT:")
        print(content["video_script"])
    else:
        print("👋 Thanks for using 285IQ Content Creator!")
        
    print("\n🚀 Ready to create more amazing content!")