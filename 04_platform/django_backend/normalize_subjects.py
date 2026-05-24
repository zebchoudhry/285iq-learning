# normalize_subjects.py
"""
Normalize Subject rows:
- Ensure display_name is populated (e.g. 'GCSE Maths')
- Merge duplicate Subject rows by `name` into a single canonical Subject
- Reassign related Topic, StudySession, StudentExamSettings rows to the canonical Subject
- Delete duplicate Subject rows after reassignment
"""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")
django.setup()

from learning.models import Subject, Topic, StudySession, StudentExamSettings
from django.db import transaction

# Map name -> canonical display_name fallback
DISPLAY_FALLBACK = {
    'mathematics': 'GCSE Maths',
    'biology': 'GCSE Biology',
    'chemistry': 'GCSE Chemistry',
    'physics': 'GCSE Physics',
}

def choose_canonical(subjects):
    # Prefer subject with non-empty display_name, else first
    for s in subjects:
        if s.display_name and s.display_name.strip():
            return s
    return subjects[0]

def normalize():
    names = Subject.objects.values_list('name', flat=True).distinct()
    changed = []
    deleted_ids = []
    with transaction.atomic():
        for name in names:
            subjects = list(Subject.objects.filter(name=name).order_by('id'))
            if not subjects:
                continue
            canonical = choose_canonical(subjects)
            # Ensure canonical has a display_name
            if not (canonical.display_name and canonical.display_name.strip()):
                canonical.display_name = DISPLAY_FALLBACK.get(name, name.title())
                canonical.save()
                changed.append((canonical.id, 'display_name set', canonical.display_name))
            # Reassign related objects for any duplicates
            duplicates = [s for s in subjects if s.id != canonical.id]
            for dup in duplicates:
                # Topics reference Subject directly
                Topic.objects.filter(subject=dup).update(subject=canonical)
                # StudySession has subject FK
                StudySession.objects.filter(subject=dup).update(subject=canonical)
                # StudentExamSettings has subject FK
                StudentExamSettings.objects.filter(subject=dup).update(subject=canonical)
                # (Add other reassignments here if needed)
                deleted_ids.append(dup.id)
                dup.delete()
    return changed, deleted_ids

if __name__ == "__main__":
    print("Running subject normalization. Make sure you have a DB backup first.")
    changed, deleted = normalize()
    print("Done.")
    if changed:
        print("Updated subjects:")
        for row in changed:
            print(" ", row)
    if deleted:
        print("Deleted duplicate subject IDs:", deleted)
    else:
        print("No duplicates deleted.")