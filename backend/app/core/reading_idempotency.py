# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from decimal import Decimal, InvalidOperation


# ============================================================
# SECTION 2: SAFE DECIMAL COMPARISON
# Convert values to Decimal for stable numeric comparison.
# ============================================================

def decimal_values_match(
    first,
    second,
) -> bool:

    try:
        first_decimal = Decimal(
            str(first)
        )

        second_decimal = Decimal(
            str(second)
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return False

    if (
        not first_decimal.is_finite()
        or not second_decimal.is_finite()
    ):
        return False

    return first_decimal == second_decimal


# ============================================================
# SECTION 3: COMMON RETRY IDENTITY
# A repeated client_submission_id must refer to the same:
#
# - reading type
# - tubewell
# - meter
# - Field User
# ============================================================

def validate_idempotent_retry_identity(
    existing_reading,
    *,
    reading_type: str,
    tubewell_id: int,
    meter_id: int | None,
    collected_by_user_id: int,
) -> bool:

    if (
        existing_reading.reading_type
        != reading_type
    ):
        return False

    if (
        existing_reading.tubewell_id
        != tubewell_id
    ):
        return False

    if (
        existing_reading.collected_by_user_id
        != collected_by_user_id
    ):
        return False

    if (
        existing_reading.meter_id
        != meter_id
    ):
        return False

    return True


# ============================================================
# SECTION 4: REQUIRE COMMON RETRY IDENTITY
# ============================================================

def require_idempotent_retry_identity(
    existing_reading,
    *,
    reading_type: str,
    tubewell_id: int,
    meter_id: int | None,
    collected_by_user_id: int,
) -> None:

    if not validate_idempotent_retry_identity(
        existing_reading,
        reading_type=reading_type,
        tubewell_id=tubewell_id,
        meter_id=meter_id,
        collected_by_user_id=collected_by_user_id,
    ):
        raise ValueError(
            "Client submission ID is already used "
            "for a different reading submission."
        )


# ============================================================
# SECTION 5: ENERGY RETRY PAYLOAD MATCHING
# A valid retry must contain exactly the same stored Energy
# values as the original successful submission.
# ============================================================

def validate_energy_retry_payload(
    existing_reading,
    *,
    reading_date,
    previous_reading,
    current_reading,
    l1,
    l2,
    l3,
    zero_confirmed: bool,
) -> bool:

    if (
        existing_reading.reading_date
        != reading_date
    ):
        return False

    numeric_pairs = (
        (
            existing_reading.previous_reading,
            previous_reading,
        ),
        (
            existing_reading.current_reading,
            current_reading,
        ),
        (
            existing_reading.l1,
            l1,
        ),
        (
            existing_reading.l2,
            l2,
        ),
        (
            existing_reading.l3,
            l3,
        ),
    )

    for stored, submitted in numeric_pairs:

        if not decimal_values_match(
            stored,
            submitted,
        ):
            return False

    if (
        existing_reading.zero_confirmed
        is not zero_confirmed
    ):
        return False

    return True


# ============================================================
# SECTION 6: PREPAID RETRY PAYLOAD MATCHING
# A valid retry must contain exactly the same stored Prepaid
# values as the original successful submission.
# ============================================================

def validate_prepaid_retry_payload(
    existing_reading,
    *,
    reading_date,
    prepaid_meter_body_number: str,
    previous_reading,
    current_reading,
    previous_money,
    current_money,
    previous_time_minutes: int,
    current_time_minutes: int,
) -> bool:

    if (
        existing_reading.reading_date
        != reading_date
    ):
        return False

    if (
        existing_reading.prepaid_meter_body_number
        != prepaid_meter_body_number
    ):
        return False

    numeric_pairs = (
        (
            existing_reading.previous_reading,
            previous_reading,
        ),
        (
            existing_reading.current_reading,
            current_reading,
        ),
        (
            existing_reading.previous_money,
            previous_money,
        ),
        (
            existing_reading.current_money,
            current_money,
        ),
    )

    for stored, submitted in numeric_pairs:

        if not decimal_values_match(
            stored,
            submitted,
        ):
            return False

    if (
        existing_reading.previous_time_minutes
        != previous_time_minutes
    ):
        return False

    if (
        existing_reading.current_time_minutes
        != current_time_minutes
    ):
        return False

    return True


# ============================================================
# SECTION 7: REQUIRE ENERGY RETRY PAYLOAD
# ============================================================

def require_energy_retry_payload(
    existing_reading,
    *,
    reading_date,
    previous_reading,
    current_reading,
    l1,
    l2,
    l3,
    zero_confirmed: bool,
) -> None:

    if not validate_energy_retry_payload(
        existing_reading,
        reading_date=reading_date,
        previous_reading=previous_reading,
        current_reading=current_reading,
        l1=l1,
        l2=l2,
        l3=l3,
        zero_confirmed=zero_confirmed,
    ):
        raise ValueError(
            "Client submission ID already exists "
            "with different Energy reading data."
        )


# ============================================================
# SECTION 8: REQUIRE PREPAID RETRY PAYLOAD
# ============================================================

def require_prepaid_retry_payload(
    existing_reading,
    *,
    reading_date,
    prepaid_meter_body_number: str,
    previous_reading,
    current_reading,
    previous_money,
    current_money,
    previous_time_minutes: int,
    current_time_minutes: int,
) -> None:

    if not validate_prepaid_retry_payload(
        existing_reading,
        reading_date=reading_date,
        prepaid_meter_body_number=(
            prepaid_meter_body_number
        ),
        previous_reading=previous_reading,
        current_reading=current_reading,
        previous_money=previous_money,
        current_money=current_money,
        previous_time_minutes=(
            previous_time_minutes
        ),
        current_time_minutes=(
            current_time_minutes
        ),
    ):
        raise ValueError(
            "Client submission ID already exists "
            "with different Prepaid reading data."
        )