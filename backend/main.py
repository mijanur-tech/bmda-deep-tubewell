from app.api.ae_reading_warnings import router as ae_reading_warnings_router
from app.api.ae_field_user_coverage import router as ae_field_user_coverage_router
from app.api.sae_field_visitor_summary import router as sae_field_visitor_summary_router
# ============================================================
# SECTION 1: IMPORTS
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.tubewells import router as tubewells_router
from app.api.actual_upazilas import router as actual_upazilas_router
from app.api.unions import router as unions_router
from app.api.mouzas import router as mouzas_router
from app.api.dtw_master import router as dtw_master_router
from app.api.meters import router as meters_router
from app.api.assignments import router as assignments_router
from app.api.readings import router as readings_router

from app.api.meter_replacements import (
    router as meter_replacements_router,
)

from app.api.tubewell_status import (
    router as tubewell_status_router,
)

from app.api.reading_corrections import (
    router as reading_corrections_router,
)

from app.api.pending_requests import (
    router as pending_requests_router,
)

from app.api.reading_warnings import (
    router as reading_warnings_router,
)

from app.api.reports import (
    router as reports_router,
)

# AE Dashboard: unit-scoped read-only personnel summary.
from app.api.ae_personnel_summary import (
    router as ae_personnel_summary_router,
)


# ============================================================
# SECTION 2: FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="BMDA Deep Tubewell Management System",
    version="1.0.0",
)


# ============================================================
# SECTION 3: CORS CONFIGURATION
# ============================================================

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SECTION 4: API ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tubewells_router)
app.include_router(actual_upazilas_router)
app.include_router(unions_router)
app.include_router(mouzas_router)
app.include_router(dtw_master_router)
app.include_router(meters_router)
app.include_router(assignments_router)
app.include_router(readings_router)
app.include_router(meter_replacements_router)
app.include_router(tubewell_status_router)
app.include_router(reading_corrections_router)
app.include_router(pending_requests_router)
app.include_router(reading_warnings_router)
app.include_router(reports_router)

# AE Dashboard: own-unit personnel counts only.
app.include_router(ae_personnel_summary_router)
app.include_router(ae_reading_warnings_router)
app.include_router(ae_field_user_coverage_router)
app.include_router(sae_field_visitor_summary_router)


# ============================================================
# SECTION 5: ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "BMDA Backend API is running"
    }
