# ============================================================
# SECTION 1: ERROR CODES
# ============================================================

ERROR_CODE_TEMPORARY_SERVER_FAILURE = (
    "temporary_server_failure"
)

ERROR_CODE_CLIENT_SUBMISSION_CONFLICT = (
    "client_submission_conflict"
)

ERROR_CODE_READING_DATE_INVALID = (
    "reading_date_invalid"
)

ERROR_CODE_ZERO_CONFIRMATION_REQUIRED = (
    "zero_confirmation_required"
)

ERROR_CODE_PREPAID_DATA_INVALID = (
    "prepaid_data_invalid"
)

ERROR_CODE_READING_DATA_INVALID = (
    "reading_data_invalid"
)

ERROR_CODE_READING_ACCESS_DENIED = (
    "reading_access_denied"
)

ERROR_CODE_UNKNOWN_READING_REJECTION = (
    "unknown_reading_rejection"
)


# ============================================================
# SECTION 2: BUILD STRUCTURED ERROR DETAIL
#
# retryable=True:
#   Mobile keeps item in retry queue.
#
# needs_attention=True:
#   Mobile stops automatic retry and shows the item
#   in Needs Attention.
# ============================================================

def build_reading_sync_error(
    exc: ValueError,
) -> dict:

    message = str(exc)

    lowered = message.lower()


    # --------------------------------------------------------
    # TEMPORARY SERVER / DATABASE FAILURE
    # --------------------------------------------------------

    if (
        "reading could not be saved"
        in lowered
    ):

        return {
            "error_code":
                ERROR_CODE_TEMPORARY_SERVER_FAILURE,

            "message":
                message,

            "message_bn":
                (
                    "সার্ভারে রিডিং সংরক্ষণ করা যায়নি। "
                    "ইন্টারনেট বা সার্ভার স্বাভাবিক হলে "
                    "আবার স্বয়ংক্রিয়ভাবে চেষ্টা করা হবে।"
                ),

            "retryable":
                True,

            "needs_attention":
                False,
        }


    # --------------------------------------------------------
    # CLIENT SUBMISSION ID CONFLICT
    #
    # Same local submission identity is already tied to
    # another server-side payload/identity.
    # Automatic retry must stop.
    # --------------------------------------------------------

    if (
        "client submission id is already used"
        in lowered
        or
        "client submission id already exists"
        in lowered
    ):

        return {
            "error_code":
                ERROR_CODE_CLIENT_SUBMISSION_CONFLICT,

            "message":
                message,

            "message_bn":
                (
                    "এই অফলাইন সাবমিশন আইডি ইতিমধ্যে "
                    "অন্য রিডিংয়ের জন্য ব্যবহৃত হয়েছে। "
                    "তথ্য যাচাই করে প্রয়োজনীয় সংশোধন করুন।"
                ),

            "retryable":
                False,

            "needs_attention":
                True,
        }


    # --------------------------------------------------------
    # FIELD USER / ASSIGNMENT ACCESS FAILURE
    # --------------------------------------------------------

    if (
        "not authorized"
        in lowered
    ):

        return {
            "error_code":
                ERROR_CODE_READING_ACCESS_DENIED,

            "message":
                message,

            "message_bn":
                (
                    "এই টিউবওয়েলের রিডিং জমা দেওয়ার "
                    "অনুমতি বর্তমানে আপনার নেই। "
                    "অ্যাসাইনমেন্ট যাচাই করুন।"
                ),

            "retryable":
                False,

            "needs_attention":
                True,
        }


    # --------------------------------------------------------
    # FUTURE READING DATE
    # --------------------------------------------------------

    if (
        "reading date cannot be in the future"
        in lowered
    ):

        return {
            "error_code":
                ERROR_CODE_READING_DATE_INVALID,

            "message":
                message,

            "message_bn":
                (
                    "রিডিংয়ের তারিখ ভবিষ্যতের হতে পারবে না। "
                    "তারিখ সংশোধন করে আবার জমা দিন।"
                ),

            "retryable":
                False,

            "needs_attention":
                True,
        }


    # --------------------------------------------------------
    # ENERGY ZERO CONFIRMATION
    # --------------------------------------------------------

    if (
        "zero value requires confirmation"
        in lowered
    ):

        return {
            "error_code":
                ERROR_CODE_ZERO_CONFIRMATION_REQUIRED,

            "message":
                message,

            "message_bn":
                (
                    "এক বা একাধিক মান শূন্য। "
                    "শূন্য মান নিশ্চিত করে আবার জমা দিন।"
                ),

            "retryable":
                False,

            "needs_attention":
                True,
        }


    # --------------------------------------------------------
    # PREPAID-SPECIFIC VALIDATION
    # --------------------------------------------------------

    prepaid_phrases = (
        "prepaid meter body number",
        "previous money",
        "current money",
        "previous time minutes",
        "current time minutes",
    )

    if any(
        phrase in lowered
        for phrase in prepaid_phrases
    ):

        return {
            "error_code":
                ERROR_CODE_PREPAID_DATA_INVALID,

            "message":
                message,

            "message_bn":
                (
                    "প্রিপেইড রিডিংয়ের তথ্য সঠিক নয়। "
                    "মিটার বডি নম্বর, টাকা ও সময়ের তথ্য "
                    "যাচাই করে আবার জমা দিন।"
                ),

            "retryable":
                False,

            "needs_attention":
                True,
        }


    # --------------------------------------------------------
    # GENERIC READING VALIDATION
    # --------------------------------------------------------

    reading_validation_phrases = (
        "previous reading",
        "current reading",
        "l1",
        "l2",
        "l3",
        "cannot be negative",
        "must be a number",
        "must be a whole number",
    )

    if any(
        phrase in lowered
        for phrase in reading_validation_phrases
    ):

        return {
            "error_code":
                ERROR_CODE_READING_DATA_INVALID,

            "message":
                message,

            "message_bn":
                (
                    "রিডিংয়ের তথ্য সঠিক নয়। "
                    "দেওয়া মানগুলো যাচাই ও সংশোধন করে "
                    "আবার জমা দিন।"
                ),

            "retryable":
                False,

            "needs_attention":
                True,
        }


    # --------------------------------------------------------
    # UNKNOWN BUSINESS REJECTION
    #
    # Do not automatically retry an unknown ValueError
    # forever. Human attention is safer.
    # --------------------------------------------------------

    return {
        "error_code":
            ERROR_CODE_UNKNOWN_READING_REJECTION,

        "message":
            message,

        "message_bn":
            (
                "রিডিংটি সার্ভার গ্রহণ করেনি। "
                "তথ্য যাচাই করে প্রয়োজন হলে সংশোধন করুন।"
            ),

        "retryable":
            False,

        "needs_attention":
            True,
    }


# ============================================================
# SECTION 3: HTTP STATUS FOR STRUCTURED ERROR
# ============================================================

def get_reading_sync_http_status(
    error_detail: dict,
) -> int:

    error_code = error_detail[
        "error_code"
    ]

    if (
        error_code
        == ERROR_CODE_TEMPORARY_SERVER_FAILURE
    ):
        return 503

    if (
        error_code
        == ERROR_CODE_CLIENT_SUBMISSION_CONFLICT
    ):
        return 409

    if (
        error_code
        == ERROR_CODE_READING_ACCESS_DENIED
    ):
        return 403

    return 400