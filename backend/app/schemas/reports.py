# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


# ============================================================
# SECTION 2: COMMON REPORT ROW
# ============================================================

class BaseReadingReportRow(BaseModel):

    reading_id: int

    tubewell_id: int

    tubewell_number: str

    tubewell_name: str

    actual_upazila: str

    management_unit_id: int

    meter_id: int | None = None

    meter_number: str | None = None

    reading_date: date

    collected_by_user_id: int

    collected_by_name: str

    reading_type: Literal[
        "energy",
        "prepaid",
    ]

    previous_reading: Decimal

    current_reading: Decimal

    signed_reading_difference: Decimal

    positive_reading_contribution: Decimal


# ============================================================
# SECTION 3: ENERGY REPORT ROW
# ============================================================

class EnergyReportRow(
    BaseReadingReportRow
):

    reading_type: Literal[
        "energy"
    ] = "energy"

    l1: Decimal

    l2: Decimal

    l3: Decimal

    zero_confirmed: bool


# ============================================================
# SECTION 4: PREPAID REPORT ROW
# ============================================================

class PrepaidReportRow(
    BaseReadingReportRow
):

    reading_type: Literal[
        "prepaid"
    ] = "prepaid"

    prepaid_meter_body_number: str

    previous_money: Decimal

    current_money: Decimal

    signed_money_difference: Decimal

    positive_money_contribution: Decimal

    previous_time_minutes: int

    current_time_minutes: int

    signed_time_difference_minutes: int

    positive_time_contribution_minutes: int

    signed_time_difference_hours: Decimal

    positive_time_contribution_hours: Decimal


# ============================================================
# SECTION 5: ENERGY REPORT SUMMARY
# ============================================================

class EnergyReportSummary(BaseModel):

    total_records: int

    positive_reading_total: Decimal

    negative_reading_total: Decimal

    net_reading_total: Decimal


# ============================================================
# SECTION 6: PREPAID REPORT SUMMARY
# ============================================================

class PrepaidReportSummary(BaseModel):

    total_records: int

    positive_reading_total: Decimal

    negative_reading_total: Decimal

    net_reading_total: Decimal

    positive_money_total: Decimal

    negative_money_total: Decimal

    net_money_total: Decimal

    positive_time_minutes_total: int

    negative_time_minutes_total: int

    net_time_minutes_total: int


# ============================================================
# SECTION 7: ENERGY REPORT RESPONSE
# ============================================================

class EnergyReportResponse(BaseModel):

    report_type: Literal[
        "energy"
    ] = "energy"

    rows: list[
        EnergyReportRow
    ]

    summary: EnergyReportSummary


# ============================================================
# SECTION 8: PREPAID REPORT RESPONSE
# ============================================================

class PrepaidReportResponse(BaseModel):

    report_type: Literal[
        "prepaid"
    ] = "prepaid"

    rows: list[
        PrepaidReportRow
    ]

    summary: PrepaidReportSummary


# ============================================================
# SECTION 9: COMBINED REPORT RESPONSE
# ============================================================

class CombinedReportResponse(BaseModel):

    report_type: Literal[
        "combined"
    ] = "combined"

    energy: EnergyReportResponse

    prepaid: PrepaidReportResponse