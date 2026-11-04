# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.report_calculation import (
    calculate_decimal_totals,
    calculate_positive_contribution,
    calculate_positive_time_contribution,
    calculate_signed_difference,
    calculate_signed_time_difference,
    calculate_time_totals,
    minutes_to_hours,
)

from app.core.report_scope_management import (
    get_report_scope_condition,
)

from app.models.meter import Meter
from app.models.reading import Reading
from app.models.tubewell import Tubewell
from app.models.user import User


# ============================================================
# SECTION 2: PREPAID REPORT QUERY
# ============================================================

def get_prepaid_report_rows(
    db: Session,
    *,
    current_user: User,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise ValueError(
            "Start date cannot be after end date."
        )

    # --------------------------------------------------------
    # Build role-based scope.
    # Admin returns None for global access.
    # --------------------------------------------------------

    scope_condition = (
        get_report_scope_condition(
            current_user
        )
    )

    query = (
        select(
            Reading,
            Tubewell,
            User,
            Meter,
        )
        .join(
            Tubewell,
            Tubewell.id
            == Reading.tubewell_id,
        )
        .join(
            User,
            User.id
            == Reading.collected_by_user_id,
        )
        .outerjoin(
            Meter,
            Meter.id
            == Reading.meter_id,
        )
        .where(
            Reading.reading_type
            == "prepaid"
        )
    )

    # --------------------------------------------------------
    # Apply role scope except for Admin global access.
    # --------------------------------------------------------

    if scope_condition is not None:
        query = query.where(
            scope_condition
        )

    # --------------------------------------------------------
    # Optional date filters.
    # --------------------------------------------------------

    if start_date is not None:
        query = query.where(
            Reading.reading_date
            >= start_date
        )

    if end_date is not None:
        query = query.where(
            Reading.reading_date
            <= end_date
        )

    query = query.order_by(
        Reading.reading_date.desc(),
        Reading.id.desc(),
    )

    records = db.execute(
        query
    ).all()

    rows = []

    for (
        reading,
        tubewell,
        collector,
        meter,
    ) in records:

        signed_reading_difference = (
            calculate_signed_difference(
                reading.previous_reading,
                reading.current_reading,
            )
        )

        positive_reading_contribution = (
            calculate_positive_contribution(
                signed_reading_difference
            )
        )

        signed_money_difference = (
            calculate_signed_difference(
                reading.previous_money,
                reading.current_money,
            )
        )

        positive_money_contribution = (
            calculate_positive_contribution(
                signed_money_difference
            )
        )

        signed_time_difference_minutes = (
            calculate_signed_time_difference(
                reading.previous_time_minutes,
                reading.current_time_minutes,
            )
        )

        positive_time_contribution_minutes = (
            calculate_positive_time_contribution(
                signed_time_difference_minutes
            )
        )

        signed_time_difference_hours = (
            minutes_to_hours(
                signed_time_difference_minutes
            )
        )

        positive_time_contribution_hours = (
            minutes_to_hours(
                positive_time_contribution_minutes
            )
        )

        rows.append(
            {
                "reading_id":
                    reading.id,

                "tubewell_id":
                    tubewell.id,

                "tubewell_number":
                    tubewell.tubewell_number,

                "tubewell_name":
                    tubewell.name,

                "actual_upazila":
                    tubewell.actual_upazila,

                "management_unit_id":
                    tubewell.management_unit_id,

                "meter_id":
                    reading.meter_id,

                "meter_number":
                    (
                        meter.meter_number
                        if meter is not None
                        else None
                    ),

                "reading_date":
                    reading.reading_date,

                "collected_by_user_id":
                    collector.id,

                "collected_by_name":
                    collector.full_name,

                "reading_type":
                    "prepaid",

                "previous_reading":
                    reading.previous_reading,

                "current_reading":
                    reading.current_reading,

                "signed_reading_difference":
                    signed_reading_difference,

                "positive_reading_contribution":
                    positive_reading_contribution,

                "prepaid_meter_body_number":
                    reading.prepaid_meter_body_number,

                "previous_money":
                    reading.previous_money,

                "current_money":
                    reading.current_money,

                "signed_money_difference":
                    signed_money_difference,

                "positive_money_contribution":
                    positive_money_contribution,

                "previous_time_minutes":
                    reading.previous_time_minutes,

                "current_time_minutes":
                    reading.current_time_minutes,

                "signed_time_difference_minutes":
                    signed_time_difference_minutes,

                "positive_time_contribution_minutes":
                    positive_time_contribution_minutes,

                "signed_time_difference_hours":
                    signed_time_difference_hours,

                "positive_time_contribution_hours":
                    positive_time_contribution_hours,
            }
        )

    return rows


# ============================================================
# SECTION 3: PREPAID REPORT SUMMARY
# ============================================================

def build_prepaid_report_summary(
    rows: list[dict],
) -> dict:

    reading_totals = (
        calculate_decimal_totals(
            [
                row[
                    "signed_reading_difference"
                ]
                for row in rows
            ]
        )
    )

    money_totals = (
        calculate_decimal_totals(
            [
                row[
                    "signed_money_difference"
                ]
                for row in rows
            ]
        )
    )

    time_totals = (
        calculate_time_totals(
            [
                row[
                    "signed_time_difference_minutes"
                ]
                for row in rows
            ]
        )
    )

    return {
        "total_records":
            len(rows),

        "positive_reading_total":
            reading_totals[
                "positive_total"
            ],

        "negative_reading_total":
            reading_totals[
                "negative_total"
            ],

        "net_reading_total":
            reading_totals[
                "net_total"
            ],

        "positive_money_total":
            money_totals[
                "positive_total"
            ],

        "negative_money_total":
            money_totals[
                "negative_total"
            ],

        "net_money_total":
            money_totals[
                "net_total"
            ],

        "positive_time_minutes_total":
            time_totals[
                "positive_total"
            ],

        "negative_time_minutes_total":
            time_totals[
                "negative_total"
            ],

        "net_time_minutes_total":
            time_totals[
                "net_total"
            ],
    }


# ============================================================
# SECTION 4: COMPLETE PREPAID REPORT
# ============================================================

def get_prepaid_report(
    db: Session,
    *,
    current_user: User,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:

    rows = get_prepaid_report_rows(
        db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )

    summary = (
        build_prepaid_report_summary(
            rows
        )
    )

    return {
        "report_type":
            "prepaid",

        "rows":
            rows,

        "summary":
            summary,
    }