# fix_subject_names.py
import os, django, re
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studymate285.settings")
django.setup()

from learning.models import Subject

pattern = re.compile(r'^(?:GCSE\s+){2,}', re.IGNORECASE)
fixed = 0
for s in Subject.objects.all():
    if pattern.match(s.display_name or ""):
        new = re.sub(pattern, "GCSE ", s.display_name).strip()
        print("Fixing:", s.id, "->", s.display_name, "=>", new)
        s.display_name = new
        s.save()
        fixed += 1

print(f"Subjects fixed: {fixed}")