# 285IQ – Quick Start

**Phase 0 baseline.** Use this to run and verify the app.

---

## 1. Start the server

```powershell
cd 04_platform\django_backend
python manage.py runserver 127.0.0.1:8000
```

Server runs at: **http://127.0.0.1:8000/**

---

## 2. First-time setup

```powershell
python manage.py migrate
```

If you need to add content:

```powershell
python manage.py bootstrap_gcse
```

(Content already seeded: 4 subjects, 28 topics, 413 lessons, 1,648 questions.)

---

## 3. Create a user (if needed)

```powershell
python manage.py createsuperuser
```

Or register at: http://127.0.0.1:8000/register/

---

## 4. Test the flagship flow

1. **Login** → http://127.0.0.1:8000/login/
2. **Onboarding** (if new) → Set exam dates at /onboarding/exam-dates/
3. **Dashboard** → http://127.0.0.1:8000/
4. **Subjects** → Click a subject card or go to /subjects/
5. **Subject detail** → Click subject → "Start Today's Practice"
6. **Practice** → Answer 6 questions; try a wrong answer and click **Show step-by-step breakdown**
7. **Summary** → See accuracy, XP, skills improved / needs work

---

## 5. Full test checklist

See [PHASE_0_CHECKLIST.md](PHASE_0_CHECKLIST.md) for the complete manual test flow.
