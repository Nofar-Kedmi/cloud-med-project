"""Prescription PDF generation with ReportLab."""

from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


MARGIN = 0.75 * inch
CONTENT_WIDTH = letter[0] - (2 * MARGIN)

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"

COLOR_PRIMARY = colors.HexColor("#1e3a5f")
COLOR_TEXT = colors.HexColor("#1e293b")
COLOR_MUTED = colors.HexColor("#64748b")
COLOR_LINE = colors.HexColor("#cbd5e1")
COLOR_BOX_FILL = colors.HexColor("#f8fafc")
COLOR_BOX_BORDER = colors.HexColor("#94a3b8")
COLOR_ACCENT = colors.HexColor("#2563eb")


def _medical_center_name() -> str:
    return os.environ.get("MEDICAL_CENTER_NAME", "Medical Center").strip() or "Medical Center"


def _visit_date_label(visit: Any) -> str:
    if visit.visit_date:
        if isinstance(visit.visit_date, datetime):
            return visit.visit_date.strftime("%B %d, %Y")
        return str(visit.visit_date)
    return "N/A"


def _patient_dob(patient: Any) -> str:
    dob = getattr(patient, "date_of_birth", None)
    if dob and hasattr(dob, "strftime"):
        return dob.strftime("%B %d, %Y")
    return "—"


def _wrap_lines(
    text: str,
    pdf: canvas.Canvas,
    font: str,
    size: int,
    max_width: float,
) -> list[str]:
    words = (text or "—").split()
    if not words:
        return ["—"]

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if pdf.stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_horizontal_rule(pdf: canvas.Canvas, y: float) -> float:
    pdf.setStrokeColor(COLOR_LINE)
    pdf.setLineWidth(1)
    pdf.line(MARGIN, y, letter[0] - MARGIN, y)
    return y - 14


def _draw_section_heading(pdf: canvas.Canvas, y: float, title: str) -> float:
    pdf.setFillColor(COLOR_PRIMARY)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawString(MARGIN, y, title.upper())
    return y - 18


def _draw_label_value(
    pdf: canvas.Canvas,
    y: float,
    label: str,
    value: str,
    *,
    label_x: float | None = None,
    value_x: float | None = None,
) -> float:
    label_x = label_x if label_x is not None else MARGIN
    value_x = value_x if value_x is not None else MARGIN + 118

    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(label_x, y, label)

    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont(FONT_REGULAR, 10)
    pdf.drawString(value_x, y, value or "—")
    return y - 15


def _draw_text_block(
    pdf: canvas.Canvas,
    y: float,
    lines: list[str],
    *,
    font: str = FONT_REGULAR,
    size: int = 10,
    leading: int = 14,
    color: colors.Color = COLOR_TEXT,
) -> float:
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    for line in lines:
        pdf.drawString(MARGIN + 12, y, line)
        y -= leading
    return y


def _draw_highlight_box(
    pdf: canvas.Canvas,
    y: float,
    title: str,
    body_lines: list[str],
    *,
    min_height: float = 72,
) -> float:
    leading = 14
    padding = 12
    content_height = max(min_height, 28 + len(body_lines) * leading)
    box_bottom = y - content_height

    pdf.setFillColor(COLOR_BOX_FILL)
    pdf.setStrokeColor(COLOR_BOX_BORDER)
    pdf.setLineWidth(0.8)
    pdf.roundRect(MARGIN, box_bottom, CONTENT_WIDTH, content_height, 6, fill=1, stroke=1)

    pdf.setFillColor(COLOR_PRIMARY)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(MARGIN + padding, y - 18, title)

    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont(FONT_REGULAR, 10)
    text_y = y - 34
    for line in body_lines:
        pdf.drawString(MARGIN + padding, text_y, line)
        text_y -= leading

    return box_bottom - 16


def _draw_validity_box(pdf: canvas.Canvas, y: float, prescription_id: str) -> float:
    box_height = 52
    box_bottom = y - box_height

    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(COLOR_ACCENT)
    pdf.setLineWidth(1.2)
    pdf.roundRect(MARGIN, box_bottom, CONTENT_WIDTH, box_height, 6, fill=1, stroke=1)

    pdf.setFillColor(COLOR_ACCENT)
    pdf.setFont(FONT_BOLD, 11)
    pdf.drawCentredString(letter[0] / 2, y - 22, "Valid for collection at HMO / Pharmacy")

    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawCentredString(
        letter[0] / 2,
        y - 38,
        f"Prescription reference: {prescription_id}",
    )

    return box_bottom - 22


def _draw_signature_block(pdf: canvas.Canvas, y: float, doctor_name: str) -> float:
    pdf.setFillColor(COLOR_PRIMARY)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(MARGIN, y, "Doctor's Signature")

    line_y = y - 28
    pdf.setStrokeColor(COLOR_TEXT)
    pdf.setLineWidth(0.6)
    pdf.line(MARGIN, line_y, MARGIN + 3.2 * inch, line_y)

    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont(FONT_ITALIC, 9)
    pdf.drawString(MARGIN, line_y - 14, doctor_name or "Authorized prescriber")

    issued_x = letter[0] - MARGIN - 2.4 * inch
    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(issued_x, y, "Date Issued")
    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawString(issued_x, y - 14, datetime.now().strftime("%B %d, %Y"))

    return line_y - 28


def _sanitize_name_part(value: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", (value or "").strip(), flags=re.UNICODE)
    cleaned = re.sub(r"[\s-]+", "_", cleaned)
    return cleaned.strip("_")


def build_prescription_filename(patient: Any, prescription: Any) -> str:
    """Build filename like YONI_JON_prescription.pdf."""
    name_parts = [
        _sanitize_name_part(getattr(patient, "first_name", "")),
        _sanitize_name_part(getattr(patient, "last_name", "")),
    ]
    name_parts = [part.upper() for part in name_parts if part]

    if name_parts:
        return f"{'_'.join(name_parts)}_prescription.pdf"

    rx_id = getattr(prescription, "prescription_id", "PRESCRIPTION")
    return f"{_sanitize_name_part(rx_id).upper() or 'PRESCRIPTION'}_prescription.pdf"


def generate_prescription_pdf(
    visit,
    prescription,
    patient,
    doctor_name: str = "",
    doctor_license_number: str = "",
) -> tuple[str, str]:
    """
    Generate a prescription PDF and return (filepath, filename).
    Caller is responsible for deleting the temp file after upload.
    """
    filename = build_prescription_filename(patient, prescription)
    tmp_dir = Path(tempfile.gettempdir())
    filepath = str(tmp_dir / f"{prescription.prescription_id}_{filename}")

    pdf = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - MARGIN

    center_name = _medical_center_name()
    license_number = doctor_license_number.strip() or "—"
    instructions = prescription.instructions or prescription.general_instructions or "—"

    # Header band
    header_height = 56
    pdf.setFillColor(COLOR_PRIMARY)
    pdf.rect(0, y - header_height + 8, width, header_height, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont(FONT_BOLD, 22)
    pdf.drawString(MARGIN, y - 18, center_name)

    pdf.setFont(FONT_REGULAR, 11)
    pdf.drawString(MARGIN, y - 36, "Official Prescription Document")

    pdf.setFont(FONT_REGULAR, 9)
    pdf.drawRightString(width - MARGIN, y - 18, f"Rx No. {prescription.prescription_id}")
    pdf.drawRightString(width - MARGIN, y - 32, f"Visit No. {visit.visit_id}")

    y -= header_height + 18

    # Doctor information
    y = _draw_section_heading(pdf, y, "Prescribing Physician")
    y = _draw_label_value(pdf, y, "Doctor's Name:", doctor_name or "—")
    y = _draw_label_value(pdf, y, "License Number:", license_number)
    y = _draw_label_value(pdf, y, "Issue Date:", _visit_date_label(visit))
    y = _draw_horizontal_rule(pdf, y)

    # Patient information
    y = _draw_section_heading(pdf, y, "Patient Information")
    y = _draw_label_value(
        pdf,
        y,
        "Patient Name:",
        f"{patient.first_name} {patient.last_name}".strip(),
    )
    y = _draw_label_value(pdf, y, "Patient ID:", patient.patient_id)
    if getattr(patient, "id_number", ""):
        y = _draw_label_value(pdf, y, "ID Number:", patient.id_number)
    y = _draw_label_value(pdf, y, "Date of Birth:", _patient_dob(patient))
    y = _draw_horizontal_rule(pdf, y)

    # Clinical summary
    y = _draw_section_heading(pdf, y, "Clinical Summary")
    y = _draw_label_value(pdf, y, "Diagnosis:", visit.diagnosis or "—")
    diagnosis_y = y
    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont(FONT_BOLD, 10)
    pdf.drawString(MARGIN, diagnosis_y, "Symptoms:")
    symptom_lines = _wrap_lines(visit.symptoms or "—", pdf, FONT_REGULAR, 10, CONTENT_WIDTH - 130)
    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont(FONT_REGULAR, 10)
    symptom_y = diagnosis_y
    for line in symptom_lines[:3]:
        pdf.drawString(MARGIN + 118, symptom_y, line)
        symptom_y -= 14
    y = symptom_y - 6
    y = _draw_horizontal_rule(pdf, y)

    # Medication details
    y = _draw_section_heading(pdf, y, "Medication Details")
    y = _draw_label_value(pdf, y, "Medication:", prescription.medication_name or "—")
    y = _draw_label_value(pdf, y, "Dosage:", prescription.dosage or "—")
    y = _draw_label_value(pdf, y, "Frequency:", prescription.frequency or "—")
    y = _draw_horizontal_rule(pdf, y)

    # Usage instructions (highlighted)
    instruction_lines = _wrap_lines(instructions, pdf, FONT_REGULAR, 10, CONTENT_WIDTH - 28)
    y = _draw_highlight_box(
        pdf,
        y,
        "Usage Instructions",
        instruction_lines,
        min_height=56 + max(0, len(instruction_lines) - 2) * 14,
    )

    # Pharmacy validity
    y = _draw_validity_box(pdf, y, prescription.prescription_id)

    # Signature
    _draw_signature_block(pdf, y, doctor_name)

    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawCentredString(
        width / 2,
        0.45 * inch,
        f"This document was generated electronically by {center_name}.",
    )

    pdf.save()
    return filepath, filename
