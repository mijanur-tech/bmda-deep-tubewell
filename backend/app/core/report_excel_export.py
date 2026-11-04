# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from io import BytesIO

from openpyxl import Workbook
from openpyxl.utils import get_column_letter


# ============================================================
# SECTION 2: ENERGY COLUMN DEFINITIONS
# ============================================================

ENERGY_COLUMNS = [
    ("reading_id", "Reading ID"),
    ("tubewell_id", "Tubewell ID"),
    ("tubewell_number", "Tubewell Number"),
    ("tubewell_name", "Tubewell Name"),
    ("actual_upazila", "Actual Upazila"),
    ("management_unit_id", "Management Unit ID"),
    ("meter_id", "Meter ID"),
    ("meter_number", "Meter Number"),
    ("reading_date", "Reading Date"),
    ("collected_by_user_id", "Collected By User ID"),
    ("collected_by_name", "Collected By"),
    ("previous_reading", "Previous Reading"),
    ("current_reading", "Current Reading"),
    (
        "signed_reading_difference",
        "Signed Reading Difference",
    ),
    (
        "positive_reading_contribution",
        "Positive Reading Contribution",
    ),
    ("l1", "L1"),
    ("l2", "L2"),
    ("l3", "L3"),
    ("zero_confirmed", "Zero Confirmed"),
]


# ============================================================
# SECTION 3: PREPAID COLUMN DEFINITIONS
# ============================================================

PREPAID_COLUMNS = [
    ("reading_id", "Reading ID"),
    ("tubewell_id", "Tubewell ID"),
    ("tubewell_number", "Tubewell Number"),
    ("tubewell_name", "Tubewell Name"),
    ("actual_upazila", "Actual Upazila"),
    ("management_unit_id", "Management Unit ID"),
    ("meter_id", "Meter ID"),
    ("meter_number", "Meter Number"),
    ("reading_date", "Reading Date"),
    ("collected_by_user_id", "Collected By User ID"),
    ("collected_by_name", "Collected By"),
    (
        "prepaid_meter_body_number",
        "Prepaid Meter Body Number",
    ),
    ("previous_reading", "Previous Reading"),
    ("current_reading", "Current Reading"),
    (
        "signed_reading_difference",
        "Signed Reading Difference",
    ),
    (
        "positive_reading_contribution",
        "Positive Reading Contribution",
    ),
    ("previous_money", "Previous Money"),
    ("current_money", "Current Money"),
    (
        "signed_money_difference",
        "Signed Money Difference",
    ),
    (
        "positive_money_contribution",
        "Positive Money Contribution",
    ),
    (
        "previous_time_minutes",
        "Previous Time Minutes",
    ),
    (
        "current_time_minutes",
        "Current Time Minutes",
    ),
    (
        "signed_time_difference_minutes",
        "Signed Time Difference Minutes",
    ),
    (
        "positive_time_contribution_minutes",
        "Positive Time Contribution Minutes",
    ),
    (
        "signed_time_difference_hours",
        "Signed Time Difference Hours",
    ),
    (
        "positive_time_contribution_hours",
        "Positive Time Contribution Hours",
    ),
]


# ============================================================
# SECTION 4: AUTO-SIZE WORKSHEET COLUMNS
# ============================================================

def auto_size_columns(
    worksheet,
) -> None:

    for column_cells in worksheet.columns:

        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:

            value = cell.value

            if value is None:
                continue

            length = len(
                str(value)
            )

            if length > max_length:
                max_length = length

        worksheet.column_dimensions[
            column_letter
        ].width = min(
            max_length + 2,
            40,
        )


# ============================================================
# SECTION 5: WRITE REPORT SHEET
# ============================================================

def write_report_sheet(
    worksheet,
    *,
    title: str,
    rows: list[dict],
    summary: dict,
    columns: list[tuple[str, str]],
) -> None:

    worksheet.title = title

    # --------------------------------------------------------
    # Header row
    # --------------------------------------------------------

    for column_index, (
        field_name,
        display_name,
    ) in enumerate(
        columns,
        start=1,
    ):
        worksheet.cell(
            row=1,
            column=column_index,
            value=display_name,
        )

    # --------------------------------------------------------
    # Data rows
    # --------------------------------------------------------

    for row_index, row_data in enumerate(
        rows,
        start=2,
    ):

        for column_index, (
            field_name,
            _,
        ) in enumerate(
            columns,
            start=1,
        ):

            worksheet.cell(
                row=row_index,
                column=column_index,
                value=row_data.get(
                    field_name
                ),
            )

    # --------------------------------------------------------
    # Summary section
    # --------------------------------------------------------

    summary_start_row = (
        len(rows) + 4
    )

    worksheet.cell(
        row=summary_start_row,
        column=1,
        value="Summary",
    )

    summary_row = (
        summary_start_row + 1
    )

    for key, value in summary.items():

        worksheet.cell(
            row=summary_row,
            column=1,
            value=key,
        )

        worksheet.cell(
            row=summary_row,
            column=2,
            value=value,
        )

        summary_row += 1

    # --------------------------------------------------------
    # Freeze header
    # --------------------------------------------------------

    worksheet.freeze_panes = "A2"

    # --------------------------------------------------------
    # Auto filter
    # --------------------------------------------------------

    if columns:
        worksheet.auto_filter.ref = (
            f"A1:"
            f"{get_column_letter(len(columns))}"
            f"{max(len(rows) + 1, 1)}"
        )

    auto_size_columns(
        worksheet
    )


# ============================================================
# SECTION 6: EXPORT ENERGY REPORT
# ============================================================

def export_energy_report_excel(
    report: dict,
) -> bytes:

    workbook = Workbook()

    worksheet = workbook.active

    write_report_sheet(
        worksheet,
        title="Energy",
        rows=report["rows"],
        summary=report["summary"],
        columns=ENERGY_COLUMNS,
    )

    output = BytesIO()

    workbook.save(
        output
    )

    return output.getvalue()


# ============================================================
# SECTION 7: EXPORT PREPAID REPORT
# ============================================================

def export_prepaid_report_excel(
    report: dict,
) -> bytes:

    workbook = Workbook()

    worksheet = workbook.active

    write_report_sheet(
        worksheet,
        title="Prepaid",
        rows=report["rows"],
        summary=report["summary"],
        columns=PREPAID_COLUMNS,
    )

    output = BytesIO()

    workbook.save(
        output
    )

    return output.getvalue()


# ============================================================
# SECTION 8: EXPORT COMBINED REPORT
# ============================================================

def export_combined_report_excel(
    report: dict,
) -> bytes:

    workbook = Workbook()

    energy_sheet = workbook.active

    write_report_sheet(
        energy_sheet,
        title="Energy",
        rows=report["energy"]["rows"],
        summary=report["energy"]["summary"],
        columns=ENERGY_COLUMNS,
    )

    prepaid_sheet = workbook.create_sheet(
        title="Prepaid"
    )

    write_report_sheet(
        prepaid_sheet,
        title="Prepaid",
        rows=report["prepaid"]["rows"],
        summary=report["prepaid"]["summary"],
        columns=PREPAID_COLUMNS,
    )

    output = BytesIO()

    workbook.save(
        output
    )

    return output.getvalue()