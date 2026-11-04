# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# SECTION 2: ENERGY COLUMN DEFINITIONS
# ============================================================

ENERGY_COLUMNS = [
    ("reading_id", "Reading ID"),
    ("tubewell_number", "Tubewell"),
    ("tubewell_name", "Name"),
    ("actual_upazila", "Upazila"),
    ("meter_number", "Meter"),
    ("reading_date", "Date"),
    ("collected_by_name", "Collected By"),
    ("previous_reading", "Previous"),
    ("current_reading", "Current"),
    (
        "signed_reading_difference",
        "Difference",
    ),
    ("l1", "L1"),
    ("l2", "L2"),
    ("l3", "L3"),
]


# ============================================================
# SECTION 3: PREPAID COLUMN DEFINITIONS
# ============================================================

PREPAID_COLUMNS = [
    ("reading_id", "Reading ID"),
    ("tubewell_number", "Tubewell"),
    ("tubewell_name", "Name"),
    ("actual_upazila", "Upazila"),
    ("meter_number", "Meter"),
    ("reading_date", "Date"),
    (
        "prepaid_meter_body_number",
        "Body No.",
    ),
    ("previous_reading", "Prev Reading"),
    ("current_reading", "Curr Reading"),
    (
        "signed_reading_difference",
        "Reading Diff",
    ),
    ("previous_money", "Prev Money"),
    ("current_money", "Curr Money"),
    (
        "signed_money_difference",
        "Money Diff",
    ),
    (
        "signed_time_difference_minutes",
        "Time Diff Min",
    ),
    (
        "signed_time_difference_hours",
        "Time Diff Hr",
    ),
]


# ============================================================
# SECTION 4: VALUE FORMATTER
# ============================================================

def format_pdf_value(
    value,
) -> str:

    if value is None:
        return ""

    return str(value)


# ============================================================
# SECTION 5: BUILD DATA TABLE
# ============================================================

def build_report_table(
    rows: list[dict],
    columns: list[tuple[str, str]],
) -> Table:

    table_data = [
        [
            display_name
            for _, display_name
            in columns
        ]
    ]

    for row in rows:

        table_data.append(
            [
                format_pdf_value(
                    row.get(field_name)
                )
                for field_name, _
                in columns
            ]
        )

    table = Table(
        table_data,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    return table


# ============================================================
# SECTION 6: BUILD SUMMARY TABLE
# ============================================================

def build_summary_table(
    summary: dict,
) -> Table:

    data = [
        [
            "Summary Item",
            "Value",
        ]
    ]

    for key, value in summary.items():

        data.append(
            [
                key,
                format_pdf_value(
                    value
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            65 * mm,
            45 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    return table


# ============================================================
# SECTION 7: ADD REPORT SECTION
# ============================================================

def add_report_section(
    story: list,
    *,
    title: str,
    rows: list[dict],
    summary: dict,
    columns: list[tuple[str, str]],
) -> None:

    styles = getSampleStyleSheet()

    story.append(
        Paragraph(
            title,
            styles["Heading1"],
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    if rows:

        story.append(
            build_report_table(
                rows,
                columns,
            )
        )

    else:

        story.append(
            Paragraph(
                "No records found.",
                styles["Normal"],
            )
        )

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    story.append(
        build_summary_table(
            summary
        )
    )


# ============================================================
# SECTION 8: BUILD PDF DOCUMENT
# ============================================================

def build_pdf_document(
    story: list,
) -> bytes:

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title="BMDA Report",
    )

    document.build(
        story
    )

    return output.getvalue()


# ============================================================
# SECTION 9: EXPORT ENERGY PDF
# ============================================================

def export_energy_report_pdf(
    report: dict,
) -> bytes:

    story = []

    add_report_section(
        story,
        title="BMDA Energy Report",
        rows=report["rows"],
        summary=report["summary"],
        columns=ENERGY_COLUMNS,
    )

    return build_pdf_document(
        story
    )


# ============================================================
# SECTION 10: EXPORT PREPAID PDF
# ============================================================

def export_prepaid_report_pdf(
    report: dict,
) -> bytes:

    story = []

    add_report_section(
        story,
        title="BMDA Prepaid Report",
        rows=report["rows"],
        summary=report["summary"],
        columns=PREPAID_COLUMNS,
    )

    return build_pdf_document(
        story
    )


# ============================================================
# SECTION 11: EXPORT COMBINED PDF
# ============================================================

def export_combined_report_pdf(
    report: dict,
) -> bytes:

    story = []

    add_report_section(
        story,
        title="BMDA Energy Report",
        rows=report["energy"]["rows"],
        summary=report["energy"]["summary"],
        columns=ENERGY_COLUMNS,
    )

    story.append(
        PageBreak()
    )

    add_report_section(
        story,
        title="BMDA Prepaid Report",
        rows=report["prepaid"]["rows"],
        summary=report["prepaid"]["summary"],
        columns=PREPAID_COLUMNS,
    )

    return build_pdf_document(
        story
    )