# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.reading_date_validation import (
    validate_reading_date,
)

from app.core.reading_idempotency import (
    require_energy_retry_payload,
    require_idempotent_retry_identity,
    require_prepaid_retry_payload,
)

from app.core.roles import UserRole

from app.models.meter import Meter
from app.models.reading import Reading
from app.models.tubewell import Tubewell
from app.models.tubewell_assignment import TubewellAssignment
from app.models.user import User


# ============================================================
# SECTION 2: DECIMAL CONVERSION
# ============================================================

def to_decimal(
    value,
    field_name: str,
) -> Decimal:

    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be a numeric value."
        )

    try:
        result = Decimal(str(value))

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        raise ValueError(
            f"{field_name} must be a numeric value."
        )

    if not result.is_finite():
        raise ValueError(
            f"{field_name} must be a finite numeric value."
        )

    return result


# ============================================================
# SECTION 3: NON-NEGATIVE VALUE VALIDATION
# ============================================================

def validate_non_negative(
    value: Decimal,
    field_name: str,
) -> None:

    if value < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )


# ============================================================
# SECTION 4: ENERGY READING VALIDATION
# ============================================================

def validate_energy_reading(
    previous_reading,
    current_reading,
    l1,
    l2,
    l3,
    zero_confirmed: bool = False,
) -> dict:

    previous = to_decimal(
        previous_reading,
        "Previous reading",
    )

    current = to_decimal(
        current_reading,
        "Current reading",
    )

    phase_l1 = to_decimal(
        l1,
        "L1",
    )

    phase_l2 = to_decimal(
        l2,
        "L2",
    )

    phase_l3 = to_decimal(
        l3,
        "L3",
    )

    validate_non_negative(
        previous,
        "Previous reading",
    )

    validate_non_negative(
        current,
        "Current reading",
    )

    validate_non_negative(
        phase_l1,
        "L1",
    )

    validate_non_negative(
        phase_l2,
        "L2",
    )

    validate_non_negative(
        phase_l3,
        "L3",
    )

    has_zero_value = any(
        value == 0
        for value in (
            previous,
            current,
            phase_l1,
            phase_l2,
            phase_l3,
        )
    )

    if (
        has_zero_value
        and zero_confirmed is not True
    ):
        raise ValueError(
            "Zero value requires confirmation."
        )

    difference = (
        current - previous
    )

    return {
        "previous_reading": previous,
        "current_reading": current,
        "difference": difference,
        "l1": phase_l1,
        "l2": phase_l2,
        "l3": phase_l3,
        "zero_confirmed": zero_confirmed,
        "negative_difference":
            difference < 0,
    }


# ============================================================
# SECTION 5: PREPAID READING VALIDATION
# ============================================================

def validate_prepaid_reading(
    prepaid_meter_body_number: str,
    previous_reading,
    current_reading,
    previous_money,
    current_money,
    previous_time_minutes: int,
    current_time_minutes: int,
) -> dict:

    if not isinstance(
        prepaid_meter_body_number,
        str,
    ):
        raise ValueError(
            "Prepaid meter body number is required."
        )

    if not prepaid_meter_body_number.strip():
        raise ValueError(
            "Prepaid meter body number is required."
        )

    if (
        prepaid_meter_body_number
        != prepaid_meter_body_number.strip()
    ):
        raise ValueError(
            "Prepaid meter body number must not contain "
            "leading or trailing spaces."
        )

    if len(prepaid_meter_body_number) > 100:
        raise ValueError(
            "Prepaid meter body number is too long."
        )

    previous = to_decimal(
        previous_reading,
        "Previous reading",
    )

    current = to_decimal(
        current_reading,
        "Current reading",
    )

    money_previous = to_decimal(
        previous_money,
        "Previous money",
    )

    money_current = to_decimal(
        current_money,
        "Current money",
    )

    validate_non_negative(
        previous,
        "Previous reading",
    )

    validate_non_negative(
        current,
        "Current reading",
    )

    validate_non_negative(
        money_previous,
        "Previous money",
    )

    validate_non_negative(
        money_current,
        "Current money",
    )

    for value, field_name in (
        (
            previous_time_minutes,
            "Previous time minutes",
        ),
        (
            current_time_minutes,
            "Current time minutes",
        ),
    ):

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
        ):
            raise ValueError(
                f"{field_name} must be a whole number."
            )

        if value < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

    reading_difference = (
        current - previous
    )

    money_difference = (
        money_current - money_previous
    )

    time_difference_minutes = (
        current_time_minutes
        - previous_time_minutes
    )

    time_difference_hours = (
        Decimal(time_difference_minutes)
        / Decimal("60")
    )

    negative_reading_difference = (
        reading_difference < 0
    )

    negative_money_difference = (
        money_difference < 0
    )

    negative_time_difference = (
        time_difference_minutes < 0
    )

    return {
        "prepaid_meter_body_number":
            prepaid_meter_body_number,

        "previous_reading":
            previous,

        "current_reading":
            current,

        "reading_difference":
            reading_difference,

        "previous_money":
            money_previous,

        "current_money":
            money_current,

        "money_difference":
            money_difference,

        "previous_time_minutes":
            previous_time_minutes,

        "current_time_minutes":
            current_time_minutes,

        "time_difference_minutes":
            time_difference_minutes,

        "time_difference_hours":
            time_difference_hours,

        "negative_reading_difference":
            negative_reading_difference,

        "negative_money_difference":
            negative_money_difference,

        "negative_time_difference":
            negative_time_difference,

        "has_negative_difference":
            any(
                (
                    negative_reading_difference,
                    negative_money_difference,
                    negative_time_difference,
                )
            ),
    }


# ============================================================
# SECTION 6: READING SUBMISSION PERMISSION
# ============================================================

def validate_reading_submission_access(
    db: Session,
    tubewell_id: int,
    field_user_id: int,
) -> bool:

    for record_id in (
        tubewell_id,
        field_user_id,
    ):
        if (
            not isinstance(record_id, int)
            or isinstance(record_id, bool)
            or record_id <= 0
        ):
            return False

    tubewell = db.get(
        Tubewell,
        tubewell_id,
    )

    if tubewell is None:
        return False

    field_user = db.get(
        User,
        field_user_id,
    )

    if field_user is None:
        return False

    if (
        field_user.role
        != UserRole.FIELD_USER.value
    ):
        return False

    if not field_user.is_active:
        return False

    if (
        field_user.upazila_id
        != tubewell.management_unit_id
    ):
        return False

    current_assignment = db.scalar(
        select(TubewellAssignment).where(
            TubewellAssignment.tubewell_id
            == tubewell_id,
            TubewellAssignment.field_user_id
            == field_user_id,
            TubewellAssignment.ended_at.is_(
                None
            ),
        )
    )

    return current_assignment is not None


# ============================================================
# SECTION 7: CLIENT SUBMISSION ID VALIDATION
# ============================================================

def validate_client_submission_id(
    client_submission_id: str,
) -> str:

    if not isinstance(
        client_submission_id,
        str,
    ):
        raise ValueError(
            "Client submission ID is required."
        )

    if not client_submission_id.strip():
        raise ValueError(
            "Client submission ID is required."
        )

    if (
        client_submission_id
        != client_submission_id.strip()
    ):
        raise ValueError(
            "Client submission ID must not contain "
            "leading or trailing spaces."
        )

    if len(client_submission_id) > 100:
        raise ValueError(
            "Client submission ID is too long."
        )

    return client_submission_id


# ============================================================
# SECTION 8: FIND EXISTING SUBMISSION
# ============================================================

def get_reading_by_client_submission_id(
    db: Session,
    client_submission_id: str,
) -> Reading | None:

    valid_submission_id = (
        validate_client_submission_id(
            client_submission_id
        )
    )

    return db.scalar(
        select(Reading).where(
            Reading.client_submission_id
            == valid_submission_id
        )
    )


# ============================================================
# SECTION 9: METER / TUBEWELL CONSISTENCY
# ============================================================

def validate_meter_for_tubewell(
    db: Session,
    tubewell_id: int,
    meter_id: int | None,
) -> bool:

    if meter_id is None:
        return True

    if (
        not isinstance(meter_id, int)
        or isinstance(meter_id, bool)
        or meter_id <= 0
    ):
        return False

    meter = db.get(
        Meter,
        meter_id,
    )

    if meter is None:
        return False

    return (
        meter.tubewell_id
        == tubewell_id
    )


# ============================================================
# SECTION 10: COMMON SUBMISSION CONTEXT
# ============================================================

def validate_reading_submission_context(
    db: Session,
    *,
    reading_type: str,
    tubewell_id: int,
    field_user_id: int,
    meter_id: int | None,
    client_submission_id: str,
) -> Reading | None:

    valid_submission_id = (
        validate_client_submission_id(
            client_submission_id
        )
    )

    existing_reading = (
        get_reading_by_client_submission_id(
            db,
            valid_submission_id,
        )
    )

    if existing_reading is not None:

        require_idempotent_retry_identity(
            existing_reading,
            reading_type=reading_type,
            tubewell_id=tubewell_id,
            meter_id=meter_id,
            collected_by_user_id=field_user_id,
        )

        return existing_reading

    if not validate_reading_submission_access(
        db,
        tubewell_id,
        field_user_id,
    ):
        raise ValueError(
            "Field User is not authorized to submit "
            "a reading for this tubewell."
        )

    if not validate_meter_for_tubewell(
        db,
        tubewell_id,
        meter_id,
    ):
        raise ValueError(
            "Meter does not belong to this tubewell."
        )

    return None


# ============================================================
# SECTION 11: RESOLVE CONCURRENT IDEMPOTENCY CONFLICT
# ============================================================

def resolve_idempotency_conflict(
    db: Session,
    *,
    client_submission_id: str,
    reading_type: str,
    tubewell_id: int,
    meter_id: int | None,
    collected_by_user_id: int,
) -> Reading | None:

    existing_reading = (
        get_reading_by_client_submission_id(
            db,
            client_submission_id,
        )
    )

    if existing_reading is None:
        return None

    require_idempotent_retry_identity(
        existing_reading,
        reading_type=reading_type,
        tubewell_id=tubewell_id,
        meter_id=meter_id,
        collected_by_user_id=collected_by_user_id,
    )

    return existing_reading


# ============================================================
# SECTION 12: CREATE ENERGY READING
# ============================================================

def create_energy_reading(
    db: Session,
    *,
    tubewell_id: int,
    meter_id: int | None,
    reading_date,
    collected_by_user_id: int,
    previous_reading,
    current_reading,
    l1,
    l2,
    l3,
    zero_confirmed: bool,
    client_submission_id: str,
) -> tuple[Reading, bool]:

    if not validate_reading_date(
        reading_date
    ):
        raise ValueError(
            "Reading date cannot be in the future."
        )

    existing = validate_reading_submission_context(
        db=db,
        reading_type="energy",
        tubewell_id=tubewell_id,
        field_user_id=collected_by_user_id,
        meter_id=meter_id,
        client_submission_id=client_submission_id,
    )

    # --------------------------------------------------------
    # Exact retry must match the original full Energy payload.
    # --------------------------------------------------------

    if existing is not None:

        require_energy_retry_payload(
            existing,
            reading_date=reading_date,
            previous_reading=previous_reading,
            current_reading=current_reading,
            l1=l1,
            l2=l2,
            l3=l3,
            zero_confirmed=zero_confirmed,
        )

        return existing, False

    values = validate_energy_reading(
        previous_reading=previous_reading,
        current_reading=current_reading,
        l1=l1,
        l2=l2,
        l3=l3,
        zero_confirmed=zero_confirmed,
    )

    reading = Reading(
        tubewell_id=tubewell_id,
        meter_id=meter_id,
        reading_value=None,
        reading_date=reading_date,
        collected_by_user_id=(
            collected_by_user_id
        ),
        reading_type="energy",

        previous_reading=values[
            "previous_reading"
        ],

        current_reading=values[
            "current_reading"
        ],

        l1=values["l1"],
        l2=values["l2"],
        l3=values["l3"],

        zero_confirmed=values[
            "zero_confirmed"
        ],

        prepaid_meter_body_number=None,
        previous_money=None,
        current_money=None,
        previous_time_minutes=None,
        current_time_minutes=None,

        client_submission_id=(
            client_submission_id
        ),
    )

    db.add(reading)

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        existing = resolve_idempotency_conflict(
            db,
            client_submission_id=(
                client_submission_id
            ),
            reading_type="energy",
            tubewell_id=tubewell_id,
            meter_id=meter_id,
            collected_by_user_id=(
                collected_by_user_id
            ),
        )

        if existing is not None:

            require_energy_retry_payload(
                existing,
                reading_date=reading_date,
                previous_reading=previous_reading,
                current_reading=current_reading,
                l1=l1,
                l2=l2,
                l3=l3,
                zero_confirmed=zero_confirmed,
            )

            return existing, False

        raise ValueError(
            "Reading could not be saved."
        )

    db.refresh(reading)

    return reading, True


# ============================================================
# SECTION 13: CREATE PREPAID READING
# ============================================================

def create_prepaid_reading(
    db: Session,
    *,
    tubewell_id: int,
    meter_id: int | None,
    reading_date,
    collected_by_user_id: int,
    prepaid_meter_body_number: str,
    previous_reading,
    current_reading,
    previous_money,
    current_money,
    previous_time_minutes: int,
    current_time_minutes: int,
    client_submission_id: str,
) -> tuple[Reading, bool]:

    if not validate_reading_date(
        reading_date
    ):
        raise ValueError(
            "Reading date cannot be in the future."
        )

    existing = validate_reading_submission_context(
        db=db,
        reading_type="prepaid",
        tubewell_id=tubewell_id,
        field_user_id=collected_by_user_id,
        meter_id=meter_id,
        client_submission_id=client_submission_id,
    )

    # --------------------------------------------------------
    # Exact retry must match original full Prepaid payload.
    # --------------------------------------------------------

    if existing is not None:

        require_prepaid_retry_payload(
            existing,
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
        )

        return existing, False

    values = validate_prepaid_reading(
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
    )

    reading = Reading(
        tubewell_id=tubewell_id,
        meter_id=meter_id,
        reading_value=None,
        reading_date=reading_date,
        collected_by_user_id=(
            collected_by_user_id
        ),
        reading_type="prepaid",

        previous_reading=values[
            "previous_reading"
        ],

        current_reading=values[
            "current_reading"
        ],

        l1=None,
        l2=None,
        l3=None,
        zero_confirmed=None,

        prepaid_meter_body_number=values[
            "prepaid_meter_body_number"
        ],

        previous_money=values[
            "previous_money"
        ],

        current_money=values[
            "current_money"
        ],

        previous_time_minutes=values[
            "previous_time_minutes"
        ],

        current_time_minutes=values[
            "current_time_minutes"
        ],

        client_submission_id=(
            client_submission_id
        ),
    )

    db.add(reading)

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        existing = resolve_idempotency_conflict(
            db,
            client_submission_id=(
                client_submission_id
            ),
            reading_type="prepaid",
            tubewell_id=tubewell_id,
            meter_id=meter_id,
            collected_by_user_id=(
                collected_by_user_id
            ),
        )

        if existing is not None:

            require_prepaid_retry_payload(
                existing,
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
            )

            return existing, False

        raise ValueError(
            "Reading could not be saved."
        )

    db.refresh(reading)

    return reading, True