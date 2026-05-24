"""
Seed Chemistry curriculum with all 85 sub-topics (lessons) across 11 topics.
Based on Cognito Learning structure for GCSE Chemistry.

Usage: python manage.py seed_chemistry_subtopics

This command is idempotent and safe to run multiple times.
Handles duplicate topics like "Atomic Structure" vs "Atomic Structure & the Periodic Table".
"""
from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson


class Command(BaseCommand):
    help = 'Seed GCSE Chemistry with complete 85-lesson curriculum structure'
    
    # Complete curriculum: 11 topics, 85 lessons
    CHEMISTRY_CURRICULUM = [
        (1, "Atomic Structure & the Periodic Table", "Atoms, elements, periodic table, electronic structure", [
            "Atoms",
            "Elements, Isotopes & Relative Atomic Mass",
            "Compounds, Molecules & Mixtures",
            "Balancing Chemical Equations",
            "Filtration & Crystallisation",
            "Distillation",
            "The History of the Atom",
            "Electronic Structure",
            "Development of the Periodic Table",
            "Metals & Non-metals",
            "Group 1 (Alkali Metals)",
            "Group 7 & Group 0 (Halogens & Noble Gases)",
        ]),
        (2, "Bonding, Structure & Properties of Matter", "Ionic, covalent, metallic bonding, structures, states of matter", [
            "Formation of Ions",
            "Ionic Bonding",
            "Ionic Compounds",
            "Molecular & Empirical Formulas",
            "Covalent Bonding",
            "Types of Covalent Structures",
            "Diamond & Graphite",
            "Graphene & Fullerenes",
            "Metallic Bonding",
            "States of Matter",
            "Nanoparticles",
        ]),
        (3, "Quantitative Chemistry", "Moles, mass, concentration, atom economy, percentage yield", [
            "Relative Formula Mass",
            "Moles & Mass",
            "Calculating Mass in Reactions",
            "Conservation of Mass",
            "Limiting Reactants",
            "Concentration Calculations (grams/dm³)",
            "Gas Calculations",
            "Atom Economy",
            "Percentage Yield",
        ]),
        (4, "Chemical Changes", "Acids, bases, electrolysis, reactivity series, redox reactions", [
            "Acids & Bases",
            "Titration Practical",
            "Strong Acids & Weak Acids",
            "Neutralisation Reactions",
            "The Reactivity Series & Displacement Reactions",
            "Separating Metals from Metal Oxides",
            "Redox Reactions",
            "Electrolysis 1 - Introduction",
            "Electrolysis 2 - Aluminium Oxide",
            "Electrolysis 3 - Aqueous Solutions",
        ]),
        (5, "Energy Changes", "Exothermic, endothermic reactions, bond energies, cells", [
            "Exothermic & Endothermic Reactions",
            "Bond Energies",
            "Cells & Batteries",
            "Fuel Cells",
        ]),
        (6, "The Rate & Extent of Chemical Change", "Rates of reaction, equilibrium, Le Chatelier's Principle", [
            "Rates of Reaction",
            "Factors Affecting Rates of Reaction & Collision Theory",
            "Measuring Rates of Reaction from a Graph",
            "Reversible Reactions & Dynamic Equilibrium",
            "Le Chatelier's Principle",
        ]),
        (7, "Organic Chemistry", "Hydrocarbons, alkanes, alkenes, polymers, alcohols, acids", [
            "Hydrocarbons",
            "Alkanes - Properties & Combustion",
            "Fractional Distillation",
            "Cracking & Alkenes",
            "Reaction of Alkenes",
            "Addition Polymers",
            "Alcohols",
            "Production of Ethanol",
            "Carboxylic Acids",
            "Esters",
            "Condensation Polymers",
            "Naturally Occurring Polymers",
        ]),
        (8, "Chemical Analysis", "Purity, chromatography, tests for ions and gases", [
            "Purity & Formulations",
            "Paper Chromatography",
            "Tests for Gases",
            "Test for Anions",
            "Test for Cations",
            "Flame Emission Spectroscopy",
        ]),
        (9, "Chemistry of the Atmosphere", "Evolution of atmosphere, greenhouse gases, pollution", [
            "The Evolution of the Atmosphere",
            "Greenhouse Gases & Climate Change",
            "Carbon Footprints",
            "Air Pollution",
        ]),
        (10, "Using Resources", "Sustainable development, water treatment, life cycle assessment", [
            "Sustainable Development",
            "Water Treatment & Purification",
            "Life Cycle Assessment",
            "Recycling & Resource Management",
        ]),
        (11, "Practicals", "Required practical experiments for GCSE Chemistry", [
            "Making Salts",
            "Neutralisation",
            "Electrolysis",
            "Temperature Changes",
            "Rates of Reaction",
            "Chromatography",
            "Identifying Ions",
            "Water Purification",
        ]),
    ]
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SEEDING CHEMISTRY CURRICULUM")
        self.stdout.write("=" * 60)
        self.stdout.write("")
        
        # Step 1: Find Chemistry subject
        chemistry_subject = self._find_chemistry_subject()
        if not chemistry_subject:
            return
        
        self.stdout.write(f"Using subject: {chemistry_subject.display_name} (ID: {chemistry_subject.id})")
        self.stdout.write("")
        
        # Step 2: Remove duplicate/overlapping topics
        duplicates_removed = self._deactivate_duplicate_topics(chemistry_subject)
        
        # Step 3: Deactivate old bootstrap lessons
        old_lessons_count = self._deactivate_old_lessons(chemistry_subject)
        
        # Step 4: Create curriculum
        topics_created, lessons_created = self._create_curriculum(chemistry_subject)
        
        # Step 5: Print summary
        self._print_summary(duplicates_removed, old_lessons_count, topics_created, lessons_created, chemistry_subject)
    
    def _find_chemistry_subject(self):
        """Find Chemistry subject (case-insensitive)."""
        candidates = Subject.objects.filter(name__iexact='chemistry') | \
                     Subject.objects.filter(name__icontains='chemistry')
        
        if not candidates.exists():
            self.stdout.write(self.style.ERROR("[ERROR] Chemistry subject not found!"))
            self.stdout.write("Run 'python manage.py bootstrap_gcse' first.")
            return None
        
        # Prefer exact match 'chemistry', then 'Chemistry', then first match
        for candidate in candidates:
            if candidate.name.lower() == 'chemistry':
                return candidate
        
        return candidates.first()
    
    def _deactivate_duplicate_topics(self, subject):
        """
        Deactivate duplicate/overlapping topics.
        E.g., "Atomic Structure" when "Atomic Structure & the Periodic Table" is canonical.
        """
        self.stdout.write("Checking for duplicate/overlapping topics...")
        
        # Canonical topic names from curriculum
        canonical_names = {topic_name for _, topic_name, _, _ in self.CHEMISTRY_CURRICULUM}
        
        # Find all topics for this subject
        all_topics = Topic.objects.filter(subject=subject, is_active=True)
        
        duplicates_deactivated = 0
        
        for topic in all_topics:
            topic_name = topic.name
            
            # Check if this topic name is a subset of any canonical name
            is_duplicate = False
            for canonical in canonical_names:
                if topic_name != canonical and topic_name in canonical:
                    # This is a duplicate/subset (e.g. "Atomic Structure" in "Atomic Structure & the Periodic Table")
                    is_duplicate = True
                    break
            
            if is_duplicate:
                topic.is_active = False
                topic.save(update_fields=['is_active'])
                self.stdout.write(f"  - Deactivated duplicate: {topic_name}")
                duplicates_deactivated += 1
        
        if duplicates_deactivated == 0:
            self.stdout.write("  (No duplicates found)")
        
        self.stdout.write("")
        return duplicates_deactivated
    
    def _deactivate_old_lessons(self, subject):
        """
        Deactivate lessons whose title does NOT match {topic_num}.{lesson_num} - {lesson_title}.
        E.g., "Atomic Structure - Lesson 1" or "Bonding Lesson 2".
        """
        self.stdout.write("Checking for old bootstrap lessons to deactivate...")
        
        # Get all active lessons for Chemistry
        all_lessons = Lesson.objects.filter(topic__subject=subject, is_active=True)
        
        old_lessons_count = 0
        
        for lesson in all_lessons:
            title = lesson.title
            # Expected format: starts with "{digit}.{digit}" (e.g. "1.1 -", "2.10 -")
            import re
            if not re.match(r'^\d+\.\d+\s*-', title):
                # This is an old bootstrap lesson
                lesson.is_active = False
                lesson.save(update_fields=['is_active'])
                self.stdout.write(f"  - Deactivating: {title}")
                old_lessons_count += 1
        
        if old_lessons_count == 0:
            self.stdout.write("  (No old lessons found)")
        
        self.stdout.write("")
        return old_lessons_count
    
    def _create_curriculum(self, subject):
        """Create all topics and lessons from CHEMISTRY_CURRICULUM."""
        self.stdout.write("Creating topics and lessons...")
        self.stdout.write("")
        
        topics_created_count = 0
        lessons_created_count = 0
        
        for topic_num, topic_name, topic_desc, lesson_titles in self.CHEMISTRY_CURRICULUM:
            # Create or get topic
            topic, topic_was_created = Topic.objects.get_or_create(
                subject=subject,
                name=topic_name,
                defaults={
                    'description': topic_desc,
                    'order': topic_num - 1,  # 0-based
                    'is_active': True,
                }
            )
            
            if topic_was_created:
                topics_created_count += 1
                self.stdout.write(f"[+] Created topic: {topic_name}")
            else:
                self.stdout.write(f"[=] Topic exists: {topic_name}")
            
            # Ensure topic is active
            if not topic.is_active:
                topic.is_active = True
                topic.save(update_fields=['is_active'])
            
            # Create lessons
            lessons_created = 0
            for lesson_num, lesson_title in enumerate(lesson_titles, 1):
                full_title = f"{topic_num}.{lesson_num} - {lesson_title}"
                
                lesson, lesson_was_created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=full_title,
                    defaults={
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Chemistry concepts.',
                        'lesson_type': 'theory',
                        'difficulty_level': 2,
                        'estimated_duration': 30,
                        'key_skills': [lesson_title.lower()],
                        'order': lesson_num - 1,  # 0-based
                        'is_active': True,
                    }
                )
                
                if lesson_was_created:
                    lessons_created += 1
            
            if lessons_created > 0:
                self.stdout.write(f"    + Created {len(lesson_titles)} lessons")
            else:
                self.stdout.write(f"    = All {len(lesson_titles)} lessons already exist")
            
            lessons_created_count += lessons_created
            self.stdout.write("")
        
        return topics_created_count, lessons_created_count
    
    def _print_summary(self, duplicates_removed, old_lessons_count, topics_created, lessons_created, subject):
        """Print final summary."""
        self.stdout.write("=" * 60)
        self.stdout.write("SEEDING COMPLETE")
        self.stdout.write("=" * 60)
        self.stdout.write("")
        
        if duplicates_removed > 0:
            self.stdout.write(f"Duplicate topics deactivated: {duplicates_removed}")
        if old_lessons_count > 0:
            self.stdout.write(f"Old lessons deactivated: {old_lessons_count}")
        
        self.stdout.write(f"Topics created:  {topics_created}")
        self.stdout.write(f"Lessons created: {lessons_created}")
        self.stdout.write("")
        
        # Count active topics and lessons
        active_topics = Topic.objects.filter(subject=subject, is_active=True).count()
        active_lessons = Lesson.objects.filter(topic__subject=subject, is_active=True).count()
        
        self.stdout.write(f"Total active topics:  {active_topics}")
        self.stdout.write(f"Total active lessons: {active_lessons}")
        self.stdout.write("")
        
        if active_lessons == 85:
            self.stdout.write("[OK] All 85 lessons in place!")
        else:
            self.stdout.write(f"[WARN] Expected 85 lessons, found {active_lessons}")
        
        self.stdout.write("")
        self.stdout.write("Run 'python manage.py runserver' to see the updated curriculum.")
        self.stdout.write("=" * 60)
