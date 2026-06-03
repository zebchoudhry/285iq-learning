"""
Seed static flashcards across all GCSE subjects.
Usage: python manage.py seed_flashcards [--dry-run]
"""
from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Flashcard

FLASHCARDS = {
    "mathematics": {
        "Numbers": [
            ("What is a prime number?", "A number greater than 1 with no factors other than 1 and itself. E.g. 2, 3, 5, 7, 11…"),
            ("What is the LCM?", "Lowest Common Multiple — the smallest number that is a multiple of two or more numbers."),
            ("What is the HCF?", "Highest Common Factor — the largest number that divides exactly into two or more numbers."),
            ("How do you convert a fraction to a decimal?", "Divide the numerator by the denominator. E.g. 3/4 = 3 ÷ 4 = 0.75"),
            ("What is standard form?", "A way of writing very large or small numbers: A × 10ⁿ where 1 ≤ A < 10."),
            ("How do you round to significant figures?", "Count digits from the first non-zero digit. Round at the required sig fig, looking at the next digit."),
        ],
        "Algebra": [
            ("What does 'expand' mean in algebra?", "Multiply out the brackets. E.g. 3(x+2) = 3x + 6"),
            ("What does 'factorise' mean?", "Write an expression as a product of its factors. E.g. 6x + 9 = 3(2x + 3)"),
            ("What is the quadratic formula?", "x = (−b ± √(b²−4ac)) / 2a  — used to solve ax² + bx + c = 0"),
            ("What is the nth term of an arithmetic sequence?", "nth term = a + (n−1)d, where a = first term, d = common difference."),
            ("How do you solve simultaneous equations by elimination?", "Add or subtract the equations to eliminate one variable, then solve for the other."),
            ("What is the difference between an expression and an equation?", "An expression has no equals sign (e.g. 3x+2). An equation has an equals sign (e.g. 3x+2=8)."),
        ],
        "Geometry & Measures": [
            ("Area of a circle?", "A = πr²"),
            ("Circumference of a circle?", "C = πd = 2πr"),
            ("Pythagoras' theorem?", "a² + b² = c²  (c is the hypotenuse — the longest side)"),
            ("Area of a triangle?", "A = ½ × base × height"),
            ("What are the angles in a triangle?", "They always add up to 180°."),
            ("Volume of a cuboid?", "V = length × width × height"),
        ],
        "Probability & Statistics": [
            ("What is probability?", "A measure of how likely an event is. P = favourable outcomes ÷ total outcomes. Always between 0 and 1."),
            ("How do you find the mean?", "Add all values together, then divide by how many values there are."),
            ("What is the median?", "The middle value when data is arranged in order."),
            ("What is the mode?", "The value that appears most often in a data set."),
            ("What is the range?", "The difference between the highest and lowest values."),
        ],
    },
    "biology": {
        "Cell Biology": [
            ("What is diffusion?", "The movement of particles from high to low concentration — down a concentration gradient. No energy needed."),
            ("What is osmosis?", "The movement of water molecules from high to low water potential through a partially permeable membrane."),
            ("What is active transport?", "Movement of particles against a concentration gradient — requires energy (ATP)."),
            ("What are the differences between plant and animal cells?", "Plant cells have: cell wall, chloroplasts, large vacuole. Animal cells do not."),
            ("What is mitosis?", "Cell division producing 2 genetically identical daughter cells — for growth and repair."),
            ("What is the function of the nucleus?", "Controls the cell and contains DNA (genetic information)."),
        ],
        "Organisation": [
            ("What do enzymes do?", "Biological catalysts that speed up chemical reactions in the body without being used up."),
            ("What is the optimum temperature for enzymes?", "Around 37°C in humans. Above this they denature — the active site changes shape."),
            ("What is the role of the small intestine?", "Absorbs digested food (nutrients) into the bloodstream. Has villi to increase surface area."),
            ("Name the four chambers of the heart.", "Right atrium, right ventricle, left atrium, left ventricle."),
            ("What does bile do?", "Emulsifies fats — breaks large fat globules into smaller ones to increase surface area for lipase."),
        ],
        "Bioenergetics": [
            ("Equation for photosynthesis?", "Carbon dioxide + water → glucose + oxygen  (light energy required)"),
            ("Equation for aerobic respiration?", "Glucose + oxygen → carbon dioxide + water  (+energy/ATP)"),
            ("Equation for anaerobic respiration (animals)?", "Glucose → lactic acid  (+small amount of energy)"),
            ("What are the three limiting factors of photosynthesis?", "Light intensity, CO₂ concentration, temperature."),
            ("Where does aerobic respiration occur?", "In the mitochondria."),
        ],
        "Infection & Response": [
            ("What is a pathogen?", "A microorganism that causes disease — bacteria, viruses, fungi, or protists."),
            ("How do antibiotics work?", "They kill or inhibit the growth of bacteria. They do NOT work on viruses."),
            ("What are antigens?", "Proteins on the surface of pathogens that trigger an immune response."),
            ("What are antibodies?", "Proteins produced by white blood cells that bind to specific antigens to neutralise pathogens."),
            ("How do vaccines work?", "Introduce dead/weakened pathogens → immune system makes antibodies → memory cells formed for faster future response."),
        ],
        "Homeostasis & Response": [
            ("What is homeostasis?", "Maintaining a stable internal environment (e.g. temperature, blood glucose, water balance)."),
            ("What does insulin do?", "Lowers blood glucose — stimulates cells to absorb glucose and liver to convert it to glycogen."),
            ("What does glucagon do?", "Raises blood glucose — stimulates the liver to convert glycogen back into glucose."),
            ("What is a reflex arc?", "Stimulus → receptor → sensory neuron → relay neuron → motor neuron → effector → response."),
        ],
        "Inheritance, Variation & Evolution": [
            ("What is DNA?", "The molecule that carries genetic information, made of nucleotides arranged in a double helix."),
            ("What is a dominant allele?", "An allele that is always expressed when present — even if only one copy is inherited."),
            ("What is a recessive allele?", "An allele that is only expressed when two copies are present (homozygous recessive)."),
            ("What is natural selection?", "Individuals with advantageous traits survive and reproduce more, passing traits to offspring — driving evolution."),
            ("What is the difference between genotype and phenotype?", "Genotype = genetic makeup (e.g. Aa). Phenotype = physical characteristics shown (e.g. brown eyes)."),
        ],
    },
    "chemistry": {
        "Atomic Structure & the Periodic Table": [
            ("What are the three subatomic particles?", "Proton (+1, in nucleus), neutron (0, in nucleus), electron (−1, orbits nucleus)."),
            ("What is atomic number?", "The number of protons in an atom's nucleus. It defines the element."),
            ("What is mass number?", "The total number of protons + neutrons in the nucleus."),
            ("What are isotopes?", "Atoms of the same element with the same number of protons but different numbers of neutrons."),
            ("Why are noble gases unreactive?", "They have a full outer electron shell — no tendency to gain or lose electrons."),
            ("What are periods on the periodic table?", "Horizontal rows — elements in the same period have the same number of electron shells."),
        ],
        "Bonding, Structure & Properties of Matter": [
            ("What is ionic bonding?", "Transfer of electrons from a metal to a non-metal, forming oppositely charged ions that attract."),
            ("What is covalent bonding?", "Sharing of electrons between non-metal atoms so both achieve a full outer shell."),
            ("What is metallic bonding?", "Positive metal ions in a lattice surrounded by a 'sea' of delocalised electrons."),
            ("Why do ionic compounds have high melting points?", "Strong electrostatic forces between ions in a giant lattice require lots of energy to break."),
            ("Why does diamond have a high melting point?", "Giant covalent structure — each carbon forms 4 strong covalent bonds."),
        ],
        "Quantitative Chemistry": [
            ("Formula for moles?", "moles = mass ÷ Mr  (relative formula mass)"),
            ("What is Mr?", "Relative formula mass — sum of all atomic masses in a compound."),
            ("What is percentage yield?", "% yield = (actual yield ÷ theoretical yield) × 100"),
            ("What is atom economy?", "% atom economy = (mass of desired product ÷ total mass of reactants) × 100"),
        ],
        "Chemical Changes": [
            ("What is oxidation? (electrons)", "Loss of electrons — OIL (Oxidation Is Loss)"),
            ("What is reduction? (electrons)", "Gain of electrons — RIG (Reduction Is Gain). Remember OILRIG."),
            ("What is the reactivity series?", "A list of metals in order of reactivity: K, Na, Ca, Mg, Al, Zn, Fe, Sn, Pb, H, Cu, Ag, Au."),
            ("What is electrolysis?", "Using electricity to decompose a molten or dissolved ionic compound."),
            ("What is neutralisation?", "Acid + base → salt + water"),
        ],
        "Energy Changes": [
            ("What is an exothermic reaction?", "Releases energy to surroundings — temperature rises. E.g. combustion, respiration."),
            ("What is an endothermic reaction?", "Absorbs energy from surroundings — temperature falls. E.g. thermal decomposition."),
            ("What is activation energy?", "The minimum energy needed for a reaction to occur."),
            ("What does a catalyst do?", "Provides an alternative reaction pathway with lower activation energy — speeds up the reaction without being used up."),
        ],
        "The Rate & Extent of Chemical Change": [
            ("Four factors that increase reaction rate?", "Higher temperature, higher concentration, larger surface area, adding a catalyst."),
            ("What is Le Chatelier's Principle?", "If a system at equilibrium is disturbed, it shifts to oppose the change and restore equilibrium."),
            ("Effect of increasing temperature on equilibrium?", "Shifts the equilibrium in the endothermic direction."),
        ],
    },
    "physics": {
        "Energy": [
            ("Conservation of energy?", "Energy cannot be created or destroyed — only transferred from one form to another."),
            ("Formula for kinetic energy?", "KE = ½mv²  (m = mass in kg, v = velocity in m/s, KE in joules)"),
            ("Formula for gravitational potential energy?", "GPE = mgh  (m = mass, g = gravitational field strength, h = height)"),
            ("Formula for efficiency?", "Efficiency = useful output energy ÷ total input energy  (× 100 for %)"),
            ("What is specific heat capacity?", "Energy needed to raise 1 kg of a substance by 1°C. Formula: Q = mcΔT"),
        ],
        "Electricity": [
            ("Ohm's Law?", "V = IR  (Voltage = Current × Resistance)"),
            ("Formula for electrical power?", "P = IV  or  P = I²R  or  P = V²/R"),
            ("Series circuit rules?", "Same current throughout. Voltages add up. Total resistance = sum of all resistances."),
            ("Parallel circuit rules?", "Same voltage across each branch. Currents add up. Total resistance is less than any individual resistor."),
            ("What is AC vs DC?", "DC = direct current (one direction, e.g. batteries). AC = alternating current (reverses direction, e.g. mains at 50 Hz)."),
            ("Why is electricity transmitted at high voltage?", "High V → low I → less energy lost as heat in cables (P = I²R)."),
        ],
        "Forces": [
            ("Newton's Second Law?", "F = ma  (Force = mass × acceleration)"),
            ("What is terminal velocity?", "When drag force equals weight — no net force — object stops accelerating and falls at constant speed."),
            ("What is the resultant force at constant velocity?", "Zero — forces are balanced."),
            ("Formula for momentum?", "p = mv  (momentum = mass × velocity). Unit: kg m/s"),
            ("What is Hooke's Law?", "F = ke  (Force = spring constant × extension). Valid up to the elastic limit."),
        ],
        "Waves": [
            ("Wave equation?", "v = fλ  (wave speed = frequency × wavelength)"),
            ("Transverse vs longitudinal waves?", "Transverse: oscillation perpendicular to direction (e.g. light, water). Longitudinal: oscillation parallel (e.g. sound)."),
            ("What is reflection?", "Wave bounces off a surface — angle of incidence = angle of reflection."),
            ("What is refraction?", "Wave changes speed (and direction) when passing from one medium to another."),
        ],
        "Atomic Structure": [
            ("What is alpha radiation?", "Helium nucleus (2p + 2n). Charge: +2. Stopped by paper or a few cm of air."),
            ("What is beta radiation?", "Fast-moving electron from nucleus. Stopped by a few mm of aluminium."),
            ("What is gamma radiation?", "Electromagnetic wave from nucleus. Stopped by several cm of lead."),
            ("What is half-life?", "Time for half the radioactive nuclei in a sample to decay."),
            ("What is nuclear fission?", "A large nucleus splits into two smaller nuclei, releasing energy and neutrons — used in nuclear reactors."),
        ],
        "Particle Model of Matter": [
            ("What happens to particles when heated?", "They gain kinetic energy — vibrate/move faster. When enough energy is gained, state changes occur."),
            ("Formula for density?", "ρ = m/V  (density = mass ÷ volume). Units: kg/m³ or g/cm³"),
            ("What is specific latent heat?", "Energy needed to change 1 kg of substance from one state to another at constant temperature."),
        ],
    },
    "computer_science": {
        "Systems Architecture": [
            ("What does CPU stand for?", "Central Processing Unit — the brain of the computer that executes instructions."),
            ("What is the fetch-decode-execute cycle?", "Fetch instruction from RAM → Decode it → Execute it. Repeats for every instruction."),
            ("What is cache memory?", "Small, fast memory inside/near the CPU that stores frequently used data for rapid access."),
            ("What is the Von Neumann architecture?", "A computer design where CPU, memory, and I/O share a single bus — instructions and data stored in same memory."),
            ("Three ways to improve CPU performance?", "Increase clock speed, add more cores, increase cache size."),
        ],
        "Memory & Storage": [
            ("RAM vs ROM?", "RAM: volatile, temporary storage for running programs. ROM: non-volatile, stores boot instructions."),
            ("What is secondary storage?", "Permanent storage (HDD, SSD, USB, optical) — retains data when powered off."),
            ("How many values can n bits store?", "2ⁿ values. E.g. 8 bits = 256 values (0–255)."),
            ("Binary to denary: how?", "Multiply each bit by its place value (128,64,32,16,8,4,2,1) and add them up."),
            ("What is a nibble?", "4 bits. A byte = 8 bits. A kilobyte ≈ 1000 bytes."),
        ],
        "Networks": [
            ("LAN vs WAN?", "LAN = Local Area Network (small area, e.g. school). WAN = Wide Area Network (large area, e.g. internet)."),
            ("What does a router do?", "Directs data packets between networks using IP addresses to find the best route."),
            ("What is packet switching?", "Data split into packets, sent independently across a network, reassembled at destination."),
            ("What is a protocol?", "A set of rules that govern how data is transmitted between devices."),
            ("What does HTTP stand for?", "HyperText Transfer Protocol — rules for transferring web pages over the internet."),
        ],
        "Data Representation": [
            ("Why do computers use binary?", "Electronic components have two states: on (1) and off (0) — binary maps directly to this."),
            ("What is ASCII?", "American Standard Code for Information Interchange — assigns a binary number to each character."),
            ("How do you convert denary to binary?", "Repeatedly divide by 2, recording remainders — read remainders bottom to top."),
            ("What is hexadecimal?", "Base-16 number system (0-9 then A-F). Each hex digit = 4 bits (1 nibble)."),
            ("How many colours in 24-bit colour?", "2²⁴ = 16,777,216 colours — 8 bits each for red, green, blue."),
        ],
        "Programming Concepts": [
            ("What is a variable?", "A named storage location in memory that holds a value which can change."),
            ("What is a function?", "A named block of reusable code that returns a value."),
            ("Difference between while and for loop?", "For loop: fixed number of iterations. While loop: repeats while a condition is true."),
            ("What is an array?", "A data structure that stores multiple values of the same type in a single variable."),
            ("What is recursion?", "When a function calls itself — must have a base case to stop infinite recursion."),
        ],
        "Boolean Logic & Logic Gates": [
            ("AND gate truth?", "Output is 1 only if BOTH inputs are 1. Otherwise 0."),
            ("OR gate truth?", "Output is 1 if AT LEAST ONE input is 1."),
            ("NOT gate?", "Inverts the input. NOT 1 = 0, NOT 0 = 1."),
            ("XOR gate?", "Output is 1 if inputs are DIFFERENT. 0,0→0; 0,1→1; 1,0→1; 1,1→0."),
            ("De Morgan's Law?", "NOT(A AND B) = (NOT A) OR (NOT B)  |  NOT(A OR B) = (NOT A) AND (NOT B)"),
        ],
        "Cyber Security": [
            ("What is malware?", "Malicious software — includes viruses, worms, trojans, ransomware, spyware."),
            ("What is phishing?", "Fraudulent emails/messages pretending to be trustworthy to steal sensitive information."),
            ("What is encryption?", "Encoding data so only authorised parties with the decryption key can read it."),
            ("What is a firewall?", "Hardware or software that monitors and controls incoming/outgoing network traffic based on rules."),
            ("What is two-factor authentication?", "Requires two forms of verification (e.g. password + SMS code) to access an account."),
        ],
    },
}


class Command(BaseCommand):
    help = "Seed static flashcards across all GCSE subjects"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview without writing")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = 0
        skipped = 0

        for subject_name, topics in FLASHCARDS.items():
            try:
                subject = Subject.objects.get(name=subject_name)
            except Subject.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Subject not found: {subject_name} — skipping"))
                continue

            for topic_name, cards in topics.items():
                topic = Topic.objects.filter(subject=subject, name=topic_name, is_active=True).first()
                if not topic:
                    self.stdout.write(self.style.WARNING(f"  Topic not found: {topic_name} in {subject_name}"))
                    continue

                for front, back in cards:
                    exists = Flashcard.objects.filter(topic=topic, front=front).exists()
                    if exists:
                        skipped += 1
                        continue
                    if not dry_run:
                        Flashcard.objects.create(topic=topic, front=front, back=back)
                    created += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Done — {created} flashcards {'would be ' if dry_run else ''}created, {skipped} skipped."
        ))
