"""
Parent progress report PDF export.

GET /api/parent/export/<parent_access_token>/pdf/

Generates a plain-text report as a PDF-like text attachment when weasyprint
is not available, or a proper PDF when it is.
"""
import io
import logging
from datetime import date

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from learning.throttles import ParentRateThrottle
from learning.models import StudentExamSettings
from users.models import Student
from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
from decision_engine.v1_0.core import OutlookTier, PerformanceTrend, generate_recommendations
from learning.services.learning_mission import build_learning_mission

logger = logging.getLogger(__name__)


def _build_report_text(student, subject_outlooks) -> str:
    lines = [
        "285IQ GCSE Progress Report",
        "=" * 40,
        f"Student: {student.display_name}",
        f"Generated: {date.today().isoformat()}",
        "",
    ]
    for s in subject_outlooks:
        if "error" in s:
            lines += [f"Subject: {s.get('subject_name', '?')}", f"  Error: {s['error']}", ""]
            continue
        outlook = s.get("outlook", {})
        tier = outlook.get("tier", "")
        tier_str = tier.value if hasattr(tier, "value") else str(tier)
        lines += [
            f"Subject: {s['subject_name']}",
            f"  Exam date:       {s.get('exam_date', 'N/A')}",
            f"  Target grade:    {s.get('target_grade', 'N/A')}",
            f"  Weeks remaining: {s.get('weeks_remaining', 'N/A')}",
            f"  Outlook tier:    {tier_str.replace('_', ' ').title()}",
            f"  Trend:           {outlook.get('trend', 'N/A')}",
            f"  Coverage:        {s.get('activity', {}).get('coverage_breadth', 0)}%",
            f"  Sessions/week:   {s.get('activity', {}).get('sessions_per_week', 0)}",
        ]
        narrative = s.get("parent_narrative")
        if narrative:
            lines.append(f"  Summary: {narrative}")
        recs = s.get("recommendations", [])
        if recs:
            lines.append("  Recommendations:")
            for r in recs:
                lines.append(f"    - {r}")
        lines.append("")
    return "\n".join(lines)


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([ParentRateThrottle])
def parent_export_pdf(request, parent_access_token):
    try:
        student = Student.objects.get(parent_access_token=parent_access_token)
    except Student.DoesNotExist:
        return Response({"error": "Invalid access token"}, status=status.HTTP_404_NOT_FOUND)

    exam_settings = StudentExamSettings.objects.filter(student=student).select_related("subject")
    subject_outlooks = []

    for setting in exam_settings:
        try:
            previous_tier = None
            if setting.last_outlook_tier:
                try:
                    previous_tier = OutlookTier(setting.last_outlook_tier)
                except Exception:
                    pass
            evaluation = evaluate_student_subject(
                student_id=student.id,
                subject_id=setting.subject_id,
                exam_date=setting.exam_date,
                target_grade=setting.target_grade,
                previous_tier=previous_tier,
            )
            mission = build_learning_mission(student, subject_id=setting.subject_id)
            from learning.services.parent_narrative import build_parent_narrative
            narrative = build_parent_narrative(
                subject_name=setting.subject.display_name,
                target_grade=setting.target_grade,
                predicted_grade=mission.get("predicted_grade", setting.target_grade),
                risk_level=mission.get("risk_level", "watch"),
                sessions_per_week=evaluation.get("activity_per_week", 0),
                coverage_breadth=round(evaluation.get("coverage_breadth", 0.0) * 100, 1),
                weak_skills=mission.get("skill_codes", []),
            )
            rec_dict = generate_recommendations(
                attainment_band=evaluation["attainment_band"],
                target_grade=setting.target_grade,
                trend=PerformanceTrend(evaluation["trend"]),
                weeks_remaining=evaluation["weeks_remaining"],
                topic_performances=[],
            )
            recs = [rec_dict.get("message", "")]
            if rec_dict.get("priority_topics"):
                recs.append("Focus: " + ", ".join(str(t) for t in rec_dict["priority_topics"]))
            subject_outlooks.append({
                "subject_name": setting.subject.display_name,
                "exam_date": setting.exam_date.isoformat(),
                "target_grade": setting.target_grade,
                "weeks_remaining": evaluation["weeks_remaining"],
                "outlook": {
                    "tier": evaluation["tier"],
                    "trend": evaluation["trend"],
                },
                "activity": {
                    "sessions_per_week": evaluation["activity_per_week"],
                    "coverage_breadth": round(evaluation.get("coverage_breadth", 0) * 100, 1),
                },
                "parent_narrative": narrative,
                "recommendations": [r for r in recs if r],
            })
        except Exception as exc:
            logger.warning("Export error for subject %s: %s", setting.subject_id, exc)
            subject_outlooks.append({
                "subject_name": setting.subject.display_name,
                "error": str(exc),
            })

    report_text = _build_report_text(student, subject_outlooks)

    # Try weasyprint for real PDF; fall back to plain-text attachment
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=f"<pre style='font-family:monospace'>{report_text}</pre>").write_pdf()
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="285iq_report_{student.username}_{date.today()}.pdf"'
        )
        return response
    except ImportError:
        pass

    response = HttpResponse(report_text, content_type="text/plain")
    response["Content-Disposition"] = (
        f'attachment; filename="285iq_report_{student.username}_{date.today()}.txt"'
    )
    return response
