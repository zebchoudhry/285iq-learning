# 285IQ Content Workflow

Content is the main product. Treat every lesson, question, video, flashcard, and mock exam as a source-controlled asset with a clear audit trail.

## What Good Looks Like

- Each topic has short lesson text, worked examples, exam-style questions, flashcards, and at least one short intervention video.
- Each subject has timed mock exams built from fixed question sets.
- Every exam-style question has marks, an answer, explanation, marking guidance, difficulty, and a source/provenance note.
- Past-paper questions should only be used where licensing allows it. Otherwise store original questions inspired by specification coverage, and link to official papers separately.

## Current Import Commands

Run the content audit:

```cmd
venv\Scripts\python.exe manage.py content_audit
```

Import question JSON:

```cmd
venv\Scripts\python.exe manage.py load_questions --file data\questions_mathematics_generated.json
```

Import skill videos from CSV:

```cmd
venv\Scripts\python.exe manage.py import_skill_videos --file data\skill_videos_template.csv
```

Dry-run first when adding new content:

```cmd
venv\Scripts\python.exe manage.py import_skill_videos --file data\skill_videos_template.csv --dry-run
```

Seed official past-paper links:

```cmd
venv\Scripts\python.exe manage.py seed_past_papers
```

## Commercial Content Targets

- Launch wedge: one brilliant subject first, preferably GCSE Mathematics.
- Minimum for a paid beta: 200 lessons, 2,000 verified questions, 100 videos, 500 flashcards, 6 timed mock exams, and parent/student progress reporting.
- Minimum for all four core subjects: 600 lessons, 8,000 verified questions, 400 videos, 2,000 flashcards, and 24 timed mock exams.

## Content QA Checklist

- Question text is unambiguous.
- Answer can be marked reliably by the app.
- Explanation teaches the exact misconception.
- Marking scheme matches the marks available.
- Difficulty is realistic for GCSE tier.
- Topic and lesson mapping is correct.
- Source/provenance is filled in.
- Video link is live and relevant.
- No copyrighted past-paper text is copied without permission.
