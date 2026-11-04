# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from sqlalchemy.orm import Session

from app.api.auth import get_current_user

from app.core.combined_report_management import (
    get_combined_report,
)

from app.core.energy_report_management import (
    get_energy_report,
)

from app.core.prepaid_report_management import (
    get_prepaid_report,
)

from app.core.report_excel_export import (
    export_combined_report_excel,
    export_energy_report_excel,
    export_prepaid_report_excel,
)

from app.core.report_pdf_export import (
    export_combined_report_pdf,
    export_energy_report_pdf,
    export_prepaid_report_pdf,
)

from app.db.database import get_db

from app.models.user import User

from app.schemas.reports import (
    CombinedReportResponse,
    EnergyReportResponse,
    PrepaidReportResponse,
)


# ============================================================
# SECTION 2: ROUTER
# ============================================================

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


# ============================================================
# SECTION 3: CONSTANTS
# ============================================================

XLSX_MEDIA_TYPE = (
    "application/"
    "vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)

PDF_MEDIA_TYPE = "application/pdf"


# ============================================================
# SECTION 4: REPORT ERROR MAPPING
# ============================================================

def raise_report_http_error(
    exc: ValueError,
) -> None:

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ============================================================
# SECTION 5: BUILD EXCEL RESPONSE
# ============================================================

def build_excel_response(
    *,
    content: bytes,
    filename: str,
) -> Response:

    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )


# ============================================================
# SECTION 6: BUILD PDF RESPONSE
# ============================================================

def build_pdf_response(
    *,
    content: bytes,
    filename: str,
) -> Response:

    return Response(
        content=content,
        media_type=PDF_MEDIA_TYPE,
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )


# ============================================================
# SECTION 7: ENERGY REPORT JSON
# ============================================================

@router.get(
    "/energy",
    response_model=EnergyReportResponse,
)
def energy_report(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        return get_energy_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 8: PREPAID REPORT JSON
# ============================================================

@router.get(
    "/prepaid",
    response_model=PrepaidReportResponse,
)
def prepaid_report(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        return get_prepaid_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 9: COMBINED REPORT JSON
# ============================================================

@router.get(
    "/combined",
    response_model=CombinedReportResponse,
)
def combined_report(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        return get_combined_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 10: ENERGY REPORT EXCEL
# ============================================================

@router.get(
    "/energy/excel",
)
def energy_report_excel(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        report = get_energy_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        content = export_energy_report_excel(
            report
        )

        return build_excel_response(
            content=content,
            filename="energy_report.xlsx",
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 11: PREPAID REPORT EXCEL
# ============================================================

@router.get(
    "/prepaid/excel",
)
def prepaid_report_excel(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        report = get_prepaid_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        content = export_prepaid_report_excel(
            report
        )

        return build_excel_response(
            content=content,
            filename="prepaid_report.xlsx",
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 12: COMBINED REPORT EXCEL
# ============================================================

@router.get(
    "/combined/excel",
)
def combined_report_excel(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        report = get_combined_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        content = export_combined_report_excel(
            report
        )

        return build_excel_response(
            content=content,
            filename="combined_report.xlsx",
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 13: ENERGY REPORT PDF
# ============================================================

@router.get(
    "/energy/pdf",
)
def energy_report_pdf(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        report = get_energy_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        content = export_energy_report_pdf(
            report
        )

        return build_pdf_response(
            content=content,
            filename="energy_report.pdf",
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 14: PREPAID REPORT PDF
# ============================================================

@router.get(
    "/prepaid/pdf",
)
def prepaid_report_pdf(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        report = get_prepaid_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        content = export_prepaid_report_pdf(
            report
        )

        return build_pdf_response(
            content=content,
            filename="prepaid_report.pdf",
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )


# ============================================================
# SECTION 15: COMBINED REPORT PDF
# ============================================================

@router.get(
    "/combined/pdf",
)
def combined_report_pdf(
    start_date: date | None = Query(
        default=None
    ),

    end_date: date | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:
        report = get_combined_report(
            db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        content = export_combined_report_pdf(
            report
        )

        return build_pdf_response(
            content=content,
            filename="combined_report.pdf",
        )

    except ValueError as exc:
        raise_report_http_error(
            exc
        )