"""
Structured lesson content for Physics Energy topic.
Content uses format supported by formatLessonContent() in lessons.html:
Key Concept, Formula/Key Info, Worked Example, Common Mistake, Quick Check.
"""

ENERGY_LESSON_CONTENT = {
    "Energy Stores & Systems": """Key Concept
Energy cannot be created or destroyed. It is transferred between energy stores within objects or systems. In a closed system, the total energy remains constant.

Formula/Key Info
The eight energy stores are:
Thermal
Kinetic
Gravitational potential
Elastic potential
Chemical
Magnetic
Electrostatic
Nuclear

Energy is transferred by:
Heating
Mechanical work (forces doing work)
Electrical work
Radiation (light or sound)

Worked Example
A moving car slows down when braking.
The car initially has kinetic energy.
Friction between the brakes and wheels transfers energy.
The kinetic energy decreases and the thermal energy store of the brakes increases.

Common Mistake
Confusing energy stores with transfer pathways.
Heating is not a store — it is a transfer pathway.
Energy does not disappear; it spreads to the surroundings.

Quick Check
When a ball falls from a height, which energy store decreases and which increases?
Answer: Gravitational potential energy decreases and kinetic energy increases.""",
    "Kinetic Energy": """Key Concept
Kinetic energy is the energy an object has because it is moving. The faster an object moves and the greater its mass, the more kinetic energy it has.

Formula/Key Info
KE = 0.5 x m x v²
where KE is kinetic energy in joules (J), m is mass in kilograms (kg), and v is speed in metres per second (m/s).
Mass must be in kg and speed in m/s for the answer to be in joules.

Worked Example
A cyclist of mass 60 kg rides at 5 m/s. Calculate kinetic energy.
KE = 0.5 x 60 x 5² = 0.5 x 60 x 25 = 750 J

Common Mistake
Forgetting to square the speed, or using mass in grams instead of kilograms. Always convert units before substituting.

Quick Check
A car of mass 1200 kg travels at 10 m/s. What is its kinetic energy?
Answer: KE = 0.5 x 1200 x 10² = 60 000 J.""",
    "Gravitational Potential Energy & Gravity": """Key Concept
Gravitational potential energy (GPE) is the energy stored in an object when it is raised above the ground. The higher the object and the greater its mass, the more GPE it has.

Formula/Key Info
GPE = m x g x h
where GPE is in joules (J), m is mass in kg, g is gravitational field strength (9.8 N/kg on Earth), and h is height in metres (m).
g = 9.8 N/kg is usually given in exam questions.

Worked Example
A book of mass 2 kg is on a shelf 1.5 m high. Calculate GPE. (g = 9.8 N/kg)
GPE = 2 x 9.8 x 1.5 = 29.4 J

Common Mistake
Using height in cm instead of metres, or forgetting g. Always use metres for height and include g in the calculation.

Quick Check
A 5 kg mass is lifted 3 m. What is its GPE? (g = 9.8 N/kg)
Answer: GPE = 5 x 9.8 x 3 = 147 J.""",
    "Specific Heat Capacity": """Key Concept
Specific heat capacity is the energy needed to raise the temperature of 1 kg of a substance by 1 degree Celsius. Different materials need different amounts of energy to heat up.

Formula/Key Info
E = m x c x Δθ
where E is energy in joules (J), m is mass in kg, c is specific heat capacity in J/(kg°C), and Δθ is temperature change in °C.
Δθ = final temperature minus initial temperature.

Worked Example
Calculate the energy needed to heat 2 kg of water by 10°C. (c for water = 4200 J/(kg°C))
E = 2 x 4200 x 10 = 84 000 J

Common Mistake
Using mass in grams or temperature in Kelvin. Always use kg and Celsius. Watch the sign of Δθ for cooling.

Quick Check
How much energy is needed to heat 0.5 kg of aluminium by 20°C? (c for aluminium = 900 J/(kg°C))
Answer: E = 0.5 x 900 x 20 = 9000 J.""",
    "Power & Work Done": """Key Concept
Power is the rate of energy transfer or the rate of doing work. A more powerful device transfers more energy per second.

Formula/Key Info
P = E / t
where P is power in watts (W), E is energy transferred in joules (J), and t is time in seconds (s).
1 watt = 1 joule per second. Time must be in seconds.

Worked Example
A heater transfers 12 000 J in 2 minutes. Calculate power.
t = 2 x 60 = 120 s
P = 12 000 / 120 = 100 W

Common Mistake
Forgetting to convert time to seconds. Minutes must be multiplied by 60. Hours by 3600.

Quick Check
A motor does 5000 J of work in 10 seconds. What is its power?
Answer: P = 5000 / 10 = 500 W.""",
}

# Skill codes for adaptive diagnostics and mastery weighting
ENERGY_LESSON_SKILLS = {
    "Energy Stores & Systems": [
        "conservation_law",
        "identify_store",
        "identify_transfer",
    ],
    "Kinetic Energy": [
        "kinetic_energy_formula",
        "substitution_calculation",
        "unit_consistency",
    ],
    "Gravitational Potential Energy & Gravity": [
        "gpe_formula",
        "substitution_calculation",
        "use_of_g_value",
    ],
    "Specific Heat Capacity": [
        "shc_formula",
        "temperature_change",
        "unit_application",
    ],
    "Power & Work Done": [
        "power_formula",
        "rate_calculation",
        "unit_conversion_time",
    ],
}
