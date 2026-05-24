# day1_smart_content.py - Smart learning without AI costs!

import random

# Our curated content database (this will grow huge!)
SUBJECT_CONTENT = {
    "mathematics": {
        "quadratic_equations": {
            "keywords": ["quadratic", "x²", "x squared", "parabola", "factoring"],
            "explanation": """
🔢 Quadratic Equations Explained:

A quadratic equation has the form: ax² + bx + c = 0

Think of it like this:
- The x² term makes it curved (like a U-shape)
- You can solve it by: factoring, completing the square, or using the quadratic formula
- Real-world uses: projectile motion, profit optimization, bridge design

Key insight: The graph is always a parabola!
            """,
            "examples": [
                "x² + 5x + 6 = 0  →  (x + 2)(x + 3) = 0  →  x = -2 or x = -3",
                "x² - 4 = 0  →  x² = 4  →  x = ±2"
            ],
            "practice": [
                "Solve: x² + 7x + 12 = 0",
                "Solve: x² - 9 = 0", 
                "Solve: 2x² + 8x + 6 = 0"
            ],
            "connections": ["graphs", "physics_motion", "optimization_problems"]
        },
        "linear_equations": {
            "keywords": ["linear", "straight line", "y = mx + b", "slope"],
            "explanation": """
📈 Linear Equations Explained:

A linear equation creates a straight line: y = mx + b

Breaking it down:
- m = slope (how steep the line is)
- b = y-intercept (where it crosses the y-axis)
- Every increase in x causes a constant increase in y

Think: constant rate of change = straight line!
            """,
            "examples": [
                "y = 2x + 3  →  slope = 2, y-intercept = 3",
                "y = -x + 5  →  slope = -1, y-intercept = 5"
            ],
            "practice": [
                "What's the slope of y = 3x - 2?",
                "Find the equation of a line through (0,4) with slope 2",
                "Graph: y = -2x + 1"
            ],
            "connections": ["coordinate_geometry", "physics_velocity", "economics"]
        }
    },
    "physics": {
        "forces": {
            "keywords": ["force", "newton", "F=ma", "acceleration", "mass"],
            "explanation": """
⚡ Forces Explained:

Newton's Second Law: F = ma (Force = mass × acceleration)

Real-world thinking:
- Heavier objects need more force to accelerate
- Same force on lighter object = more acceleration
- Force and acceleration point in the same direction

Example: Push a shopping cart vs a car with same force!
            """,
            "examples": [
                "Car (1000kg) accelerating at 2m/s²  →  F = 1000 × 2 = 2000N",
                "Ball (0.5kg) with 10N force  →  a = 10 ÷ 0.5 = 20m/s²"
            ],
            "practice": [
                "Calculate force needed to accelerate 500kg at 3m/s²",
                "Find acceleration when 20N acts on 4kg mass",
                "What force stops a 1200kg car in 5 seconds from 10m/s?"
            ],
            "connections": ["energy", "motion_graphs", "engineering"]
        }
    }
}

def find_topic_match(user_input, subject_content):
    """Find the best matching topic based on keywords"""
    user_words = user_input.lower().split()
    best_match = None
    best_score = 0
    
    for topic, content in subject_content.items():
        score = 0
        for keyword in content["keywords"]:
            if keyword.lower() in user_input.lower():
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = topic
            
    return best_match, best_score

def get_smart_response(user_question):
    """Generate intelligent response without AI"""
    
    # Check all subjects for matches
    all_matches = []
    for subject, topics in SUBJECT_CONTENT.items():
        topic_match, score = find_topic_match(user_question, topics)
        if topic_match and score > 0:
            all_matches.append((subject, topic_match, score))
    
    if not all_matches:
        return """
🤔 I didn't find an exact match, but here's what I can help with:

📚 Mathematics: quadratic equations, linear equations, graphs
⚡ Physics: forces, energy, motion  
🧪 Chemistry: atoms, reactions, acids & bases
🧬 Biology: cells, photosynthesis, DNA

Try asking about a specific topic!
        """
    
    # Get the best match
    best_subject, best_topic, _ = max(all_matches, key=lambda x: x[2])
    content = SUBJECT_CONTENT[best_subject][best_topic]
    
    # Build response
    response = f"""
🎯 Great question about {best_topic.replace('_', ' ').title()}!

{content['explanation']}

📝 Examples:
"""
    
    for example in content['examples']:
        response += f"• {example}\n"
    
    response += f"""
🏋️ Practice Questions:
"""
    
    # Show random practice questions
    for question in random.sample(content['practice'], min(2, len(content['practice']))):
        response += f"• {question}\n"
    
    response += f"""
🔗 This connects to: {', '.join(content['connections'])}

🎉 +25 XP for asking a detailed question!
    """
    
    return response

# Test the system
def main():
    print("=== 285IQ Smart Learning System ===")
    print("💡 Ask me about GCSE Maths or Physics!")
    print("Examples: 'help with quadratic equations', 'explain forces', 'what is F=ma'")
    
    total_xp = 0
    
    while True:
        question = input("\n📚 What would you like to learn about? (or 'quit'): ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
            
        if len(question.strip()) < 3:
            print("Try asking a more specific question!")
            continue
            
        response = get_smart_response(question)
        print(response)
        
        # Simulate XP earning
        xp_earned = 25 if len(question) > 20 else 15
        total_xp += xp_earned
        level = total_xp // 100
        
        print(f"\n📊 Your Stats: {total_xp} XP, Level {level}")

if __name__ == "__main__":
    main()