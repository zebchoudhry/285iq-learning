from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson

class Command(BaseCommand):
    help = 'Load all GCSE Biology lessons from Cognito structure'

    def handle(self, *args, **options):
        self.stdout.write('Loading GCSE Biology structure...')
        
        # Create or get Biology subject
        biology_subject, created = Subject.objects.get_or_create(
            exam_board=None,
            name='Biology',
            tier='higher',
            defaults={
                'display_name': 'GCSE Biology (Higher Tier)',
                'description': 'GCSE Biology - covering Cell Biology, Organisation, Infection, Bioenergetics and more',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Created Biology subject'))
        else:
            self.stdout.write('[OK] Biology subject already exists')
        
        # Create topics
        topics_data = [
            ('Cell Biology', 'Cell structure, microscopy, mitosis, diffusion, osmosis, active transport', 1),
            ('Organisation', 'Cells, tissues, organs, enzymes, digestive system, circulatory system', 2),
            ('Infection & Response', 'Communicable diseases, immune system, vaccinations, medicines', 3),
            ('Bioenergetics', 'Photosynthesis, respiration, exercise', 4),
            ('Homeostasis & Response', 'Nervous system, hormones, kidneys, reproduction', 5),
            ('Inheritance, Variation & Evolution', 'DNA, genetics, evolution, selective breeding, classification', 6),
            ('Ecology', 'Competition, food chains, carbon cycle, biodiversity, global warming', 7),
            ('Practicals', 'Required practical experiments for GCSE Biology', 8),
        ]
        
        topics = {}
        for name, description, order in topics_data:
            topic, created = Topic.objects.get_or_create(
                subject=biology_subject,
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
        
        # Get topics
        topic_cell = topics['Cell Biology']
        topic_org = topics['Organisation']
        topic_infection = topics['Infection & Response']
        topic_bioener = topics['Bioenergetics']
        topic_homeo = topics['Homeostasis & Response']
        topic_inherit = topics['Inheritance, Variation & Evolution']
        topic_ecology = topics['Ecology']
        topic_practicals = topics['Practicals']
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Creating lessons...')
        self.stdout.write('='*60 + '\n')

        # Topic 1 - Cell Biology (17 lessons)
        cell_biology_lessons = [
            "Cell Structure",
            "Kingdoms of Life",
            "Microscopy 1 - What it is",
            "Microscopy 2 - Light & Electron Microscopy",
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
            "Specialised Exchange Surfaces"
        ]

        # Topic 2 - Organisation (18 lessons)
        organisation_lessons = [
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
            "Transpiration & Translocation"
        ]

        # Topic 3 - Infection & Response (11 lessons)
        infection_lessons = [
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
            "Plant Diseases & Defences"
        ]

        # Topic 4 - Bioenergetics (4 lessons)
        bioenergetics_lessons = [
            "Photosynthesis",
            "Factors that Affect Photosynthesis",
            "Aerobic & Anaerobic Respiration",
            "Exercise"
        ]

        # Topic 5 - Homeostasis & Response (18 lessons)
        homeostasis_lessons = [
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
            "Plant Hormones 2 - Commercial Uses"
        ]

        # Topic 6 - Inheritance, Variation & Evolution (23 lessons)
        inheritance_lessons = [
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
            "Classification"
        ]

        # Topic 7 - Ecology (16 lessons)
        ecology_lessons = [
            "Competition & Interdependence",
            "Abiotic & Biotic Factors",
            "Adaptations",
            "Food Chains & Predator-Prey Cycles",
            "Investigating Abundance & Distribution",
            "Carbon Cycle & Water Cycle",
            "Decay",
            "How Humans Reduce Biodiversity",
            "Maintaining Biodiversity",
            "Global Warming",
            "Deforestation & Land Use",
            "Trophic Levels",
            "Pyramids of Biomass",
            "Fish Farming",
            "Food Security",
            "GMOs & Population Growth"
        ]

        # Topic 8 - Practicals (10 lessons)
        practicals_lessons = [
            "Osmosis",
            "Enzymes & pH",
            "Plant Responses",
            "Decay",
            "Microscopy",
            "Microbiology",
            "Food Tests",
            "Reaction Time",
            "Photosynthesis",
            "Field Investigations"
        ]

        # Create lessons
        lessons_data = [
            (topic_cell, cell_biology_lessons, "1"),
            (topic_org, organisation_lessons, "2"),
            (topic_infection, infection_lessons, "3"),
            (topic_bioener, bioenergetics_lessons, "4"),
            (topic_homeo, homeostasis_lessons, "5"),
            (topic_inherit, inheritance_lessons, "6"),
            (topic_ecology, ecology_lessons, "7"),
            (topic_practicals, practicals_lessons, "8")
        ]

        total_created = 0
        for topic, lessons, topic_num in lessons_data:
            for i, lesson_title in enumerate(lessons, 1):
                lesson, created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=f"{topic_num}.{i} - {lesson_title}",
                    defaults={
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Biology concepts.',
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
        self.stdout.write(self.style.SUCCESS(f'Total GCSE Biology lessons: {Lesson.objects.filter(topic__subject__name="Biology").count()}'))