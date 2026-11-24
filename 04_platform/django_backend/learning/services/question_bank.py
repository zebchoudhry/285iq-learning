"""
Hand-written question banks.

Questions are written in plain text files that are easy to read, review and edit, one per
topic, under question_bank/<subject>/. Format:

    topic: Cell Biology
    lesson: 1.1 - Cell Structure
    MC | difficulty | question | correct answer | wrong 1 | wrong 2 | wrong 3 | explanation
    SA | difficulty | question | answer | explanation

    // lines starting with // and blank lines are ignored

MC is multiple choice. The correct answer is written first and is shuffled when loaded.
SA is a short answer, which the app grades by matching, so the answer must be one short
term or number (no lists, no "or", no commas). Every question is worth 1 mark.
"""
import hashlib
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

SOURCE_PREFIX = "Written for 285IQ"
MAX_TEXT, MAX_OPTION, MAX_ANSWER_WORDS = 320, 150, 5
BAD_OPTIONS = ("all of the above", "none of the above", "both a and b", "all of these", "none of these")


@dataclass
class WrittenQuestion:
    kind: str                  # "MC" or "SA"
    difficulty: int
    text: str
    answer: str
    wrong: List[str]
    explanation: str
    topic: str
    lesson: str
    path: str
    line: int

    def options(self) -> List[dict]:
        """Options in a stable shuffled order, so the correct answer isn't always first."""
        seed = int(hashlib.sha1(self.text.encode("utf-8")).hexdigest()[:8], 16)
        opts = [{"text": self.answer, "correct": True}] + [{"text": w, "correct": False} for w in self.wrong]
        random.Random(seed).shuffle(opts)
        return opts

    def as_dict(self, source: str) -> dict:
        d = {
            "question_text": self.text,
            "correct_answer": self.answer,
            "difficulty_level": self.difficulty,
            "marks_available": 1,
            "explanation": self.explanation,
            "source": source,
        }
        if self.kind == "MC":
            d.update(question_type="multiple_choice", options=self.options())
        else:
            d["question_type"] = "short_answer"
        return d


@dataclass
class ParseResult:
    questions: List[WrittenQuestion] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _problem(q: WrittenQuestion) -> List[str]:
    out = []
    if not 1 <= q.difficulty <= 5:
        out.append("difficulty must be 1 to 5")
    if len(q.text) < 10 or len(q.text) > MAX_TEXT:
        out.append(f"question must be 10 to {MAX_TEXT} characters")
    if len(q.explanation) < 15:
        out.append("explanation is missing or too short")
    if not q.answer:
        out.append("answer is empty")
    if q.kind == "MC":
        options = [q.answer] + q.wrong
        if len(q.wrong) != 3:
            out.append("a multiple choice question needs exactly 3 wrong answers")
        if any(not o or len(o) > MAX_OPTION for o in options):
            out.append(f"every option must be 1 to {MAX_OPTION} characters")
        if len({o.strip().lower() for o in options}) != len(options):
            out.append("options must all be different")
        if any(o.strip().lower().rstrip(".") in BAD_OPTIONS for o in options):
            out.append("'all/none of the above' options are not allowed")
    else:
        words = q.answer.split()
        if len(words) > MAX_ANSWER_WORDS:
            out.append(f"a short answer must be at most {MAX_ANSWER_WORDS} words")
        if re.search(r"[,;]|\sor\s|\sand\s|/", q.answer.lower()) and not re.fullmatch(r"[\d.,]+", q.answer):
            out.append("a short answer must be a single term (no lists, commas, 'or', 'and' or '/')")
    return out


def parse_file(path: Path) -> ParseResult:
    result = ParseResult()
    topic = lesson = ""
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        where = f"{path.name}:{number}"
        if line.lower().startswith("topic:"):
            topic = line.split(":", 1)[1].strip()
            continue
        if line.lower().startswith("lesson:"):
            lesson = line.split(":", 1)[1].strip()
            continue
        parts = [p.strip() for p in line.split("|")]
        kind = parts[0].upper()
        if kind not in ("MC", "SA"):
            result.errors.append(f"{where}: line must start with MC, SA, topic: or lesson:")
            continue
        if not topic or not lesson:
            result.errors.append(f"{where}: question appears before a topic: and lesson: line")
            continue
        need = 8 if kind == "MC" else 5
        if len(parts) != need:
            result.errors.append(f"{where}: {kind} needs {need} fields separated by |, found {len(parts)}")
            continue
        try:
            difficulty = int(parts[1])
        except ValueError:
            result.errors.append(f"{where}: difficulty must be a number")
            continue
        if kind == "MC":
            text, answer, wrong, explanation = parts[2], parts[3], parts[4:7], parts[7]
        else:
            text, answer, wrong, explanation = parts[2], parts[3], [], parts[4]
        q = WrittenQuestion(kind, difficulty, text, answer, wrong, explanation, topic, lesson, str(path), number)
        for problem in _problem(q):
            result.errors.append(f"{where}: {problem}")
        result.questions.append(q)
    return result


def parse_directory(directory: Path) -> ParseResult:
    total = ParseResult()
    for path in sorted(Path(directory).glob("*.txt")):
        part = parse_file(path)
        total.questions += part.questions
        total.errors += part.errors
    seen: Dict[str, str] = {}
    for q in total.questions:
        key = q.text.strip().lower()
        if key in seen:
            total.errors.append(f"{Path(q.path).name}:{q.line}: duplicate of the question at {seen[key]}")
        else:
            seen[key] = f"{Path(q.path).name}:{q.line}"
    return total


def lessons_in(questions: List[WrittenQuestion]) -> Dict[Tuple[str, str], List[WrittenQuestion]]:
    grouped: Dict[Tuple[str, str], List[WrittenQuestion]] = {}
    for q in questions:
        grouped.setdefault((q.topic, q.lesson), []).append(q)
    return grouped


def review_markdown(questions: List[WrittenQuestion], title: str) -> str:
    """A readable document for checking the questions before they are loaded."""
    out = [f"# {title}", "", f"{len(questions)} questions. The correct answer is marked ✓.", ""]
    current_topic = current_lesson = None
    for q in questions:
        if q.topic != current_topic:
            out += [f"## {q.topic}", ""]
            current_topic, current_lesson = q.topic, None
        if q.lesson != current_lesson:
            out += [f"### {q.lesson}", ""]
            current_lesson = q.lesson
        out.append(f"**{q.text}** *(difficulty {q.difficulty})*")
        if q.kind == "MC":
            out += [f"- {'✓ ' if o['correct'] else ''}{o['text']}" for o in q.options()]
        else:
            out.append(f"- ✓ {q.answer} *(typed answer)*")
        out += [f"- *Why:* {q.explanation}", ""]
    return "\n".join(out)
