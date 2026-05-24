import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from decision_engine.v1_0.decision_engine_v1 import build_weekly_summaries
from decision_engine.v1_0.core import WeeklyPerformanceSummary

# Get summaries
summaries = build_weekly_summaries(7, 1, weeks=8)

print(f"\nSummaries: {len(summaries)}")
for s in summaries:
    print(f"  Week {s.week_ending}: {s.average_accuracy*100:.0f}% accuracy, {s.questions_attempted} questions")

# Now manually calculate what the grade SHOULD be
if summaries:
    avg_accuracy = sum(s.average_accuracy for s in summaries) / len(summaries)
    
    # GCSE grade mapping (conservative)
    if avg_accuracy >= 0.80:
        grade = 7
    elif avg_accuracy >= 0.70:
        grade = 6
    elif avg_accuracy >= 0.60:
        grade = 5
    elif avg_accuracy >= 0.50:
        grade = 4
    elif avg_accuracy >= 0.40:
        grade = 3
    else:
        grade = 2
    
    print(f"\nAverage accuracy: {avg_accuracy*100:.0f}%")
    print(f"Calculated grade: {grade}")
    print(f"\nThe attainment_band SHOULD be: {grade}")
    print(f"But core.py is returning: 0")
    print(f"\nThis means core.py calculate_attainment_band() has a bug!")

# Check the actual function
from decision_engine.v1_0.core import calculate_attainment_band

coverage = 0.33
attainment = calculate_attainment_band(summaries, coverage_breadth=coverage)

print(f"\nWhat core.py returns: {attainment}")
print(f"With coverage: {coverage}")