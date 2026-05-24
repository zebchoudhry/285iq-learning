# Phase 0: Stabilize – Test Checklist

**Purpose:** Establish a known-good baseline for the 285IQ platform.  
**Date:** March 2026

---

## Prerequisites

1. **Start the server**
   ```powershell
   cd 04_platform\django_backend
   python manage.py runserver 127.0.0.1:8000
   ```
2. **Verify migrations**
   ```powershell
   python manage.py migrate
   ```
   Expected: `No migrations to apply`

3. **Current content counts**
   - Subjects: 4 (Mathematics, Biology, Chemistry, Physics)
   - Topics: 28
   - Lessons: 413
   - Questions: 1,648

---

## Full User Journey (End-to-End)

Run through this flow to verify the app works. Check each step.

### 1. Login / Register

| Step | Action | Expected |
|------|--------|----------|
| 1.1 | Open http://127.0.0.1:8000/ | Redirects to login or dashboard (if logged in) |
| 1.2 | Go to http://127.0.0.1:8000/register/ | Registration form loads |
| 1.3 | Register a new account | Redirects to login or dashboard |
| 1.4 | Go to http://127.0.0.1:8000/login/ | Login form loads |
| 1.5 | Log in | Redirects to dashboard or onboarding |

### 2. Onboarding (First-Time User)

| Step | Action | Expected |
|------|--------|----------|
| 2.1 | If no exam settings exist | Redirect to /onboarding/exam-dates/ |
| 2.2 | Submit exam dates (subjects, exam date, target grade) | Redirect to dashboard |
| 2.3 | Dashboard loads | Shows subjects grid, focus areas |

### 3. Dashboard

| Step | Action | Expected |
|------|--------|----------|
| 3.1 | View dashboard (/) | Subject cards load |
| 3.2 | Click a subject card | Navigate to subject detail |
| 3.3 | Sidebar nav | Links to Subjects, Revision Planner, Mock Tests, Flashcards, Settings work |

### 4. Subject Detail

| Step | Action | Expected |
|------|--------|----------|
| 4.1 | Visit /subject/1/ (or any subject ID) | Subject name, topics, completion % load |
| 4.2 | Click "Start Today's Practice" | Navigate to /practice/1/ |
| 4.3 | Topics grid | Each topic has "Continue" link to lessons |

### 5. Practice Session (Flagship Flow)

| Step | Action | Expected |
|------|--------|----------|
| 5.1 | Go to /practice/1/ (Mathematics) | "Loading practice session..." then question loads |
| 5.2 | Answer a question (correct) | "✓ Correct!" + explanation, Next button appears |
| 5.3 | Answer a question (incorrect) | "✗ Incorrect." + static explanation, "Show step-by-step breakdown" button appears |
| 5.4 | Click "Show step-by-step breakdown" | Button shows "Loading...", then AI explanation replaces static OR static re-displays if LLM fails |
| 5.5 | Complete all 6 questions | Summary screen with accuracy, XP, skills improved / needs work |
| 5.6 | Click "Practice Again" | New set of 6 questions loads |

### 6. AI Tutor (Wrong Answer Flow)

| Step | Action | Expected |
|------|--------|----------|
| 6.1 | Get a wrong answer in practice | Static explanation shown immediately |
| 6.2 | Click "Show step-by-step breakdown" | POST to /api/tutor/explain-wrong/ |
| 6.3 | LLM succeeds | AI explanation replaces static text |
| 6.4 | LLM fails (or backend disabled) | Static explanation stays; no crash |

### 7. Lessons

| Step | Action | Expected |
|------|--------|----------|
| 7.1 | Go to /lessons/?subject=1&topic=1 | Lesson content loads |
| 7.2 | Answer lesson questions | Feedback on correct/incorrect |
| 7.3 | Click "Mark Complete" | Lesson marked complete |

### 8. Other Pages (Smoke Test)

| Step | Action | Expected |
|------|--------|----------|
| 8.1 | /subjects/ | Subjects list loads |
| 8.2 | /revision/ | Revision planner loads |
| 8.3 | /mock-tests/ | Mock tests page loads |
| 8.4 | /flashcards/ | Flashcards page loads |
| 8.5 | /settings/ | Settings page loads |

---

## API Endpoints (Quick Reference)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/users/auth/login/ | POST | Login |
| /api/users/auth/register/ | POST | Register |
| /api/revision-summary/ | GET | Exam dates, subject readiness |
| /api/subject/<id>/detail/ | GET | Subject detail, topics |
| /api/practice/start/ | POST | Start 6-question practice |
| /api/quiz/question/<id>/ | GET | Get question for quiz/practice |
| /api/attempts/ | POST | Submit answer |
| /api/tutor/explain-wrong/ | POST | AI wrong-answer explanation |

---

## Known Issues / Notes

- **LLM backend:** If `LLM_BACKEND` is `disabled` or `none`, tutor explain-wrong falls back to `Question.explanation`.
- **Practice URL:** Must use `/practice/<subject_id>/` or `/practice/topic/<topic_id>/`. Direct `/practice/` will show "Invalid practice URL."
- **Onboarding:** New users without `StudentExamSettings` are redirected to `/onboarding/exam-dates/` before dashboard.

---

## What to Fix (Phase 0)

1. **Critical blockers:** Anything that prevents the full journey from completing
2. **500 errors:** Check server logs for exceptions
3. **404s:** Verify URL routes match frontend links
4. **Empty states:** Ensure "No questions" etc. have helpful messages
5. **Console errors:** Check browser dev tools for JS errors

---

## Next: Phase 1

After Phase 0 is complete (no critical blockers, full journey works):

- Phase 1: Polish the flagship flow (Practice + AI tutor)
