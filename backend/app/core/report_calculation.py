# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from decimal import Decimal


# ============================================================
# SECTION 2: DECIMAL NORMALIZATION
# ============================================================

def to_decimal(
    value,
) -> Decimal:

    if isinstance(value, Decimal):
        return value

    return Decimal(
        str(value)
    )


# ============================================================
# SECTION 3: SIGNED DIFFERENCE
# ============================================================

def calculate_signed_difference(
    previous_value,
    current_value,
) -> Decimal:

    previous_decimal = to_decimal(
        previous_value
    )

    current_decimal = to_decimal(
        current_value
    )

    return (
        current_decimal
        - previous_decimal
    )


# ============================================================
# SECTION 4: POSITIVE CONTRIBUTION
# ============================================================

def calculate_positive_contribution(
    signed_difference,
) -> Decimal:

    value = to_decimal(
        signed_difference
    )

    if value > 0:
        return value

    return Decimal("0")


# ============================================================
# SECTION 5: NEGATIVE CONTRIBUTION
# ============================================================

def calculate_negative_contribution(
    signed_difference,
) -> Decimal:

    value = to_decimal(
        signed_difference
    )

    if value < 0:
        return value

    return Decimal("0")


# ============================================================
# SECTION 6: INTEGER TIME DIFFERENCE
# ============================================================

def calculate_signed_time_difference(
    previous_minutes: int,
    current_minutes: int,
) -> int:

    return (
        current_minutes
        - previous_minutes
    )


# ============================================================
# SECTION 7: POSITIVE TIME CONTRIBUTION
# ============================================================

def calculate_positive_time_contribution(
    signed_minutes: int,
) -> int:

    if signed_minutes > 0:
        return signed_minutes

    return 0


# ============================================================
# SECTION 8: NEGATIVE TIME CONTRIBUTION
# ============================================================

def calculate_negative_time_contribution(
    signed_minutes: int,
) -> int:

    if signed_minutes < 0:
        return signed_minutes

    return 0


# ============================================================
# SECTION 9: MINUTES TO HOURS
# ============================================================

def minutes_to_hours(
    minutes: int,
) -> Decimal:

    return (
        Decimal(minutes)
        / Decimal("60")
    )


# ============================================================
# SECTION 10: DECIMAL TOTALS
# ============================================================

def calculate_decimal_totals(
    signed_values,
) -> dict:

    positive_total = Decimal("0")
    negative_total = Decimal("0")
    net_total = Decimal("0")

    for value in signed_values:

        decimal_value = to_decimal(
            value
        )

        net_total += decimal_value

        if decimal_value > 0:
            positive_total += decimal_value

        elif decimal_value < 0:
            negative_total += decimal_value

    return {
        "positive_total":
            positive_total,

        "negative_total":
            negative_total,

        "net_total":
            net_total,
    }


# ============================================================
# SECTION 11: INTEGER TIME TOTALS
# ============================================================

def calculate_time_totals(
    signed_minutes_values,
) -> dict:

    positive_total = 0
    negative_total = 0
    net_total = 0

    for value in signed_minutes_values:

        net_total += value

        if value > 0:
            positive_total += value

        elif value < 0:
            negative_total += value

    return {
        "positive_total":
            positive_total,

        "negative_total":
            negative_total,

        "net_total":
            net_total,
    }