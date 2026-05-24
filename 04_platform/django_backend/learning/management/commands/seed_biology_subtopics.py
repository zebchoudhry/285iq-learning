"""
Seed Biology curriculum with all 91 sub-topics (lessons) across 6 topics.
Based on Cognito Learning structure for GCSE Biology.

Usage: python manage.py seed_biology_subtopics

This command is idempotent and safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson


class Command(BaseCommand):
    help = 'Seed GCSE Biology with complete 91-lesson curriculum structure'
    
    # Complete curriculum: 6 topics, 91 lessons
    BIOLOGY_CURRICULUM = [
        (1, "Cell Biology", "Cell structure, microscopy, cell division, transport, stem cells", [
            "Cell Structure",
            "Kingdoms of Life",
            "Microscopy 1 - What it is",
            "Microscopy 2 - Light & Electron Microscopes",
            "Microscopy 3 - Units of Conversion",
            "Microscopy 4 - Calculations",
            "Mitosis",
            "Binary Fission",
            "Culturing Microorganisms (Practical)",
            "Stem Cells",
            "Specialised Cells & Differentiation",
            "Stem Cells in Medicine",
            "Diffusion",
            "Osmosis",
            "Active Transport",
            "Surface Area to Volume Ratio",
            "Specialised Exchange Surfaces",
        ]),
        (2, "Organisation", "Cells, tissues, organs, enzymes, digestion, circulatory system, plants", [
            "Cells, Tissues, Organs & Organ Systems",
            "What are Enzymes",
            "Factors Affecting Enzyme Action",
            "Balanced Diet (Nutrients)",
            "Biological Molecules",
            "Digestive Enzymes",
            "Digestive System",
            "Food Tests (Practical)",
            "Lungs & Gas Exchange",
            "Circulatory System 1 - Heart",
            "Circulatory System 2 - Blood Vessels",
            "Circulatory System 3 - Blood",
            "Cardiovascular Disease",
            "Health & Disease",
            "Risk factors for Non-Communicable Disease",
            "Cancer",
            "Plant Cell Organisation",
            "Transpiration & Translocation",
        ]),
        (3, "Infection & Response", "Communicable diseases, immune system, medicines, plant diseases", [
            "Communicable Disease 1 - Introduction",
            "Communicable Disease 2 - Viruses",
            "Communicable Disease 3 - Bacteria",
            "Communicable Disease 4 - Protists & Fungi",
            "Immune System & Defences",
            "Vaccinations & Immunisation",
            "Drugs & Medicines",
            "Developing New Medicines",
            "Monoclonal Antibodies",
            "Pregnancy Tests",
            "Plant Diseases & Defences",
        ]),
        (4, "Bioenergetics", "Photosynthesis, respiration, exercise", [
            "Photosynthesis",
            "Factors that Affect Photosynthesis",
            "Aerobic & Anaerobic Respiration",
            "Exercise",
        ]),
        (5, "Homeostasis & Response", "Nervous system, hormones, kidneys, reproduction, plant hormones", [
            "Homeostasis",
            "The Nervous System, Synapses & Reflexes",
            "Brain",
            "Eyes 1 - Structure of the Eye & Iris Reflex",
            "Eyes 2 - Accommodation & Visual Defects",
            "Thermoregulation",
            "Endocrine System",
            "Regulating Glucose",
            "Diabetes",
            "Kidneys 1 - Overview & ADH",
            "Kidneys 2 - Anatomy & Nephrons",
            "Kidneys 3 - Dialysis & Transplants",
            "Reproductive Hormones - Puberty & Menstrual Cycle",
            "Contraception",
            "Fertility Treatment",
            "Adrenaline & Thyroxine",
            "Plant Hormones 1 - Auxins",
            "Plant Hormones 2 - Commercial Uses",
        ]),
        (6, "Inheritance, Variation & Evolution", "DNA, genetics, evolution, classification", [
            "DNA 1 - Chromosomes, Genome & Migration",
            "DNA 2 - Key Terms",
            "DNA 3 - Structure & How it Codes",
            "Protein Synthesis",
            "Mutations",
            "Sexual & Asexual Reproduction",
            "Pros & Cons of Sexual & Asexual Reproduction",
            "Meiosis",
            "Genetic Diagrams & Punnet Squares",
            "Family Trees",
            "Inherited Disorders & Embryo Screening",
            "Mendel",
            "Variation & Evolution",
            "Darwin, Wallace & Lamarck",
            "Selective Breeding",
            "Genetic Modification (Genetic Engineering)",
            "Genome Research in Medicine",
            "Cloning Animals",
            "Cloning Plants & Tissue Culture",
            "Fossils & Extinction",
            "Speciation",
            "Antibiotic Resistance",
            "Classification",
        ]),
    ]
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SEEDING BIOLOGY CURRICULUM")
        self.stdout.write("=" * 60)
        self.stdout.write("")
        
        # Step 1: Find Biology subject
        biology_subject = self._find_biology_subject()
        if not biology_subject:
            return
        
        self.stdout.write(f"Using subject: {biology_subject.display_name} (ID: {biology_subject.id})")
        self.stdout.write("")
        
        # Step 2: Remove duplicate/overlapping topics
        duplicates_removed = self._deactivate_duplicate_topics(biology_subject)
        
        # Step 3: Deactivate old bootstrap lessons
        old_lessons_count = self._deactivate_old_lessons(biology_subject)
        
        # Step 4: Create curriculum
        topics_created, lessons_created = self._create_curriculum(biology_subject)
        
        # Step 5: Print summary
        self._print_summary(duplicates_removed, old_lessons_count, topics_created, lessons_created, biology_subject)
    
    def _find_biology_subject(self):
        """Find Biology subject (case-insensitive)."""
        candidates = Subject.objects.filter(name__iexact='biology') | \
                     Subject.objects.filter(name__icontains='biology')
        
        if not candidates.exists():
            self.stdout.write(self.style.ERROR("[ERROR] Biology subject not found!"))
            self.stdout.write("Run 'python manage.py bootstrap_gcse' first.")
            return None
        
        # Prefer exact match 'biology', then 'Biology', then first match
        for candidate in candidates:
            if candidate.name.lower() == 'biology':
                return candidate
        
        return candidates.first()
    
    def _deactivate_duplicate_topics(self, subject):
        """
        Deactivate duplicate/overlapping topics.
        E.g., "Cell" when "Cell Biology" is canonical.
        Also deactivates topics not in the canonical curriculum.
        """
        self.stdout.write("Checking for duplicate/overlapping topics...")
        
        # Canonical topic names from curriculum
        canonical_names = {topic_name for _, topic_name, _, _ in self.BIOLOGY_CURRICULUM}
        
        # Find all topics for this subject
        all_topics = Topic.objects.filter(subject=subject, is_active=True)
        
        duplicates_deactivated = 0
        
        for topic in all_topics:
            topic_name = topic.name
            
            # Check if this topic is NOT in the canonical list
            if topic_name not in canonical_names:
                # Check if it's a subset of any canonical name (e.g., "Cell" vs "Cell Biology")
                is_duplicate = False
                for canonical in canonical_names:
                    if topic_name in canonical:
                        is_duplicate = True
                        break
                
                # Deactivate the topic
                topic.is_active = False
                topic.save(update_fields=['is_active'])
                
                # Also deactivate all lessons in this topic
                lessons_deactivated = Lesson.objects.filter(topic=topic, is_active=True).update(is_active=False)
                
                reason = "duplicate" if is_duplicate else "non-canonical"
                self.stdout.write(f"  - Deactivated {reason}: {topic_name} ({lessons_deactivated} lessons)")
                duplicates_deactivated += 1
        
        if duplicates_deactivated == 0:
            self.stdout.write("  (No duplicates found)")
        
        self.stdout.write("")
        return duplicates_deactivated
    
    def _deactivate_old_lessons(self, subject):
        """
        Deactivate lessons whose title does NOT match {topic_num}.{lesson_num} - {lesson_title}.
        """
        self.stdout.write("Checking for old bootstrap lessons to deactivate...")
        
        # Get all active lessons for Biology
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
        """Create all topics and lessons from BIOLOGY_CURRICULUM."""
        self.stdout.write("Creating topics and lessons...")
        self.stdout.write("")
        
        topics_created_count = 0
        lessons_created_count = 0
        
        for topic_num, topic_name, topic_desc, lesson_titles in self.BIOLOGY_CURRICULUM:
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
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Biology concepts.',
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
        
        if active_lessons == 91:
            self.stdout.write("[OK] All 91 lessons in place!")
        else:
            self.stdout.write(f"[WARN] Expected 91 lessons, found {active_lessons}")
        
        self.stdout.write("")
        self.stdout.write("Run 'python manage.py runserver' to see the updated curriculum.")
        self.stdout.write("=" * 60)
