"""
Seed Mathematics curriculum with all 166 sub-topics (lessons) across 7 topics.
Based on Cognito Learning structure for GCSE Mathematics.

Usage: python manage.py seed_maths_subtopics

This command is idempotent and safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson


class Command(BaseCommand):
    help = 'Seed GCSE Mathematics with complete 166-lesson curriculum structure'
    
    # Complete curriculum: 7 topics, 166 lessons
    MATHS_CURRICULUM = [
        (1, "Numbers", "Number operations, fractions, decimals, percentages, standard form", [
            "How to use BODMAS",
            "Multiples & Factors",
            "Lowest Common Multiple (LCM)",
            "Highest Common Factor (HCF)",
            "Prime & Composite Numbers",
            "Prime Factor Trees",
            "Fractions - Introduction & how to Simplify",
            "Improper & Mixed Fractions",
            "Multiplying & Dividing Fractions",
            "Adding & Subtracting Fractions",
            "Real Life Applications of Fractions",
            "Introduction to Proportions",
            "Converting Fractions to Decimals",
            "Converting Fractions to Recurring Decimals",
            "Converting Decimals to Percentages",
            "Converting Terminating Decimals to Fractions",
            "Converting Recurring Decimals to Fractions",
            "Rounding Decimals",
            "Rounding to Significant Figures",
            "Estimating",
            "Estimating Square Roots",
            "Introduction to Standard Form",
            "How to Convert Numbers to Standard Form",
            "Multiply & Dividing Standard Form",
            "Adding & Subtracting Standard Form",
        ]),
        (2, "Algebra", "Equations, expressions, sequences, factorising, quadratics", [
            "Collecting Like Terms",
            "Simplifying Algebraic Expressions",
            "Introduction to Powers & Roots",
            "Multiplying & Dividing Powers",
            "Raising Powers",
            "Applying Powers to Fractions",
            "Negative Powers",
            "Fractional Powers",
            "Expanding Single Brackets",
            "Expanding Double Brackets",
            "Expanding Triple Brackets",
            "Factorising Single Brackets",
            "Factorising - the Difference of Two Squares",
            "Surds - Introduction & how to Simplify",
            "Surds - Simplifying Expressions",
            "Surds - Rationalising the Denominator",
            "Algebraic Equations (1 Operation & 1 Unknown)",  # CORRECTED from "Subject"
            "Algebraic Equations (2 Operations & 1 Unknown)",  # CORRECTED from "Subject"
            "Algebraic Equations (2 Subjects)",
            "Expressions & Equations",
            "What Formulas are",
            "Rearranging Formulas (Subject Appears Once)",
            "Rearranging Formulas (Subject Appears Multiple Times)",  # CORRECTED from "Twice"
            "Factorising Quadratic Equations (a = 1)",
            "Factorising Quadratic Equations (a > 1)",
            "The Quadratic Formula",
            "Completing the Square (a = 1)",
            "Solving by Completing the Square (a > 1)",  # CORRECTED from "(a = 1)"
            "Completing the Square (a > 1)",
            "Simplifying Algebraic Fractions",
            "Number Patterns & Sequences (Arithmetic)",
            "Finding The nth Term (Arithmetic Sequence)",
            "Deciding whether a Term is in a Sequence",
            "nth Term of Quadratic Sequence",
            "Introduction to Inequalities",
            "Algebra with Inequalities 1",
            "Algebra with Inequalities 2",
            "Graphical Inequalities",
            "Quadratic Inequalities",
            "Iterative Methods",
            "Solving Simultaneous Equations 1 - Using Substitution",  # CORRECTED from "Elimination"
            "Solving Simultaneous Equations 2 - Elimination",  # CORRECTED from "Elimination with Scaling"
            "Solving Simultaneous Equations 3 - Substitution with Quadratics",  # CORRECTED from "Substitution Method"
            "Simultaneous Equations - Quadratic Graphs",  # CORRECTED from "Quadratic & Linear"
            "Proving Algebraic Identities",
            "Introduction to Functions",
            "Evaluating & Combining Functions",
            "Inverse Functions",
        ]),
        (3, "Graphs", "Linear graphs, quadratic graphs, real-life graphs", [
            "What is 'y = mx + c'",
            "Common Straight Line Equations",
            "Finding the Gradient of a Line on a Graph",
            "Finding the Gradient Using Coordinates",
            "Finding the Equation of a Line from a Graph",
            "Finding the Equation of a Line from 2 Coordinates",
            "Plotting Straight Lines Using a Table of Values",
            "Finding the Midpoint of a Line",
            "Using Ratios to Find a Point Along a Line",
            "Parallel Lines",
            "Perpendicular Lines",
            "What are Quadratic Graphs",
            "How to Plot Quadratic Graphs",
            "Cubic Graphs",
            "Reciprocal Graphs",
            "Graph Transformations",
            "Conversion Graphs",
            "Distance-time Graphs",
            "Velocity-time Graphs",
        ]),
        (4, "Ratio, Proportion & Rates of Changes", "Ratios, proportions, percentages, interest", [
            "Ratios - Introduction & how to Simplify",
            "Simplifying Harder Ratios (Decimals, Mixed Units)",
            "Converting Ratios into Fractions",
            "Scaling Up Ratios",
            "Converting Whole Ratios to Part Ratios",
            "Proportional Division",
            "Scaling Up & Down Using Proportions",
            "Best Buy Questions",
            "What 'Directly Proportional' Means",
            "Algebraic Expressions for Directly Proportional",
            "What 'Inversely Proportional' Means",
            "How to Find a Percentage of a Number",
            "Percentage Increases & Decreases (Multipliers)",
            "Expressing One Number as a Percentage of Another",
            "How to Calculate Percentage Change",
            "Reverse Percentage - Finding Price Before VAT",
            "Simple Interest",
        ]),
        (5, "Geometry & Measures", "Shapes, area, volume, angles, transformations", [
            "Lines of Symmetry",
            "Perimeter",
            "Rotational Symmetry",
            "Types of Regular Polygons",
            "Types of Triangles",
            "Types of Quadrilaterals",
            "Congruent Shapes",
            "Proving Congruence in Triangles (SSS, SAS, ASA, RHS)",
            "Similar Shapes",
            "The Four Transformations",
            "Area Formulas - Rectangle, Parallelogram, Triangle, Trapezium",
            "Areas of Compound Shapes",
            "Area & Perimeter Algebra Problems",
            "Circles - Area & Circumference",
            "Circles - Chord, Segment, Arc & Sector",
            "Circles - Area of Sector & Length of Arc",
            "Eight 3D Shapes you need to Know",
            "2D Projections of 3D Shapes",
            "Volumes of Cubes & Cuboids",
            "Volumes of Spheres & Hemispheres",
            "Volumes of Cylinders & Prisms",
            "Volumes of Cones & Pyramids",
            "Volume of Frustums",
            "Acute, Obtuse & Reflex Angles",
            "5 Simple Angle Rules",
            "Angles Around Parallel & Perpendicular Lines",
            "Interior & Exterior Angles",
            "Circle Geometry - 9 Main Rules",
            "Bearings",
            "Maps & Scale Drawings",
        ]),
        (6, "Pythagoras & Trigonometry", "Pythagoras theorem, SOH CAH TOA, vectors", [
            "Introduction to Trigonometry",
            "Pythagoras' Theorem",
            "SOH CAH TOA - Sin, Cos & Tan",
            "Sine & Cosine Rules",
            "Area of a Triangle",
            "Vector Basics - Theory, Adding & Multiplying",
            "Vectors - Finding Unknown Lengths",
            "Vectors - Parallel, Same Line & Ratios",
        ]),
        (7, "Probability & Statistics", "Probability, averages, data handling, charts", [
            "Probability Basics",
            "Listing Outcomes & Product Rule",
            "Probability Experiments",
            "AND / OR Rules",
            "Tree Diagrams",
            "Conditional Probability",
            "Set Notation & Venn Diagrams",
            "Venn Diagrams",
            "Types of Data",
            "Collecting Data",
            "Averages - Mean, Median, Mode & Range",
            "Frequency Tables & Averages",
            "Grouped Frequency Tables",
            "Box Plots",
            "Cumulative Frequency",
            "Histograms",
            "Scatter Graphs",
            "Pie Charts",
            "Line Graphs",
        ]),
    ]
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("SEEDING MATHEMATICS CURRICULUM"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        
        # Step 1: Find Mathematics subject
        math_subject = self._find_maths_subject()
        if not math_subject:
            self.stdout.write(self.style.ERROR("No Mathematics subject found!"))
            self.stdout.write("Run 'python manage.py bootstrap_gcse' first.")
            return
        
        self.stdout.write(f"Using subject: {math_subject.display_name} (ID: {math_subject.id})")
        self.stdout.write("")
        
        # Step 2: Deactivate old bootstrap topics that conflict
        self._deactivate_old_topics(math_subject)
        
        # Step 3: Create topics and lessons
        topics_created, lessons_created = self._create_curriculum(math_subject)
        
        # Step 4: Summary
        self._print_summary(math_subject, topics_created, lessons_created)
    
    def _find_maths_subject(self):
        """Find Mathematics subject (case-insensitive)."""
        # Try lowercase first (bootstrap convention)
        subject = Subject.objects.filter(name__iexact='mathematics').first()
        if subject:
            return subject
        
        # Fallback to exact 'Mathematics'
        subject = Subject.objects.filter(name='Mathematics').first()
        return subject
    
    def _deactivate_old_topics(self, math_subject):
        """Deactivate old bootstrap topics that conflict with new structure."""
        self.stdout.write("Checking for old bootstrap topics to deactivate...")
        
        # Define the 7 canonical topic names we want to keep
        canonical_topics = {
            'Numbers',
            'Algebra',
            'Graphs',
            'Ratio, Proportion & Rates of Changes',
            'Geometry & Measures',
            'Pythagoras & Trigonometry',
            'Probability & Statistics',
        }
        
        # Deactivate any topic that's not in our canonical list
        old_topics = Topic.objects.filter(
            subject=math_subject,
            is_active=True
        ).exclude(name__in=canonical_topics)
        
        deactivated = 0
        for topic in old_topics:
            topic.is_active = False
            topic.save(update_fields=['is_active'])
            deactivated += 1
            self.stdout.write(f"  - Deactivated old topic: {topic.name}")
        
        if deactivated == 0:
            self.stdout.write("  No old topics to deactivate")
        
        self.stdout.write("")
        
        # Also deactivate old generic lessons (e.g. "Numbers - Lesson 1")
        # AND lessons that don't match numbering pattern (e.g. "Linear Equations" without prefix)
        self.stdout.write("Checking for old bootstrap lessons to deactivate...")
        
        deactivated_lessons = 0
        for topic_num, topic_name, _, _ in self.MATHS_CURRICULUM:
            try:
                topic = Topic.objects.get(subject=math_subject, name=topic_name, is_active=True)
                
                # Find lessons that don't start with proper numbering (e.g. "2.1 - ")
                old_lessons = Lesson.objects.filter(
                    topic=topic,
                    is_active=True
                ).exclude(title__startswith=f"{topic_num}.")
                
                if old_lessons.exists():
                    count = old_lessons.count()
                    for lesson in old_lessons:
                        self.stdout.write(f"  - Deactivating: {lesson.title}")
                    old_lessons.update(is_active=False)
                    deactivated_lessons += count
            except Topic.DoesNotExist:
                pass
        
        if deactivated_lessons == 0:
            self.stdout.write("  No old lessons to deactivate")
        
        self.stdout.write("")
    
    def _create_curriculum(self, math_subject):
        """Create all 7 topics and 166 lessons."""
        topics_created = 0
        lessons_created = 0
        
        self.stdout.write("Creating topics and lessons...")
        self.stdout.write("")
        
        for topic_num, topic_name, topic_desc, lesson_titles in self.MATHS_CURRICULUM:
            # Create or get topic
            topic, topic_was_created = Topic.objects.get_or_create(
                subject=math_subject,
                name=topic_name,
                defaults={
                    'description': topic_desc,
                    'order': topic_num,
                    'is_active': True,
                }
            )
            
            if topic_was_created:
                topics_created += 1
                self.stdout.write(self.style.SUCCESS(f"[+] Created topic: {topic_name}"))
            else:
                # Update order if topic exists
                if topic.order != topic_num:
                    topic.order = topic_num
                    topic.save(update_fields=['order'])
                self.stdout.write(f"[=] Topic exists: {topic_name}")
            
            # Create lessons for this topic
            for lesson_num, lesson_title in enumerate(lesson_titles, 1):
                full_title = f"{topic_num}.{lesson_num} - {lesson_title}"
                
                lesson, lesson_was_created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=full_title,
                    defaults={
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Mathematics concepts.',
                        'lesson_type': 'theory',
                        'difficulty_level': 2,
                        'estimated_duration': 30,
                        'key_skills': [lesson_title.lower()],
                        'order': lesson_num - 1,
                        'is_active': True,
                    }
                )
                
                if lesson_was_created:
                    lessons_created += 1
            
            # Report lessons created for this topic
            if lessons_created > 0:
                self.stdout.write(f"    + Created {len(lesson_titles)} lessons")
            else:
                self.stdout.write(f"    = All {len(lesson_titles)} lessons already exist")
            
            self.stdout.write("")
        
        return topics_created, lessons_created
    
    def _print_summary(self, math_subject, topics_created, lessons_created):
        """Print summary statistics."""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("SEEDING COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        
        # Count totals
        total_topics = Topic.objects.filter(subject=math_subject, is_active=True).count()
        total_lessons = Lesson.objects.filter(
            topic__subject=math_subject,
            topic__is_active=True,
            is_active=True
        ).count()
        
        self.stdout.write(f"Topics created:  {topics_created}")
        self.stdout.write(f"Lessons created: {lessons_created}")
        self.stdout.write("")
        self.stdout.write(f"Total active topics:  {total_topics}")
        self.stdout.write(f"Total active lessons: {total_lessons}")
        self.stdout.write("")
        
        if total_lessons == 166:
            self.stdout.write(self.style.SUCCESS("[OK] All 166 lessons in place!"))
        else:
            self.stdout.write(self.style.WARNING(f"[WARN] Expected 166 lessons, found {total_lessons}"))
        
        self.stdout.write("")
        self.stdout.write("Run 'python manage.py runserver' to see the updated curriculum.")
        self.stdout.write(self.style.SUCCESS("=" * 60))
