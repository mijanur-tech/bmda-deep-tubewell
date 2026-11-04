# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.report_calculation import (
    calculate_decimal_totals,
    calculate_positive_contribution,
    calculate_signed_difference,
)

from app.core.report_scope_management import (
    get_report_scope_condition,
)

from app.models.meter import Meter
from app.models.reading import Reading
from app.models.tubewell import Tubewell
from app.models.user import User


# ============================================================
# SECTION 2: ENERGY REPORT QUERY
# ============================================================

def get_energy_report_rows(
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
            == "energy"
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

        signed_difference = (
            calculate_signed_difference(
                reading.previous_reading,
                reading.current_reading,
            )
        )

        positive_contribution = (
            calculate_positive_contribution(
                signed_difference
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
                    "energy",

                "previous_reading":
                    reading.previous_reading,

                "current_reading":
                    reading.current_reading,

                "signed_reading_difference":
                    signed_difference,

                "positive_reading_contribution":
                    positive_contribution,

                "l1":
                    reading.l1,

                "l2":
                    reading.l2,

                "l3":
                    reading.l3,

                "zero_confirmed":
                    reading.zero_confirmed,
            }
        )

    return rows


# ============================================================
# SECTION 3: ENERGY REPORT SUMMARY
# ============================================================

def build_energy_report_summary(
    rows: list[dict],
) -> dict:

    signed_values = [
        row[
            "signed_reading_difference"
        ]
        for row in rows
    ]

    totals = calculate_decimal_totals(
        signed_values
    )

    return {
        "total_records":
            len(rows),

        "positive_reading_total":
            totals[
                "positive_total"
            ],

        "negative_reading_total":
            totals[
                "negative_total"
            ],

        "net_reading_total":
            totals[
                "net_total"
            ],
    }


# ============================================================
# SECTION 4: COMPLETE ENERGY REPORT
# ============================================================

def get_energy_report(
    db: Session,
    *,
    current_user: User,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:

    rows = get_energy_report_rows(
        db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )

    summary = (
        build_energy_report_summary(
            rows
        )
    )

    return {
        "report_type":
            "energy",

        "rows":
            rows,

        "summary":
            summary,
    }