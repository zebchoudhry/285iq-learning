# This shows what we need to change in decision_engine_v1.py

print("""
In decision_engine_v1.py, line 178:

CHANGE FROM:
    attainment = calculate_attainment_band(weekly, coverage_breadth=coverage)

CHANGE TO:
    attainment = calculate_attainment_band(weekly, coverage_breadth=coverage, min_weeks=1)

This will allow it to calculate grades with just 1 week of data!
""")