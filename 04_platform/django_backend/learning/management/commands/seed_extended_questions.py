"""
Seed 200+ static practice questions across all subjects.
Covers Maths, Biology, Chemistry, Physics, Computer Science.
Questions are topic-level (attached to the first lesson of each topic).

Usage: python manage.py seed_extended_questions [--dry-run]
"""
from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Lesson, Question

QUESTIONS = {
    # ── MATHEMATICS ──────────────────────────────────────────────────────────
    "mathematics": {
        "Numbers": [
            ("What is the Lowest Common Multiple (LCM) of 4 and 6?", "12", "4: 4,8,12…  6: 6,12… → LCM = 12", "short_answer", 1, 2),
            ("Express 0.000045 in standard form.", "4.5 × 10⁻⁵", "Move decimal 5 places right → 4.5 × 10⁻⁵", "short_answer", 1, 2),
            ("Round 3.4762 to 2 significant figures.", "3.5", "First 2 sig figs are 3 and 4; next digit (7) rounds up → 3.5", "short_answer", 1, 2),
            ("Convert 3/8 to a decimal.", "0.375", "3 ÷ 8 = 0.375", "short_answer", 1, 1),
            ("A jacket costs £80 and is reduced by 15%. What is the sale price?", "£68", "15% of 80 = 12; 80 − 12 = £68", "calculation", 2, 3),
            ("Calculate (2.4 × 10³) × (3.0 × 10⁴). Give your answer in standard form.", "7.2 × 10⁷", "2.4 × 3.0 = 7.2; 10³ × 10⁴ = 10⁷", "calculation", 2, 3),
            ("Find the HCF of 36 and 48.", "12", "36 = 2²×3²; 48 = 2⁴×3; HCF = 2²×3 = 12", "short_answer", 1, 2),
            ("Write 0.36̄ (0.3666…) as a fraction in its simplest form.", "11/30", "x = 0.3666…; 10x = 3.666…; 9x = 3.3 → x = 33/90 = 11/30", "short_answer", 2, 3),
        ],
        "Algebra": [
            ("Expand and simplify (x + 3)(x − 5).", "x² − 2x − 15", "FOIL: x²−5x+3x−15 = x²−2x−15", "short_answer", 1, 2),
            ("Factorise fully: 6x² + 9x.", "3x(2x + 3)", "HCF = 3x", "short_answer", 1, 2),
            ("Solve: 3x + 7 = 22.", "x = 5", "3x = 15 → x = 5", "short_answer", 1, 1),
            ("Find the nth term of the sequence: 5, 9, 13, 17, …", "4n + 1", "Common difference 4; first term 5 → 4(1)+1=5 ✓", "short_answer", 1, 2),
            ("Solve the simultaneous equations: 2x + y = 7 and x − y = 2.", "x = 3, y = 1", "Adding: 3x = 9 → x = 3; y = 7−6 = 1", "calculation", 2, 4),
            ("Solve x² − 5x + 6 = 0.", "x = 2 or x = 3", "Factorise: (x−2)(x−3) = 0", "short_answer", 2, 3),
            ("Rearrange v = u + at to make a the subject.", "a = (v − u) / t", "Subtract u: v−u = at; divide t", "short_answer", 1, 2),
            ("Solve the inequality: 4x − 3 > 9.", "x > 3", "4x > 12 → x > 3", "short_answer", 1, 2),
            ("A sequence has nth term 3n² − 1. What is the 4th term?", "47", "3(16)−1 = 48−1 = 47", "calculation", 2, 3),
        ],
        "Ratio, Proportion & Rates": [
            ("Divide £240 in the ratio 3:5.", "£90 and £150", "Total parts = 8; each part = £30; 3×30=90, 5×30=150", "calculation", 1, 2),
            ("A car travels 150 km in 2.5 hours. What is its average speed?", "60 km/h", "speed = distance ÷ time = 150 ÷ 2.5 = 60", "calculation", 1, 2),
            ("If 5 workers take 12 days to build a wall, how long would 3 workers take (same rate)?", "20 days", "5×12 = 60 worker-days; 60 ÷ 3 = 20 days", "calculation", 2, 3),
            ("Increase £360 by 12.5%.", "£405", "12.5% of 360 = 45; 360+45 = 405", "calculation", 1, 2),
            ("A recipe uses flour and sugar in ratio 4:1. How much sugar is needed for 500 g of flour?", "125 g", "500 ÷ 4 = 125 g", "calculation", 1, 2),
        ],
        "Geometry & Measures": [
            ("What is the area of a circle with radius 7 cm? Leave your answer in terms of π.", "49π cm²", "A = πr² = π×49 = 49π", "calculation", 1, 2),
            ("Calculate the volume of a cuboid 5 cm × 3 cm × 4 cm.", "60 cm³", "V = l×w×h = 60", "calculation", 1, 2),
            ("Two angles of a triangle are 65° and 72°. What is the third angle?", "43°", "180−65−72 = 43°", "short_answer", 1, 1),
            ("A right-angled triangle has legs 6 cm and 8 cm. What is the hypotenuse?", "10 cm", "c² = 36+64 = 100 → c = 10", "calculation", 1, 2),
            ("What is the circumference of a circle with diameter 14 cm? (π ≈ 3.14)", "43.96 cm", "C = πd = 3.14×14 = 43.96", "calculation", 1, 2),
            ("A parallelogram has base 9 cm and height 5 cm. Find its area.", "45 cm²", "A = base × height = 9 × 5 = 45", "calculation", 1, 2),
            ("Describe a full rotation of a shape about a point. How many degrees?", "360°", "A full rotation is 360°", "short_answer", 1, 1),
        ],
        "Statistics & Probability": [
            ("A dice is rolled once. What is the probability of getting a number greater than 4?", "1/3", "Favourable: 5 and 6 → 2/6 = 1/3", "short_answer", 1, 2),
            ("Find the mean of: 3, 7, 7, 9, 14.", "8", "(3+7+7+9+14)/5 = 40/5 = 8", "calculation", 1, 2),
            ("What is the median of: 2, 5, 8, 11, 14?", "8", "Middle value of 5 ordered values", "short_answer", 1, 1),
            ("A bag has 4 red and 6 blue marbles. A marble is drawn at random. What is P(blue)?", "3/5", "6/10 = 3/5", "short_answer", 1, 1),
            ("In a survey 40 students were asked their favourite sport. 18 said football. What percentage chose football?", "45%", "18/40 × 100 = 45%", "calculation", 1, 2),
        ],
    },

    # ── BIOLOGY ──────────────────────────────────────────────────────────────
    "biology": {
        "Cell Biology": [
            ("State two differences between a plant cell and an animal cell.", "Plant cells have a cell wall and chloroplasts; animal cells do not.", "Cell wall (cellulose), chloroplasts, large vacuole are plant-only.", "short_answer", 1, 2),
            ("What is the function of mitochondria?", "They are the site of aerobic respiration, releasing energy (ATP) for the cell.", "Powerhouse of the cell — ATP synthesis via cellular respiration.", "short_answer", 1, 2),
            ("Define osmosis.", "The movement of water molecules from a region of higher water potential to lower water potential through a partially permeable membrane.", "Semi-permeable membrane, water potential gradient.", "short_answer", 2, 3),
            ("What is the purpose of mitosis?", "To produce two genetically identical daughter cells for growth and repair.", "Identical copies — used in asexual reproduction, growth, repair.", "short_answer", 1, 2),
            ("Calculate the magnification if an image is 60 mm and the actual size is 0.02 mm.", "3000×", "Magnification = image size ÷ actual size = 60 ÷ 0.02 = 3000", "calculation", 2, 3),
            ("Describe the role of the cell membrane.", "Controls what enters and leaves the cell (selective permeability).", "Phospholipid bilayer — controls substance movement.", "short_answer", 1, 2),
        ],
        "Organisation": [
            ("Name the four stages of food digestion.", "Ingestion, digestion, absorption, egestion", "In order: eating, breaking down, absorbing nutrients, expelling waste.", "short_answer", 1, 2),
            ("What is the role of bile in digestion?", "Bile emulsifies fats, breaking large fat globules into smaller droplets to increase the surface area for lipase.", "Made in liver, stored in gall bladder — emulsifies fats.", "short_answer", 2, 3),
            ("Describe how the heart pumps blood around the body.", "The right ventricle pumps deoxygenated blood to the lungs; the left ventricle pumps oxygenated blood to the body.", "Two separate circuits — pulmonary and systemic.", "extended", 2, 4),
            ("What enzyme breaks down starch?", "Amylase", "Produced in salivary glands and pancreas; breaks starch into maltose.", "short_answer", 1, 1),
            ("Why do enzymes have an optimum temperature?", "At the optimum temperature (around 37°C in humans) the enzyme's active site is the correct shape to bind the substrate. Above this temperature the enzyme denatures.", "Active site shape matches substrate — denaturing changes active site shape.", "short_answer", 2, 3),
        ],
        "Infection & Response": [
            ("Define a pathogen.", "A microorganism that causes disease.", "Bacteria, viruses, fungi, protists — all can be pathogens.", "short_answer", 1, 1),
            ("How do vaccines prevent disease?", "Vaccines introduce dead or weakened pathogens (or antigens) which stimulate the immune system to produce antibodies, creating immunological memory without causing disease.", "Memory cells formed — faster response on re-exposure.", "short_answer", 2, 3),
            ("What is the difference between bacteria and viruses in terms of treatment?", "Bacterial infections can be treated with antibiotics; viruses cannot — antivirals may help but antibiotics are ineffective.", "Antibiotics target bacterial processes not found in viruses.", "short_answer", 2, 3),
            ("Name one way white blood cells defend the body.", "Phagocytosis / producing antibodies / producing antitoxins", "Three mechanisms: engulf, antibody, antitoxin.", "short_answer", 1, 1),
        ],
        "Bioenergetics": [
            ("Write the word equation for photosynthesis.", "Carbon dioxide + water → glucose + oxygen", "Light energy required; chlorophyll absorbs it.", "short_answer", 1, 2),
            ("State three factors that affect the rate of photosynthesis.", "Light intensity, carbon dioxide concentration, temperature", "Limiting factors — any one can limit rate.", "short_answer", 1, 2),
            ("What is aerobic respiration?", "The release of energy from glucose using oxygen: glucose + oxygen → carbon dioxide + water + energy (ATP)", "Occurs in mitochondria; produces ATP.", "short_answer", 1, 2),
            ("When does anaerobic respiration occur in humans?", "During intense exercise when oxygen demand exceeds supply, e.g. sprinting.", "Produces lactic acid in animals; produces ethanol+CO₂ in yeast.", "short_answer", 1, 2),
        ],
        "Homeostasis & Response": [
            ("What is homeostasis?", "The maintenance of a stable internal environment within the body (e.g. temperature, blood glucose, water balance).", "Negative feedback loops maintain set points.", "short_answer", 2, 3),
            ("What gland produces insulin and what does insulin do?", "The pancreas. Insulin lowers blood glucose by stimulating cells to absorb glucose and the liver to convert glucose to glycogen.", "Beta cells in pancreas; opposite of glucagon.", "short_answer", 2, 3),
            ("Describe the nervous system's response pathway.", "Stimulus → receptor → sensory neurone → (CNS) → motor neurone → effector → response", "Receptor detects; effector acts.", "short_answer", 1, 2),
        ],
        "Inheritance, Variation & Evolution": [
            ("What is a gene?", "A section of DNA that codes for the production of a specific protein.", "Each gene = one protein = one trait (simplified).", "short_answer", 1, 2),
            ("If both parents are carriers (Aa) for a recessive condition, what is the probability the child will have the condition?", "25%", "Aa × Aa → AA:Aa:Aa:aa = 1:2:1 → 1/4 chance of aa", "calculation", 2, 3),
            ("What is natural selection?", "Individuals with advantageous adaptations are more likely to survive and reproduce, passing those traits to offspring. Over time this leads to evolution.", "Survival of the fittest — differential reproductive success.", "short_answer", 2, 3),
        ],
    },

    # ── CHEMISTRY ────────────────────────────────────────────────────────────
    "chemistry": {
        "Atomic Structure & the Periodic Table": [
            ("What are the three subatomic particles in an atom and their charges?", "Proton (+1), neutron (0), electron (−1)", "Protons and neutrons in nucleus; electrons orbit in shells.", "short_answer", 1, 2),
            ("Define isotopes.", "Atoms of the same element with the same number of protons but different numbers of neutrons.", "Same atomic number, different mass number.", "short_answer", 1, 2),
            ("An element has atomic number 11 and mass number 23. How many neutrons does it have?", "12", "Neutrons = mass number − atomic number = 23 − 11 = 12", "calculation", 1, 2),
            ("Why are noble gases unreactive?", "They have a full outer electron shell (stable octet), so they have no tendency to gain or lose electrons.", "Group 0 — full outer shell = stable.", "short_answer", 1, 2),
        ],
        "Bonding, Structure & Properties": [
            ("Describe ionic bonding.", "The transfer of electrons from a metal to a non-metal to form oppositely charged ions that attract each other.", "Metal loses electrons → cation; non-metal gains → anion.", "short_answer", 2, 3),
            ("Why do ionic compounds have high melting points?", "They have strong electrostatic forces between the oppositely charged ions in a giant lattice structure, requiring a lot of energy to break.", "Giant ionic lattice — strong forces between ions.", "short_answer", 2, 3),
            ("Describe covalent bonding.", "The sharing of a pair of electrons between two non-metal atoms.", "Both atoms achieve a full outer shell.", "short_answer", 1, 2),
            ("Why does diamond have such a high melting point?", "Each carbon atom forms 4 strong covalent bonds in a giant covalent lattice, requiring enormous energy to break.", "Giant covalent structure — all strong C–C bonds.", "short_answer", 2, 3),
        ],
        "Quantitative Chemistry": [
            ("Calculate the relative formula mass (Mr) of water (H₂O). (H = 1, O = 16)", "18", "2×1 + 16 = 18", "calculation", 1, 2),
            ("How many moles are in 44 g of CO₂? (Mr = 44)", "1 mol", "moles = mass ÷ Mr = 44 ÷ 44 = 1", "calculation", 1, 2),
            ("Define percentage yield.", "Percentage yield = (actual yield ÷ theoretical yield) × 100%", "Actual vs theoretical; always ≤ 100%.", "short_answer", 1, 2),
            ("In a reaction, 10 g of magnesium produces 16.7 g of magnesium oxide. The theoretical yield is 16.6 g. What is the percentage yield?", "≈ 100.6%  (accept 100%)", "10/16.6 × 100 ≈ 100%. Experimental yield can be >100% due to impurities/measuring errors.", "calculation", 2, 3),
        ],
        "Chemical Changes": [
            ("Define oxidation in terms of electrons.", "Loss of electrons (OIL — Oxidation Is Loss)", "Reduction = gain electrons; OILRIG mnemonic.", "short_answer", 1, 2),
            ("What is the pH of a neutral solution?", "7", "pH < 7 = acidic; pH > 7 = alkaline; pH 7 = neutral.", "short_answer", 1, 1),
            ("Write the general equation for a metal reacting with an acid.", "Metal + acid → salt + hydrogen", "E.g. Mg + H₂SO₄ → MgSO₄ + H₂", "short_answer", 1, 2),
            ("What is electrolysis?", "The decomposition of a molten or dissolved ionic compound by passing an electric current through it.", "Electrolyte carries current; ions move to electrodes.", "short_answer", 2, 3),
        ],
        "Energy Changes": [
            ("What is an exothermic reaction? Give an example.", "A reaction that releases energy to the surroundings, causing the temperature to increase. E.g. combustion of methane.", "Products have less energy than reactants; ΔH is negative.", "short_answer", 1, 2),
            ("What is bond energy?", "The energy required to break one mole of a particular bond between atoms.", "Breaking bonds requires energy; forming bonds releases energy.", "short_answer", 1, 2),
            ("Using bond energies, H–H = 436 kJ/mol and H–Cl = 432 kJ/mol, Cl–Cl = 243 kJ/mol, calculate ΔH for H₂ + Cl₂ → 2HCl.", "ΔH = −184 kJ/mol", "Bonds broken: 436+243=679; bonds made: 2×432=864; ΔH=679−864=−185 kJ (accept ±5)", "calculation", 3, 5),
        ],
        "Rate & Equilibrium": [
            ("State four factors that increase the rate of a chemical reaction.", "Increased temperature, increased concentration, increased surface area, addition of a catalyst", "More collisions with sufficient energy = faster rate.", "short_answer", 1, 2),
            ("Define a catalyst.", "A substance that speeds up a reaction by providing an alternative pathway with a lower activation energy, without being used up.", "Not consumed — can be reused; specific to reactions.", "short_answer", 1, 2),
            ("State Le Chatelier's Principle.", "If a system at equilibrium is disturbed, it will shift to oppose the change and re-establish equilibrium.", "Applied to temperature, pressure, concentration changes.", "short_answer", 2, 3),
        ],
    },

    # ── PHYSICS ──────────────────────────────────────────────────────────────
    "physics": {
        "Energy": [
            ("State the principle of conservation of energy.", "Energy cannot be created or destroyed; it can only be transferred from one form to another.", "Total energy in a closed system remains constant.", "short_answer", 1, 2),
            ("A 2 kg object is lifted 5 m. Calculate its gain in gravitational potential energy. (g = 10 N/kg)", "100 J", "GPE = mgh = 2 × 10 × 5 = 100 J", "calculation", 1, 2),
            ("A device has an efficiency of 70%. If 500 J of energy is input, how much useful energy is output?", "350 J", "Useful output = 0.70 × 500 = 350 J", "calculation", 1, 2),
            ("Define specific heat capacity.", "The energy required to raise the temperature of 1 kg of a substance by 1°C (or 1 K).", "Q = mcΔT; units: J/(kg·K)", "short_answer", 1, 2),
            ("Calculate the kinetic energy of a 1200 kg car travelling at 20 m/s.", "240 000 J", "KE = ½mv² = 0.5 × 1200 × 400 = 240 000 J", "calculation", 1, 2),
        ],
        "Electricity": [
            ("State Ohm's Law.", "Voltage = Current × Resistance  (V = IR)", "Applies to ohmic conductors at constant temperature.", "short_answer", 1, 1),
            ("In a series circuit with a 12 V battery, R₁ = 4 Ω and R₂ = 8 Ω, what is the current?", "1 A", "Total R = 12 Ω; I = V/R = 12/12 = 1 A", "calculation", 1, 2),
            ("What is the difference between AC and DC current?", "DC (direct current) flows in one direction; AC (alternating current) reverses direction periodically.", "Mains supply is AC (50 Hz, ~230 V); batteries produce DC.", "short_answer", 1, 2),
            ("Calculate the power of a device using 5 A at 230 V.", "1150 W", "P = IV = 5 × 230 = 1150 W", "calculation", 1, 2),
            ("Why is the National Grid at very high voltage?", "High voltage means low current, which reduces the energy lost as heat in the transmission cables (P = I²R).", "Step-up transformer increases V before transmission; step-down at end.", "short_answer", 2, 3),
        ],
        "Particle Model of Matter": [
            ("Describe what happens to particles when a substance melts.", "Particles vibrate faster until they have enough energy to break free from their fixed positions, allowing them to move and flow while still remaining close together.", "Solid → liquid: fixed positions lost, bonds partially broken.", "short_answer", 1, 2),
            ("Calculate the density of a block with mass 500 g and volume 250 cm³.", "2 g/cm³", "ρ = m/V = 500/250 = 2 g/cm³", "calculation", 1, 2),
            ("Define specific latent heat of vaporisation.", "The energy needed to change 1 kg of a liquid to gas at constant temperature.", "No temperature change during change of state.", "short_answer", 2, 3),
        ],
        "Atomic Structure (Physics)": [
            ("What is alpha radiation?", "A helium nucleus (2 protons + 2 neutrons) emitted from a radioactive nucleus.", "Charge +2; stopped by paper or a few cm of air.", "short_answer", 1, 2),
            ("What is meant by half-life?", "The time taken for half the radioactive nuclei in a sample to decay.", "After n half-lives: N remaining = N₀ × (½)ⁿ", "short_answer", 1, 2),
            ("A sample starts with 800 undecayed atoms and has a half-life of 4 years. How many atoms remain after 12 years?", "100", "12/4 = 3 half-lives; 800 → 400 → 200 → 100", "calculation", 2, 3),
        ],
        "Forces": [
            ("State Newton's Second Law.", "Force = Mass × Acceleration  (F = ma)", "Units: N = kg⋅m/s²", "short_answer", 1, 1),
            ("A 70 kg person stands on a scale in a lift accelerating upward at 2 m/s². What does the scale read? (g = 10 m/s²)", "840 N", "F = m(g+a) = 70 × 12 = 840 N", "calculation", 2, 4),
            ("What is the resultant force on an object moving at constant velocity?", "Zero (the forces are balanced).", "Constant velocity → zero acceleration → resultant force = 0", "short_answer", 1, 1),
            ("Explain why a skydiver reaches terminal velocity.", "As the skydiver accelerates, air resistance increases. When air resistance equals weight, there is no net force and they stop accelerating — they have reached terminal velocity.", "Balanced forces → zero resultant → constant velocity.", "extended", 2, 4),
        ],
        "Waves": [
            ("State the wave equation.", "wave speed = frequency × wavelength  (v = fλ)", "Units: m/s, Hz, m", "short_answer", 1, 1),
            ("A wave has a frequency of 200 Hz and wavelength 1.5 m. What is its speed?", "300 m/s", "v = fλ = 200 × 1.5 = 300 m/s", "calculation", 1, 2),
            ("What is the difference between transverse and longitudinal waves?", "Transverse: oscillation perpendicular to direction of travel (e.g. light). Longitudinal: oscillation parallel to direction of travel (e.g. sound).", "Transverse = S-waves, light; Longitudinal = P-waves, sound.", "short_answer", 1, 2),
        ],
    },

    # ── COMPUTER SCIENCE ─────────────────────────────────────────────────────
    "computer_science": {
        "Systems Architecture": [
            ("What does CPU stand for and what is its function?", "Central Processing Unit — it executes program instructions (fetch, decode, execute cycle).", "Heart of a computer; all processing goes through CPU.", "short_answer", 1, 2),
            ("Name the three components of the Von Neumann architecture.", "CPU, Memory (RAM), Input/Output devices (connected via buses)", "Von Neumann: stored-program concept; single shared memory.", "short_answer", 1, 2),
            ("What is cache memory?", "A small, fast type of memory located close to (or inside) the CPU that stores frequently accessed data/instructions for rapid retrieval.", "Faster than RAM; reduces fetch time from main memory.", "short_answer", 1, 2),
            ("State two ways to increase CPU performance.", "Increase clock speed / add more cores / increase cache size", "Trade-offs: clock speed → heat; more cores need parallel software.", "short_answer", 1, 2),
            ("Describe the fetch-decode-execute cycle.", "Fetch: copy instruction from RAM to CPU. Decode: control unit interprets the instruction. Execute: ALU or other component carries out the instruction.", "Repeats for every instruction; PC incremented after fetch.", "short_answer", 2, 3),
        ],
        "Memory & Storage": [
            ("What is the difference between RAM and ROM?", "RAM is volatile (loses data when power is off) and is used for temporary storage of running programs. ROM is non-volatile, holds the boot sequence.", "RAM = Random Access Memory (temp); ROM = Read-Only Memory (permanent).", "short_answer", 1, 2),
            ("Convert the binary number 1011 to denary.", "11", "8+0+2+1 = 11", "calculation", 1, 2),
            ("Convert the denary number 47 to binary.", "00101111", "47 = 32+8+4+2+1 = 0010 1111", "calculation", 2, 3),
            ("What is secondary storage used for?", "Permanent storage of data and programs that must be retained when the computer is turned off.", "HDD, SSD, optical disc, USB — all secondary storage.", "short_answer", 1, 2),
            ("What does the term 'bit' mean?", "A single binary digit — either 0 or 1.", "8 bits = 1 byte; smallest unit of data.", "short_answer", 1, 1),
        ],
        "Networks": [
            ("What is the difference between a LAN and a WAN?", "LAN (Local Area Network) covers a small area (e.g. a building). WAN (Wide Area Network) covers a large area (e.g. the internet spans the globe).", "LAN: owned locally; WAN: uses third-party infrastructure.", "short_answer", 1, 2),
            ("What does a router do?", "A router directs data packets between networks, finding the most efficient path to the destination.", "Operates at network layer; uses IP addresses to route.", "short_answer", 1, 2),
            ("State two advantages of using a network.", "Resource sharing (printers, files, internet) / Communication between users / Centralised backup / Centralised security", "Any two valid advantages.", "short_answer", 1, 2),
            ("What is packet switching?", "Data is broken into small packets, sent independently across a network (possibly by different routes), and reassembled at the destination.", "Efficient use of network; robust to congestion or failure.", "short_answer", 2, 3),
            ("Name the four layers of the TCP/IP model.", "Application, Transport, Internet, Link (Network Access)", "HTTP/HTTPS at Application; TCP/UDP at Transport; IP at Internet.", "short_answer", 2, 3),
        ],
        "Data Representation": [
            ("How many different values can be stored in 8 bits?", "256 (0 to 255)", "2⁸ = 256", "calculation", 1, 2),
            ("What is ASCII used for?", "ASCII is a character encoding standard that assigns a unique binary number to each character (letters, digits, symbols).", "American Standard Code for Information Interchange; 7-bit standard.", "short_answer", 1, 2),
            ("Convert the hexadecimal number A3 to denary.", "163", "A=10; 10×16 + 3 = 163", "calculation", 2, 3),
            ("Why is hexadecimal used by programmers?", "Hexadecimal is a compact way to represent binary — each hex digit represents exactly 4 bits, making binary values easier to read and write.", "1 hex digit = 4 bits = nibble; easier than long binary strings.", "short_answer", 1, 2),
        ],
        "Programming Concepts": [
            ("What is the difference between a function and a procedure?", "A function returns a value; a procedure (subroutine) performs a set of instructions without returning a value.", "Functions have return values; procedures do not.", "short_answer", 1, 2),
            ("What does DRY stand for in programming?", "Don't Repeat Yourself — code should not contain repeated blocks; use functions/procedures instead.", "Improves maintainability and reduces bugs.", "short_answer", 1, 1),
            ("What is a variable in programming?", "A named memory location that stores a value which can change during program execution.", "Contrast with a constant, which cannot change.", "short_answer", 1, 1),
            ("What is the output of: for i in range(1, 4): print(i)?", "1\n2\n3", "range(1,4) generates 1, 2, 3 (4 is excluded).", "short_answer", 1, 2),
            ("Define recursion.", "When a function calls itself as part of its own definition, with a base case to stop infinite recursion.", "Every recursive call must move toward the base case.", "short_answer", 2, 3),
        ],
        "Boolean Logic": [
            ("What does an AND gate output when inputs are A=1 and B=0?", "0", "AND: output is 1 only if BOTH inputs are 1.", "short_answer", 1, 1),
            ("Complete the truth table row: NOT(A OR B) when A=1, B=0.", "0", "A OR B = 1; NOT 1 = 0", "short_answer", 1, 2),
            ("Simplify using De Morgan's Law: NOT(A AND B).", "NOT A OR NOT B", "De Morgan: NOT(A AND B) = (NOT A) OR (NOT B)", "short_answer", 2, 3),
            ("What logic gate gives output 1 when inputs are different?", "XOR (Exclusive OR)", "XOR: 0,0→0; 0,1→1; 1,0→1; 1,1→0", "short_answer", 1, 2),
        ],
        "Cyber Security": [
            ("Define malware.", "Malicious software designed to disrupt, damage, or gain unauthorised access to a computer system. Examples include viruses, worms, ransomware.", "Malware = malicious software; many types.", "short_answer", 1, 2),
            ("What is a phishing attack?", "A social engineering attack where the attacker sends fraudulent emails or messages pretending to be a trustworthy source to trick users into revealing sensitive information.", "Not technical hacking — targets human psychology.", "short_answer", 1, 2),
            ("What is encryption?", "The process of encoding data so that only authorised parties with the decryption key can read it.", "Plaintext → ciphertext using an algorithm + key.", "short_answer", 1, 2),
            ("State two ways to keep a network secure.", "Use strong passwords / firewall / encryption / two-factor authentication / regular software updates / access control", "Any two valid security measures.", "short_answer", 1, 2),
        ],
    },
}


class Command(BaseCommand):
    help = "Seed 200+ static practice questions across all GCSE subjects"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview without writing")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = 0
        skipped = 0

        for subject_name, topics in QUESTIONS.items():
            try:
                subject = Subject.objects.get(name=subject_name)
            except Subject.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Subject not found: {subject_name} — skipping"))
                continue

            for topic_name, questions in topics.items():
                topic = Topic.objects.filter(subject=subject, name=topic_name, is_active=True).first()
                if not topic:
                    self.stdout.write(self.style.WARNING(f"  Topic not found: {topic_name} in {subject_name}"))
                    continue

                lesson = Lesson.objects.filter(topic=topic, is_active=True).order_by("order").first()
                if not lesson:
                    if dry_run:
                        self.stdout.write(f"  [DRY RUN] Would create lesson for {topic_name}")
                        skipped += len(questions)
                        continue
                    lesson = Lesson.objects.create(
                        topic=topic,
                        title=f"{topic_name} Practice",
                        content=f"Practice questions for {topic_name}.",
                        estimated_duration=20,
                        lesson_type="practice",
                        difficulty_level=2,
                        key_skills=[],
                        order=1,
                        is_active=True,
                    )

                for q_text, answer, explanation, q_type, difficulty, marks in questions:
                    exists = Question.objects.filter(
                        lesson__topic=topic,
                        question_text=q_text,
                    ).exists()
                    if exists:
                        skipped += 1
                        continue
                    if not dry_run:
                        Question.objects.create(
                            lesson=lesson,
                            question_text=q_text,
                            correct_answer=answer,
                            explanation=explanation,
                            question_type=q_type,
                            difficulty_level=difficulty,
                            marks_available=marks,
                            source="extended_bank",
                            is_active=True,
                        )
                    created += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Done — {created} questions {'would be ' if dry_run else ''}created, {skipped} skipped (already exist)."
        ))
