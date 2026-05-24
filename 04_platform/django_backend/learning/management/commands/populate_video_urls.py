"""
Populate Lesson.video_url with specific YouTube video IDs
mapped by lesson title keywords.
Usage: python manage.py populate_video_urls [--dry-run] [--subject mathematics]
"""
from django.core.management.base import BaseCommand
from learning.models import Lesson

# Corbett Maths YouTube video IDs mapped to lesson title keywords
MATHS_VIDEO_MAP = {
    "bodmas": "jzKBMFMoEfc",
    "order of operations": "jzKBMFMoEfc",
    "prime factor": "K2sTBHCPHhA",
    "prime number": "K2sTBHCPHhA",
    "highest common factor": "I_BYCn6LHWE",
    "hcf": "I_BYCn6LHWE",
    "lowest common multiple": "7kdX3JdWkYY",
    "lcm": "7kdX3JdWkYY",
    "fractions": "Z4YmZNk3q_I",
    "adding fractions": "Z4YmZNk3q_I",
    "subtracting fractions": "Z4YmZNk3q_I",
    "multiplying fractions": "nvDRFTOYOGQ",
    "dividing fractions": "KPzMwrIBHsk",
    "percentages": "JHv9fZyL1BM",
    "percentage": "JHv9fZyL1BM",
    "ratio": "znt2hLgXejU",
    "proportion": "znt2hLgXejU",
    "algebra": "nbk1AXiMFmA",
    "expanding brackets": "jAL4QeM6UMY",
    "factorising": "WDFZhJkI8aA",
    "factoring": "WDFZhJkI8aA",
    "solving equations": "nbk1AXiMFmA",
    "linear equations": "nbk1AXiMFmA",
    "quadratic": "tGFBCVRnaRY",
    "simultaneous": "zkt9-hfZ3tE",
    "sequences": "R-iWnONurBE",
    "nth term": "R-iWnONurBE",
    "pythagoras": "q9ZqiCkNGls",
    "trigonometry": "ILaFqNAVAU4",
    "sin": "ILaFqNAVAU4",
    "cos": "ILaFqNAVAU4",
    "tan": "ILaFqNAVAU4",
    "area": "FxXmODLiXbY",
    "perimeter": "FxXmODLiXbY",
    "volume": "p-MqxWnpWzw",
    "circle": "bJnmZuVLbbc",
    "circumference": "bJnmZuVLbbc",
    "probability": "jkSyJLpuPpk",
    "statistics": "h7koV_PH5Cg",
    "mean": "h7koV_PH5Cg",
    "median": "h7koV_PH5Cg",
    "mode": "h7koV_PH5Cg",
    "range": "h7koV_PH5Cg",
    "standard deviation": "h7koV_PH5Cg",
    "graph": "BXJQ6K-CNEA",
    "straight line": "BXJQ6K-CNEA",
    "gradient": "BXJQ6K-CNEA",
    "y = mx": "BXJQ6K-CNEA",
    "indices": "n8OMijcq2Sw",
    "powers": "n8OMijcq2Sw",
    "surds": "TqA2bGqEUKM",
    "vectors": "JWfcvMO7_1k",
    "transformation": "6vX6s5uHbB0",
    "reflection": "6vX6s5uHbB0",
    "rotation": "6vX6s5uHbB0",
    "translation": "6vX6s5uHbB0",
    "enlargement": "6vX6s5uHbB0",
    "loci": "xALCl59gRBo",
    "constructions": "xALCl59gRBo",
    "bearing": "TUcVmOWvLXY",
    "bounds": "0X8TZZhgQWk",
    "rounding": "0X8TZZhgQWk",
    "decimal": "0X8TZZhgQWk",
    "significant figures": "0X8TZZhgQWk",
    "standard form": "fmwAbdR5mKE",
    "speed": "msq8rcxlLr8",
    "distance": "msq8rcxlLr8",
    "density": "msq8rcxlLr8",
    "pressure": "msq8rcxlLr8",
    "direct proportion": "znt2hLgXejU",
    "inverse proportion": "znt2hLgXejU",
    "venn diagram": "EeZUTtHxc0E",
    "set notation": "EeZUTtHxc0E",
    "histogram": "GGMEMqbBEVw",
    "cumulative frequency": "GGMEMqbBEVw",
    "box plot": "GGMEMqbBEVw",
    "scatter": "h7koV_PH5Cg",
    "correlation": "h7koV_PH5Cg",
    "equation of a line": "BXJQ6K-CNEA",
    "inequality": "Zp8n_ZWHzuU",
    "inequalities": "Zp8n_ZWHzuU",
    "number line": "Zp8n_ZWHzuU",
    "negative number": "WbxU3O1KSeo",
    "integer": "WbxU3O1KSeo",
    "multiples": "7kdX3JdWkYY",
    "factors": "I_BYCn6LHWE",
    "collecting like terms": "nbk1AXiMFmA",
    "like terms": "nbk1AXiMFmA",
    "expanding double": "jAL4QeM6UMY",
    "expanding triple": "jAL4QeM6UMY",
    "double brackets": "jAL4QeM6UMY",
    "triple brackets": "jAL4QeM6UMY",
    "completing the square": "tGFBCVRnaRY",
    "rearranging": "tGFBCVRnaRY",
    "formula": "tGFBCVRnaRY",
    "expressions": "nbk1AXiMFmA",
    "iterative": "nbk1AXiMFmA",
    "functions": "nbk1AXiMFmA",
    "inverse function": "nbk1AXiMFmA",
    "parallel lines": "BXJQ6K-CNEA",
    "perpendicular": "BXJQ6K-CNEA",
    "midpoint": "BXJQ6K-CNEA",
    "simple interest": "JHv9fZyL1BM",
    "best buy": "znt2hLgXejU",
    "symmetry": "6vX6s5uHbB0",
    "3d shapes": "p-MqxWnpWzw",
    "2d projection": "p-MqxWnpWzw",
    "angle": "FxXmODLiXbY",
    "polygon": "FxXmODLiXbY",
    "triangle": "FxXmODLiXbY",
    "quadrilateral": "FxXmODLiXbY",
    "congruent": "FxXmODLiXbY",
    "similar shapes": "FxXmODLiXbY",
    "maps": "TUcVmOWvLXY",
    "scale drawing": "TUcVmOWvLXY",
    "vector basics": "JWfcvMO7_1k",
    "listing outcomes": "jkSyJLpuPpk",
    "product rule": "jkSyJLpuPpk",
    "and / or": "jkSyJLpuPpk",
    "and/or": "jkSyJLpuPpk",
    "tree diagram": "jkSyJLpuPpk",
    "types of data": "h7koV_PH5Cg",
    "collecting data": "h7koV_PH5Cg",
    "frequency table": "GGMEMqbBEVw",
    "grouped frequency": "GGMEMqbBEVw",
    "pie chart": "GGMEMqbBEVw",
    "estimating": "0X8TZZhgQWk",
    "square root": "0X8TZZhgQWk",
    "prime": "K2sTBHCPHhA",
    "composite": "K2sTBHCPHhA",
    "deciding whether": "R-iWnONurBE",
    "term is in a sequence": "R-iWnONurBE",
}

# Free Science Lessons YouTube video IDs
BIOLOGY_VIDEO_MAP = {
    "cell": "8IlzKri08kU",
    "mitosis": "SNReVk_ruAA",
    "meiosis": "VzDMG7ke69g",
    "dna": "AQhkDPALYuI",
    "protein": "ztCpEoGn6zk",
    "enzyme": "EyUKJjUBo8E",
    "photosynthesis": "TqhCjbk1Hgk",
    "respiration": "y73GsFSi6mM",
    "breathing": "y73GsFSi6mM",
    "heart": "CWFd9KuVFts",
    "blood": "CWFd9KuVFts",
    "circulation": "CWFd9KuVFts",
    "nervous": "HShVnHZAB2w",
    "neuron": "HShVnHZAB2w",
    "hormone": "HShVnHZAB2w",
    "homeostasis": "HShVnHZAB2w",
    "evolution": "hOfITABFZvA",
    "natural selection": "hOfITABFZvA",
    "genetics": "CBezq1fFUEA",
    "inheritance": "CBezq1fFUEA",
    "ecosystem": "fTBNDOt7wvc",
    "food chain": "fTBNDOt7wvc",
    "biodiversity": "fTBNDOt7wvc",
    "bacteria": "8IlzKri08kU",
    "virus": "8IlzKri08kU",
    "immune": "8IlzKri08kU",
    "plant": "TqhCjbk1Hgk",
    "osmosis": "VzDMG7ke69g",
    "diffusion": "VzDMG7ke69g",
    "active transport": "VzDMG7ke69g",
    "reproduction": "VzDMG7ke69g",
    "variation": "hOfITABFZvA",
    "classification": "hOfITABFZvA",
    "surface area": "VzDMG7ke69g",
    "exchange surface": "VzDMG7ke69g",
    "kingdom": "hOfITABFZvA",
    "microscop": "8IlzKri08kU",
    "binary fission": "8IlzKri08kU",
    "culturing": "8IlzKri08kU",
    "microorganism": "8IlzKri08kU",
    "cardiovascular": "CWFd9KuVFts",
    "disease": "8IlzKri08kU",
    "cancer": "8IlzKri08kU",
    "transpiration": "TqhCjbk1Hgk",
    "translocation": "TqhCjbk1Hgk",
    "diet": "EyUKJjUBo8E",
    "nutrient": "EyUKJjUBo8E",
    "biological molecule": "EyUKJjUBo8E",
    "digestive": "EyUKJjUBo8E",
    "food test": "EyUKJjUBo8E",
    "lung": "y73GsFSi6mM",
    "gas exchange": "y73GsFSi6mM",
    "communicable": "8IlzKri08kU",
    "protist": "8IlzKri08kU",
    "fungi": "8IlzKri08kU",
    "vaccination": "8IlzKri08kU",
    "immunisation": "8IlzKri08kU",
    "drug": "8IlzKri08kU",
    "medicine": "8IlzKri08kU",
    "monoclonal": "8IlzKri08kU",
    "antibod": "8IlzKri08kU",
    "exercise": "y73GsFSi6mM",
    "kidney": "HShVnHZAB2w",
    "contraception": "HShVnHZAB2w",
    "fertility": "HShVnHZAB2w",
    "adrenaline": "HShVnHZAB2w",
    "thyroxine": "HShVnHZAB2w",
    "brain": "HShVnHZAB2w",
    "eye": "HShVnHZAB2w",
    "thermoregulation": "HShVnHZAB2w",
    "endocrine": "HShVnHZAB2w",
    "glucose": "HShVnHZAB2w",
    "diabetes": "HShVnHZAB2w",
    "family tree": "CBezq1fFUEA",
    "inherited disorder": "CBezq1fFUEA",
    "embryo": "CBezq1fFUEA",
    "mendel": "CBezq1fFUEA",
    "darwin": "hOfITABFZvA",
    "wallace": "hOfITABFZvA",
    "lamarck": "hOfITABFZvA",
    "selective breeding": "hOfITABFZvA",
    "genetic modification": "AQhkDPALYuI",
    "genetic engineering": "AQhkDPALYuI",
    "genome": "AQhkDPALYuI",
    "cloning": "AQhkDPALYuI",
    "fossil": "hOfITABFZvA",
    "extinction": "hOfITABFZvA",
    "speciation": "hOfITABFZvA",
    "antibiotic": "8IlzKri08kU",
    "mutation": "AQhkDPALYuI",
    "punnet": "CBezq1fFUEA",
    "genetic diagram": "CBezq1fFUEA",
    "ecology": "fTBNDOt7wvc",
    "pregnancy test": "HShVnHZAB2w",
}

CHEMISTRY_VIDEO_MAP = {
    "atom": "PQpEjxn3LaA",
    "element": "PQpEjxn3LaA",
    "compound": "PQpEjxn3LaA",
    "mixture": "PQpEjxn3LaA",
    "periodic table": "PQpEjxn3LaA",
    "bond": "8sMcEfRHIaM",
    "ionic": "8sMcEfRHIaM",
    "covalent": "8sMcEfRHIaM",
    "metallic": "8sMcEfRHIaM",
    "reaction": "T2pEzVB_bFk",
    "equation": "T2pEzVB_bFk",
    "acid": "QBs4TsK_9Fo",
    "base": "QBs4TsK_9Fo",
    "alkali": "QBs4TsK_9Fo",
    "salt": "QBs4TsK_9Fo",
    "electrolysis": "vPQgWMlUL5I",
    "oxidation": "T2pEzVB_bFk",
    "reduction": "T2pEzVB_bFk",
    "rate of reaction": "T2pEzVB_bFk",
    "catalyst": "T2pEzVB_bFk",
    "equilibrium": "T2pEzVB_bFk",
    "organic": "PQpEjxn3LaA",
    "hydrocarbon": "PQpEjxn3LaA",
    "polymer": "PQpEjxn3LaA",
    "crude oil": "PQpEjxn3LaA",
    "metal": "8sMcEfRHIaM",
    "non-metal": "8sMcEfRHIaM",
    "gas": "PQpEjxn3LaA",
    "mole": "T2pEzVB_bFk",
    "concentration": "T2pEzVB_bFk",
    "temperature": "T2pEzVB_bFk",
    "energy": "T2pEzVB_bFk",
    "exothermic": "T2pEzVB_bFk",
    "endothermic": "T2pEzVB_bFk",
    "filtration": "PQpEjxn3LaA",
    "crystallisation": "PQpEjxn3LaA",
    "distillation": "PQpEjxn3LaA",
    "electronic structure": "PQpEjxn3LaA",
    "formation of ion": "8sMcEfRHIaM",
    "states of matter": "PQpEjxn3LaA",
    "nanoparticle": "PQpEjxn3LaA",
    "diamond": "8sMcEfRHIaM",
    "graphite": "8sMcEfRHIaM",
    "graphene": "8sMcEfRHIaM",
    "fullerene": "8sMcEfRHIaM",
    "relative formula": "T2pEzVB_bFk",
    "formula mass": "T2pEzVB_bFk",
    "conservation of mass": "T2pEzVB_bFk",
    "limiting reactant": "T2pEzVB_bFk",
    "percentage yield": "T2pEzVB_bFk",
    "titration": "QBs4TsK_9Fo",
    "fuel cell": "vPQgWMlUL5I",
    "battery": "vPQgWMlUL5I",
    "le chatelier": "T2pEzVB_bFk",
    "ester": "PQpEjxn3LaA",
    "alkane": "PQpEjxn3LaA",
    "fractional distillation": "PQpEjxn3LaA",
    "cracking": "PQpEjxn3LaA",
    "alkene": "PQpEjxn3LaA",
    "alcohol": "PQpEjxn3LaA",
    "ethanol": "PQpEjxn3LaA",
    "cells & batteries": "vPQgWMlUL5I",
    "cell": "vPQgWMlUL5I",
}

PHYSICS_VIDEO_MAP = {
    "force": "kGCuRgmez6E",
    "motion": "kGCuRgmez6E",
    "velocity": "kGCuRgmez6E",
    "acceleration": "kGCuRgmez6E",
    "speed": "kGCuRgmez6E",
    "newton": "kGCuRgmez6E",
    "gravity": "kGCuRgmez6E",
    "weight": "kGCuRgmez6E",
    "mass": "kGCuRgmez6E",
    "energy": "EGW3bGOm_C8",
    "work done": "EGW3bGOm_C8",
    "power": "EGW3bGOm_C8",
    "kinetic": "EGW3bGOm_C8",
    "potential": "EGW3bGOm_C8",
    "wave": "GJf8L2p2oXg",
    "sound": "GJf8L2p2oXg",
    "light": "GJf8L2p2oXg",
    "electromagnetic": "GJf8L2p2oXg",
    "reflection": "GJf8L2p2oXg",
    "refraction": "GJf8L2p2oXg",
    "diffraction": "GJf8L2p2oXg",
    "frequency": "GJf8L2p2oXg",
    "wavelength": "GJf8L2p2oXg",
    "electricity": "8gvJzrjwkds",
    "current": "8gvJzrjwkds",
    "voltage": "8gvJzrjwkds",
    "resistance": "8gvJzrjwkds",
    "circuit": "8gvJzrjwkds",
    "ohm": "8gvJzrjwkds",
    "series": "8gvJzrjwkds",
    "parallel": "8gvJzrjwkds",
    "magnet": "8gvJzrjwkds",
    "magnetic": "8gvJzrjwkds",
    "nuclear": "EqZGnSMsypo",
    "radioactive": "EqZGnSMsypo",
    "radiation": "EqZGnSMsypo",
    "atom": "EqZGnSMsypo",
    "half life": "EqZGnSMsypo",
    "pressure": "kGCuRgmez6E",
    "momentum": "kGCuRgmez6E",
    "space": "EqZGnSMsypo",
    "universe": "EqZGnSMsypo",
    "star": "EqZGnSMsypo",
    "thermal": "EGW3bGOm_C8",
    "heat": "EGW3bGOm_C8",
    "specific heat": "EGW3bGOm_C8",
    "efficiency": "EGW3bGOm_C8",
    "wind": "EGW3bGOm_C8",
    "solar": "EGW3bGOm_C8",
    "biofuel": "EGW3bGOm_C8",
    "kinetic energy": "EGW3bGOm_C8",
    "gpe": "EGW3bGOm_C8",
    "gravitational": "EGW3bGOm_C8",
    "plug": "8gvJzrjwkds",
    "fuse": "8gvJzrjwkds",
    "earthing": "8gvJzrjwkds",
    "electric field": "8gvJzrjwkds",
    "v = ir": "8gvJzrjwkds",
    "i-v graph": "8gvJzrjwkds",
    "component": "8gvJzrjwkds",
    "national grid": "8gvJzrjwkds",
    "particle model": "kGCuRgmez6E",
    "density": "kGCuRgmez6E",
    "distance-time": "kGCuRgmez6E",
    "stopping distance": "kGCuRgmez6E",
    "scalar": "kGCuRgmez6E",
    "vector quantit": "kGCuRgmez6E",
    "resolving vector": "kGCuRgmez6E",
    "elasticity": "kGCuRgmez6E",
    "spring constant": "kGCuRgmez6E",
    "hooke": "kGCuRgmez6E",
    "moment": "kGCuRgmez6E",
    "ray diagram": "GJf8L2p2oXg",
    "x-ray": "EqZGnSMsypo",
    "gamma": "EqZGnSMsypo",
    "lens": "GJf8L2p2oXg",
    "transformer": "8gvJzrjwkds",
    "motor effect": "8gvJzrjwkds",
    "electric motor": "8gvJzrjwkds",
    "generator": "8gvJzrjwkds",
    "alternator": "8gvJzrjwkds",
    "dynamo": "8gvJzrjwkds",
    "oscilloscope": "8gvJzrjwkds",
    "loudspeaker": "8gvJzrjwkds",
    "microphone": "8gvJzrjwkds",
}

SUBJECT_MAPS = {
    "mathematics": MATHS_VIDEO_MAP,
    "biology": BIOLOGY_VIDEO_MAP,
    "chemistry": CHEMISTRY_VIDEO_MAP,
    "physics": PHYSICS_VIDEO_MAP,
}

def find_video_id(title, video_map):
    title_lower = title.lower()
    for keyword, video_id in video_map.items():
        if keyword in title_lower:
            return f"https://www.youtube.com/watch?v={video_id}"
    return None

class Command(BaseCommand):
    help = "Populate lesson video_url fields with matched YouTube videos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show matches without saving"
        )
        parser.add_argument(
            "--subject",
            type=str,
            help="Filter by subject name e.g. mathematics"
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing video URLs"
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        subject_filter = (options.get("subject") or "").lower()
        overwrite = options["overwrite"]

        lessons = Lesson.objects.filter(
            is_active=True
        ).select_related("topic__subject")

        if subject_filter:
            lessons = lessons.filter(
                topic__subject__name__icontains=subject_filter
            )

        updated = 0
        skipped = 0
        no_match = 0

        for lesson in lessons:
            if lesson.video_url and not overwrite:
                skipped += 1
                continue

            subject_name = (
                lesson.topic.subject.name or ""
            ).lower()
            video_map = SUBJECT_MAPS.get(subject_name)

            if not video_map:
                no_match += 1
                continue

            url = find_video_id(lesson.title, video_map)

            if not url:
                no_match += 1
                self.stdout.write(
                    f"  NO MATCH: {lesson.title}"
                )
                continue

            if not dry_run:
                lesson.video_url = url
                lesson.save(update_fields=["video_url"])

            updated += 1
            self.stdout.write(
                f"  {'[DRY]' if dry_run else 'OK'}: "
                f"{lesson.title} → {url}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Matched: {updated} | "
            f"Already set: {skipped} | "
            f"No match: {no_match}"
        ))
