from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson

class Command(BaseCommand):
    help = 'Load all GCSE Chemistry lessons from Cognito structure'

    def handle(self, *args, **options):
        self.stdout.write('Loading GCSE Chemistry structure...')
        
        # Create or get Chemistry subject
        chemistry_subject, created = Subject.objects.get_or_create(
            exam_board=None,
            name='Chemistry',
            tier='higher',
            defaults={
                'display_name': 'GCSE Chemistry (Higher Tier)',
                'description': 'GCSE Chemistry - covering Atomic Structure, Bonding, Chemical Changes, Organic Chemistry and more',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Created Chemistry subject'))
        else:
            self.stdout.write('[OK] Chemistry subject already exists')
        
        # Create topics
        topics_data = [
            ('Atomic Structure & the Periodic Table', 'Atoms, elements, periodic table, electronic structure', 1),
            ('Bonding, Structure & Properties of Matter', 'Ionic, covalent, metallic bonding, structures', 2),
            ('Quantitative Chemistry', 'Moles, mass, concentration, atom economy', 3),
            ('Chemical Changes', 'Acids, bases, electrolysis, reactivity series', 4),
            ('Energy Changes', 'Exothermic, endothermic reactions, bond energies', 5),
            ('The Rate & Extent of Chemical Change', 'Rates of reaction, equilibrium, Le Chatelier', 6),
            ('Organic Chemistry', 'Hydrocarbons, alkanes, alkenes, polymers, alcohols', 7),
            ('Chemical Analysis', 'Purity, chromatography, tests for ions and gases', 8),
            ('Chemistry of the Atmosphere', 'Evolution of atmosphere, greenhouse gases, pollution', 9),
            ('Using Resources', 'Sustainable development, water treatment, life cycle assessment', 10),
            ('Practicals', 'Required practical experiments for GCSE Chemistry', 11),
        ]
        
        topics = {}
        for name, description, order in topics_data:
            topic, created = Topic.objects.get_or_create(
                subject=chemistry_subject,
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
        topic_atomic = topics['Atomic Structure & the Periodic Table']
        topic_bonding = topics['Bonding, Structure & Properties of Matter']
        topic_quant = topics['Quantitative Chemistry']
        topic_chemical = topics['Chemical Changes']
        topic_energy = topics['Energy Changes']
        topic_rate = topics['The Rate & Extent of Chemical Change']
        topic_organic = topics['Organic Chemistry']
        topic_analysis = topics['Chemical Analysis']
        topic_atmosphere = topics['Chemistry of the Atmosphere']
        topic_resources = topics['Using Resources']
        topic_practicals = topics['Practicals']
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Creating lessons...')
        self.stdout.write('='*60 + '\n')

        # Topic 1 - Atomic Structure & the Periodic Table (12 lessons)
        atomic_lessons = [
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
            "Group 7 & Group 0 (Halogens & Noble Gases)"
        ]

        # Topic 2 - Bonding, Structure & Properties of Matter (11 lessons)
        bonding_lessons = [
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
            "Nanoparticles"
        ]

        # Topic 3 - Quantitative Chemistry (9 lessons)
        quant_lessons = [
            "Relative Formula Mass",
            "Moles & Mass",
            "Calculating Mass in Reactions",
            "Conservation of Mass",
            "Limiting Reactants",
            "Concentration Calculations (grams/dm³)",
            "Gas Calculations",
            "Atom Economy",
            "Percentage Yield"
        ]

        # Topic 4 - Chemical Changes (10 lessons)
        chemical_lessons = [
            "Acids & Bases",
            "Titration Practical",
            "Strong Acids & Weak Acids",
            "Neutralisation Reactions",
            "The Reactivity Series & Displacement Reactions",
            "Separating Metals from Metal Oxides",
            "Redox Reactions",
            "Electrolysis 1 - Introduction",
            "Electrolysis 2 - Aluminium Oxide",
            "Electrolysis 3 - Aqueous Solutions"
        ]

        # Topic 5 - Energy Changes (4 lessons)
        energy_lessons = [
            "Exothermic & Endothermic Reactions",
            "Bond Energies",
            "Cells & Batteries",
            "Fuel Cells"
        ]

        # Topic 6 - The Rate & Extent of Chemical Change (5 lessons)
        rate_lessons = [
            "Rates of Reaction",
            "Factors Affecting Rates of Reaction & Collision Theory",
            "Measuring Rates of Reaction from a Graph",
            "Reversible Reactions & Dynamic Equilibrium",
            "Le Chatelier's Principle"
        ]

        # Topic 7 - Organic Chemistry (12 lessons)
        organic_lessons = [
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
            "Naturally Occurring Polymers"
        ]

        # Topic 8 - Chemical Analysis (6 lessons)
        analysis_lessons = [
            "Purity & Formulations",
            "Paper Chromatography",
            "Tests for Gases",
            "Test for Anions",
            "Test for Cations",
            "Flame Emission Spectroscopy"
        ]

        # Topic 9 - Chemistry of the Atmosphere (4 lessons)
        atmosphere_lessons = [
            "The Evolution of the Atmosphere",
            "Greenhouse Gases & Climate Change",
            "Carbon Footprints",
            "Air Pollution"
        ]

        # Topic 10 - Using Resources (placeholder - add actual lessons if you have them)
        resources_lessons = [
            "Sustainable Development",
            "Water Treatment & Purification",
            "Life Cycle Assessment",
            "Recycling & Resource Management"
        ]

        # Topic 11 - Practicals (8 lessons)
        practicals_lessons = [
            "Making Salts",
            "Neutralisation",
            "Electrolysis",
            "Temperature Changes",
            "Rates of Reaction",
            "Chromatography",
            "Identifying Ions",
            "Water Purification"
        ]

        # Create lessons
        lessons_data = [
            (topic_atomic, atomic_lessons, "1"),
            (topic_bonding, bonding_lessons, "2"),
            (topic_quant, quant_lessons, "3"),
            (topic_chemical, chemical_lessons, "4"),
            (topic_energy, energy_lessons, "5"),
            (topic_rate, rate_lessons, "6"),
            (topic_organic, organic_lessons, "7"),
            (topic_analysis, analysis_lessons, "8"),
            (topic_atmosphere, atmosphere_lessons, "9"),
            (topic_resources, resources_lessons, "10"),
            (topic_practicals, practicals_lessons, "11")
        ]

        total_created = 0
        for topic, lessons, topic_num in lessons_data:
            for i, lesson_title in enumerate(lessons, 1):
                lesson, created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=f"{topic_num}.{i} - {lesson_title}",
                    defaults={
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Chemistry concepts.',
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
        self.stdout.write(self.style.SUCCESS(f'Total GCSE Chemistry lessons: {Lesson.objects.filter(topic__subject__name="Chemistry").count()}'))