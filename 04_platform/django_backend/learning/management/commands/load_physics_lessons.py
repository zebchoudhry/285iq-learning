from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson

class Command(BaseCommand):
    help = 'Load all GCSE Physics lessons from Cognito structure'

    def handle(self, *args, **options):
        self.stdout.write('Loading GCSE Physics structure...')
        
        # Create or get Physics subject
        physics_subject, created = Subject.objects.get_or_create(
            exam_board=None,
            name='Physics',
            tier='higher',
            defaults={
                'display_name': 'GCSE Physics (Higher Tier)',
                'description': 'GCSE Physics - covering Energy, Forces, Waves, Electricity, Magnetism and more',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Created Physics subject'))
        else:
            self.stdout.write('[OK] Physics subject already exists')
        
        # Create topics
        topics_data = [
            ('Energy', 'Energy stores, transfers, conservation, efficiency, resources', 1),
            ('Electricity', 'Circuits, current, voltage, resistance, power, static electricity', 2),
            ('Particle Model of Matter', 'States of matter, density, pressure, gas laws', 3),
            ('Atomic Structure', 'Atoms, radioactivity, nuclear fission and fusion', 4),
            ('Forces', 'Motion, vectors, momentum, pressure, moments, Newton\'s laws', 5),
            ('Waves', 'Wave properties, electromagnetic spectrum, sound, light', 6),
            ('Magnetism & Electromagnetism', 'Magnets, motors, generators, transformers', 7),
            ('Space Physics', 'Solar system, life cycle of stars, orbits, red shift', 8),
            ('Practicals', 'Required practical experiments for GCSE Physics', 9),
        ]
        
        topics = {}
        for name, description, order in topics_data:
            topic, created = Topic.objects.get_or_create(
                subject=physics_subject,
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
        topic_energy = topics['Energy']
        topic_electricity = topics['Electricity']
        topic_particle = topics['Particle Model of Matter']
        topic_atomic = topics['Atomic Structure']
        topic_forces = topics['Forces']
        topic_waves = topics['Waves']
        topic_magnetism = topics['Magnetism & Electromagnetism']
        topic_space = topics['Space Physics']
        topic_practicals = topics['Practicals']
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Creating lessons...')
        self.stdout.write('='*60 + '\n')

        # Topic 1 - Energy (17 lessons)
        energy_lessons = [
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
            "Hydroelectricity & Tidal Barrages"
        ]

        # Topic 2 - Electricity (13 lessons)
        electricity_lessons = [
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
            "Electric Fields"
        ]

        # Topic 3 - Particle Model of Matter (5 lessons)
        particle_lessons = [
            "Particle Model & States of Matter",
            "Density",
            "Specific Latent Heat",
            "Factors Affecting Gas Pressure",
            "Pressure & Volume (PV = Constant)"
        ]

        # Topic 4 - Atomic Structure (9 lessons)
        atomic_lessons = [
            "Development of the Model of the Atom",
            "Atomic Structure, Isotopes & Electron Structure",
            "Alpha, Beta & Gamma Radiation",
            "Nuclear Decay Equations",
            "Radioactive Decay & Half-life",
            "Why Radiation is Harmful",
            "Using Radiation in Medicine",
            "Nuclear Fission",
            "Nuclear Fusion"
        ]

        # Topic 5 - Forces (21 lessons)
        forces_lessons = [
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
            "Momentum 2"
        ]

        # Topic 6 - Waves (15 lessons)
        waves_lessons = [
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
            "Seismic Waves"
        ]

        # Topic 7 - Magnetism & Electromagnetism (10 lessons)
        magnetism_lessons = [
            "Magnets",
            "Permanent & Induced Magnets",
            "Electromagnetism",
            "Motor Effect",
            "How the Electric Motor Works",
            "Generator Effect",
            "Alternators, Dynamos & Oscilloscopes",
            "Loudspeakers & Microphones",
            "How Transformers Work",
            "Transformer Calculations"
        ]

        # Topic 8 - Space Physics (4 lessons)
        space_lessons = [
            "Astronomy - Universe, Galaxies & Solar System",
            "Life Cycle of Stars",
            "Orbits",
            "Red Shift"
        ]

        # Topic 9 - Practicals (10 lessons)
        practicals_lessons = [
            "Specific Heat Capacity",
            "Thermal Insulators",
            "Resistance of a Wire",
            "I-V Characteristics",
            "Density",
            "Force & Extension",
            "Acceleration",
            "Waves",
            "Light",
            "Radiation & Absorption"
        ]

        # Create lessons
        lessons_data = [
            (topic_energy, energy_lessons, "1"),
            (topic_electricity, electricity_lessons, "2"),
            (topic_particle, particle_lessons, "3"),
            (topic_atomic, atomic_lessons, "4"),
            (topic_forces, forces_lessons, "5"),
            (topic_waves, waves_lessons, "6"),
            (topic_magnetism, magnetism_lessons, "7"),
            (topic_space, space_lessons, "8"),
            (topic_practicals, practicals_lessons, "9")
        ]

        total_created = 0
        for topic, lessons, topic_num in lessons_data:
            for i, lesson_title in enumerate(lessons, 1):
                lesson, created = Lesson.objects.get_or_create(
                    topic=topic,
                    title=f"{topic_num}.{i} - {lesson_title}",
                    defaults={
                        'content': f'Lesson content for: {lesson_title}. This lesson covers key GCSE Physics concepts.',
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
        self.stdout.write(self.style.SUCCESS(f'Total GCSE Physics lessons: {Lesson.objects.filter(topic__subject__name="Physics").count()}'))