"""
Seed Physics curriculum with all 104 sub-topics (lessons) across 9 topics.
Based on Cognito Learning structure for GCSE Physics.

Usage: python manage.py seed_physics_subtopics

This command is idempotent and safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson


class Command(BaseCommand):
    help = 'Seed GCSE Physics with complete 104-lesson curriculum structure'
    
    # Complete curriculum: 9 topics, 104 lessons
    PHYSICS_CURRICULUM = [
        (1, "Energy", "Energy stores, transfers, conservation, efficiency, resources", [
            "Energy Stores & Systems",
            "Energy Transfer Examples",
            "Kinetic Energy",
            "Gravitational Potential Energy & Gravity",
            "Transfer Between KE & GPE",
            "Specific Heat Capacity",
            "Conservation of Energy",
            "Conduction, Convection & Radiation",
            "Reducing Unwanted Energy Transfers",
            "Power & Work Done",
            "Efficiency",
            "Energy Resources Introduction",
            "Fossil Fuels & Nuclear Energy",
            "Wind & Solar",
            "Geothermal Power",
            "Biofuels",
            "Hydroelectricity & Tidal Barrages",
        ]),
        (2, "Electricity", "Circuits, current, voltage, resistance, power, static electricity", [
            "Circuits Introduction",
            "V = IR Equation & I-V Graphs",
            "Charge, Current & Time",
            "Components",
            "Series Circuits",
            "Parallel Circuits",
            "Energy & Power Formulas",
            "National Grid",
            "AC & DC Current",
            "Plugs & Wires",
            "Fuses & Earthing",
            "Static Electricity",
            "Electric Fields",
        ]),
        (3, "Particle Model of Matter", "States of matter, density, pressure, gas laws", [
            "Particle Model & States of Matter",
            "Density",
            "Specific Latent Heat",
            "Factors Affecting Gas Pressure",
            "Pressure & Volume (PV = Constant)",
        ]),
        (4, "Atomic Structure", "Atoms, radioactivity, nuclear fission and fusion", [
            "Development of the Model of the Atom",
            "Atomic Structure, Isotopes & Electron Structure",
            "Alpha, Beta & Gamma Radiation",
            "Nuclear Decay Equations",
            "Radioactive Decay & Half-life",
            "Why Radiation is Harmful",
            "Using Radiation in Medicine",
            "Nuclear Fission",
            "Nuclear Fusion",
        ]),
        (5, "Forces", "Motion, vectors, momentum, pressure, moments, Newton's laws", [
            "Contact & Non-contact Forces",
            "Scalar & Vector Quantities",
            "Free Body Diagrams & Resultant Forces",
            "Resolving Vectors & Scale Drawings",
            "Elasticity, Spring Constant & Hooke's Law",
            "Elastic Potential Energy",
            "Moments 1",
            "Moments 2",
            "Pressure",
            "Liquid Pressure & Upthrust",
            "Atmospheric Pressure",
            "Speed/Velocity & Distance/Displacement",
            "Acceleration",
            "Distance-time Graphs",
            "Velocity-time Graphs",
            "Terminal Velocity",
            "Newton's 1st & 2nd Laws",
            "Newton's 3rd Law",
            "Stopping Distances",
            "Momentum 1",
            "Momentum 2",
        ]),
        (6, "Waves", "Wave properties, electromagnetic spectrum, sound, light", [
            "Longitudinal & Transverse Waves",
            "Reflection",
            "Refraction",
            "Electromagnetic Waves",
            "Radiowaves",
            "Microwaves & Infrared",
            "UV Light",
            "X-rays & Gamma Rays",
            "How Lenses Work",
            "How to Draw Ray Diagrams",
            "Visible Light & Colour",
            "Absorbing Radiation (Infrared & Black Body)",
            "Sound Waves & Hearing",
            "Ultrasound",
            "Seismic Waves",
        ]),
        (7, "Magnetism & Electromagnetism", "Magnets, motors, generators, transformers", [
            "Magnets",
            "Permanent & Induced Magnets",
            "Electromagnetism",
            "Motor Effect",
            "How the Electric Motor Works",
            "Generator Effect",
            "Alternators, Dynamos & Oscilloscopes",
            "Loudspeakers & Microphones",
            "How Transformers Work",
            "Transformer Calculations",
        ]),
        (8, "Space Physics", "Solar system, life cycle of stars, orbits, red shift", [
            "Astronomy - Universe, Galaxies & Solar System",
            "Life Cycle of Stars",
            "Orbits",
            "Red Shift",
        ]),
        (9, "Practicals", "Required practical experiments for GCSE Physics", [
            "Specific Heat Capacity",
            "Thermal Insulators",
            "Resistance of a Wire",
            "I-V Characteristics",
            "Density",
            "Force & Extension",
            "Acceleration",
            "Waves",
            "Light",
            "Radiation & Absorption",
        ]),
    ]
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("SEEDING PHYSICS CURRICULUM"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        
        # Step 1: Find Physics subject
        physics_subject = self._find_physics_subject()
        if not physics_subject:
            self.stdout.write(self.style.ERROR("No Physics subject found!"))
            self.stdout.write("Run 'python manage.py bootstrap_gcse' first.")
            return
        
        self.stdout.write(f"Using subject: {physics_subject.display_name} (ID: {physics_subject.id})")
        self.stdout.write("")
        
        # Step 2: Deactivate old bootstrap topics and lessons
        self._deactivate_old_topics(physics_subject)
        
        # Step 3: Create topics and lessons
        topics_created, lessons_created = self._create_curriculum(physics_subject)
        
        # Step 4: Summary
        self._print_summary(physics_subject, topics_created, lessons_created)
    
    def _find_physics_subject(self):
        """Find Physics subject (case-insensitive)."""
        subject = Subject.objects.filter(name__iexact='physics').first()
        if subject:
            return subject
        subject = Subject.objects.filter(name='Physics').first()
        return subject
    
    def _deactivate_old_topics(self, physics_subject):
        """Deactivate old bootstrap topics that conflict with new structure."""
        self.stdout.write("Checking for old bootstrap topics to deactivate...")
        
        canonical_topics = {
            'Energy',
            'Electricity',
            'Particle Model of Matter',
            'Atomic Structure',
            'Forces',
            'Waves',
            'Magnetism & Electromagnetism',
            'Space Physics',
            'Practicals',
        }
        
        old_topics = Topic.objects.filter(
            subject=physics_subject,
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
        
        self.stdout.write("Checking for old bootstrap lessons to deactivate...")
        
        deactivated_lessons = 0
        for topic_num, topic_name, _, _ in self.PHYSICS_CURRICULUM:
            try:
                topic = Topic.objects.get(subject=physics_subject, name=topic_name, is_active=True)
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
    
    def _create_curriculum(self, physics_subject):
        """Create all 9 topics and 104 lessons."""
        topics_created = 0
        lessons_created = 0
        
        self.stdout.write("Creating topics and lessons...")
        self.stdout.write("")
        
        for topic_num, topic_name, topic_desc, lesson_titles in self.PHYSICS_CURRICULUM:
            topic, topic_was_created = Topic.objects.get_or_create(
                subject=physics_subject,
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
                if topic.order != topic_num:
                    topic.order = topic_num
                    topic.save(update_fields=['order'])
                self.stdout.write(f"[=] Topic exists: {topic_name}")
            
            for lesson_num, lesson_title in enumerate(lesson_titles, 1):
                full_title = f"{topic_num}.{lesson_num} - {lesson_title}"
                
                lesson, lesson_was_created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=full_title,
                    defaults={
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Physics concepts.',
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
            
            if lessons_created > 0:
                self.stdout.write(f"    + Created {len(lesson_titles)} lessons")
            else:
                self.stdout.write(f"    = All {len(lesson_titles)} lessons already exist")
            
            self.stdout.write("")
        
        return topics_created, lessons_created
    
    def _print_summary(self, physics_subject, topics_created, lessons_created):
        """Print summary statistics."""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("SEEDING COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        
        total_topics = Topic.objects.filter(subject=physics_subject, is_active=True).count()
        total_lessons = Lesson.objects.filter(
            topic__subject=physics_subject,
            topic__is_active=True,
            is_active=True
        ).count()
        
        self.stdout.write(f"Topics created:  {topics_created}")
        self.stdout.write(f"Lessons created: {lessons_created}")
        self.stdout.write("")
        self.stdout.write(f"Total active topics:  {total_topics}")
        self.stdout.write(f"Total active lessons: {total_lessons}")
        self.stdout.write("")
        
        if total_lessons == 104:
            self.stdout.write(self.style.SUCCESS("[OK] All 104 lessons in place!"))
        else:
            self.stdout.write(self.style.WARNING(f"[WARN] Expected 104 lessons, found {total_lessons}"))
        
        self.stdout.write("")
        self.stdout.write("Run 'python manage.py runserver' to see the updated curriculum.")
        self.stdout.write(self.style.SUCCESS("=" * 60))
