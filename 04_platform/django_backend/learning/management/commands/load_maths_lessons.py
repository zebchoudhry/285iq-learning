from django.core.management.base import BaseCommand
from learning.models import Topic, Lesson

class Command(BaseCommand):
    help = 'Load all GCSE Mathematics lessons from Cognito structure'

    def handle(self, *args, **options):
        self.stdout.write('Loading GCSE Mathematics structure...')
        
        # Import Subject model
        from learning.models import Subject
        
        # Create or get Mathematics subject
        math_subject, created = Subject.objects.get_or_create(
            exam_board=None,
            name='Mathematics',
            tier='higher',
            defaults={
                'display_name': 'GCSE Mathematics (Higher Tier)',
                'description': 'GCSE Mathematics - covering Number, Algebra, Geometry, Statistics and more',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Created Mathematics subject'))
        else:
            self.stdout.write('[OK] Mathematics subject already exists')
        
        # Create topics
        topics_data = [
            ('Numbers', 'Number operations, fractions, decimals, percentages, standard form', 1),
            ('Algebra', 'Equations, expressions, sequences, factorising, quadratics', 2),
            ('Graphs', 'Linear graphs, quadratic graphs, real-life graphs', 3),
            ('Ratio, Proportion & Rates of Changes', 'Ratios, proportions, percentages, interest', 4),
            ('Geometry & Measures', 'Shapes, area, volume, angles, transformations', 5),
            ('Pythagoras & Trigonometry', 'Pythagoras theorem, SOH CAH TOA, vectors', 6),
            ('Probability & Statistics', 'Probability, averages, data handling, charts', 7),
        ]
        
        topics = {}
        for name, description, order in topics_data:
            topic, created = Topic.objects.get_or_create(
                subject=math_subject,
                name=name,
                defaults={
                    'description': description,
                    'order': order
                }
            )
            topics[name] = topic
            if created:
                self.stdout.write(self.style.SUCCESS(f'[OK] Created topic: {name}'))
            else:
                self.stdout.write(f'[OK] Topic already exists: {name}')
        
        # Now get the topics
        topic_numbers = topics['Numbers']
        topic_algebra = topics['Algebra']
        topic_graphs = topics['Graphs']
        topic_ratio = topics['Ratio, Proportion & Rates of Changes']
        topic_geometry = topics['Geometry & Measures']
        topic_pythagoras = topics['Pythagoras & Trigonometry']
        topic_probability = topics['Probability & Statistics']
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Creating lessons...')
        self.stdout.write('='*60 + '\n')

        # Topic 1 - Numbers (25 lessons)
        numbers_lessons = [
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
            "Adding & Subtracting Standard Form"
        ]

        # Topic 2 - Algebra (48 lessons)
        algebra_lessons = [
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
            "Algebraic Equations (1 Operation & 1 Subject)",
            "Algebraic Equations (2 Operations & 1 Subject)",
            "Algebraic Equations (2 Subjects)",
            "Expressions & Equations",
            "What Formulas are",
            "Rearranging Formulas (Subject Appears Once)",
            "Rearranging Formulas (Subject Appears Twice)",
            "Factorising Quadratic Equations (a = 1)",
            "Factorising Quadratic Equations (a > 1)",
            "The Quadratic Formula",
            "Completing the Square (a = 1)",
            "Solving by Completing the Square (a = 1)",
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
            "Solving Simultaneous Equations 1 - Using Elimination",
            "Solving Simultaneous Equations 2 - Elimination with Scaling",
            "Solving Simultaneous Equations 3 - Substitution Method",
            "Simultaneous Equations - Quadratic & Linear",
            "Proving Algebraic Identities",
            "Introduction to Functions",
            "Evaluating & Combining Functions",
            "Inverse Functions"
        ]

        # Topic 3 - Graphs (19 lessons)
        graphs_lessons = [
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
            "Velocity-time Graphs"
        ]

        # Topic 4 - Ratio, Proportion & Rates of Changes (17 lessons)
        ratio_lessons = [
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
            "Simple Interest"
        ]

        # Topic 5 - Geometry & Measures (30 lessons)
        geometry_lessons = [
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
            "Maps & Scale Drawings"
        ]

        # Topic 6 - Pythagoras & Trigonometry (8 lessons)
        pythagoras_lessons = [
            "Introduction to Trigonometry",
            "Pythagoras' Theorem",
            "SOH CAH TOA - Sin, Cos & Tan",
            "Sine & Cosine Rules",
            "Area of a Triangle",
            "Vector Basics - Theory, Adding & Multiplying",
            "Vectors - Finding Unknown Lengths",
            "Vectors - Parallel, Same Line & Ratios"
        ]

        # Topic 7 - Probability & Statistics (19 lessons)
        probability_lessons = [
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
            "Line Graphs"
        ]

        # Create lessons
        lessons_data = [
            (topic_numbers, numbers_lessons, "1"),
            (topic_algebra, algebra_lessons, "2"),
            (topic_graphs, graphs_lessons, "3"),
            (topic_ratio, ratio_lessons, "4"),
            (topic_geometry, geometry_lessons, "5"),
            (topic_pythagoras, pythagoras_lessons, "6"),
            (topic_probability, probability_lessons, "7")
        ]

        total_created = 0
        for topic, lessons, topic_num in lessons_data:
            for i, lesson_title in enumerate(lessons, 1):
                lesson, created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=f"{topic_num}.{i} - {lesson_title}",
                    defaults={
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Mathematics concepts.',
                        'lesson_type': 'theory',
                        'difficulty_level': 2,
                        'estimated_duration': 30,
                        'key_skills': [lesson_title.lower()],
                        'order': i,
                        'is_active': True
                    }
                )
                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created: {lesson.title}'))
                else:
                    self.stdout.write(f'Already exists: {lesson.title}')

        self.stdout.write(self.style.SUCCESS(f'\nCompleted! Created {total_created} new lessons.'))
        self.stdout.write(self.style.SUCCESS(f'Total GCSE Maths lessons: {Lesson.objects.filter(topic__subject__name="Mathematics").count()}'))