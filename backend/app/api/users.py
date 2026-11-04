# ============================================================
# SECTION 1: IMPORTS
# Import FastAPI, database tools, business validations,
# models, schemas, and security helpers.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.core.roles import UserRole
from app.core.security import hash_password
from app.core.user_management import (
    is_username_available,
    validate_assistant_engineer_creation,
    validate_field_user_creation,
    validate_full_name,
    validate_supervisor_creation,
)

from app.db.database import get_db
from app.models.upazila import Upazila
from app.models.user import User

from app.schemas.user import (
    ManagementUnitResponse,
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
)


# ============================================================
# SECTION 2: ROUTER CONFIGURATION
# User management endpoints start with /users.
# ============================================================

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


# ============================================================
# SECTION 3: LIST MANAGEMENT UNITS
# Only an authenticated Admin can view this helper list.
# ============================================================

@router.get(
    "/management-units",
    response_model=list[ManagementUnitResponse],
)
def list_management_units(
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    units = db.scalars(
        select(Upazila).order_by(
            Upazila.id.asc()
        )
    ).all()

    return units


# ============================================================
# SECTION 4: LIST USERS
# Only an authenticated Admin can view user accounts.
#
# Optional filters help inspect the BMDA hierarchy.
# Password hashes are never returned.
# ============================================================

@router.get(
    "",
    response_model=list[UserResponse],
)
def list_users(
    role: UserRole | None = Query(
        default=None
    ),
    upazila_id: int | None = Query(
        default=None,
        gt=0,
    ),
    supervisor_id: int | None = Query(
        default=None,
        gt=0,
    ),
    is_active: bool | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    query = select(User)

    if role is not None:
        query = query.where(
            User.role == role.value
        )

    if upazila_id is not None:
        query = query.where(
            User.upazila_id == upazila_id
        )

    if supervisor_id is not None:
        query = query.where(
            User.supervisor_id == supervisor_id
        )

    if is_active is not None:
        query = query.where(
            User.is_active == is_active
        )

    users = db.scalars(
        query.order_by(
            User.id.asc()
        )
    ).all()

    return users


# ============================================================
# SECTION 5: GET DIRECT SUBORDINATES
# Return only users who directly report to the selected user.
#
# Admin -> Assistant Engineers
# Assistant Engineer -> Supervisors
# Supervisor -> Field Users
# Field User -> Empty list
# ============================================================

@router.get(
    "/{user_id}/subordinates",
    response_model=list[UserResponse],
)
def get_direct_subordinates(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    # --------------------------------------------------------
    # CHECK 1: Validate selected user.
    # --------------------------------------------------------

    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    parent_user = db.get(
        User,
        user_id,
    )

    if parent_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # --------------------------------------------------------
    # CHECK 2: Determine expected direct child role.
    # --------------------------------------------------------

    direct_child_roles = {
        UserRole.ADMIN.value:
            UserRole.ASSISTANT_ENGINEER.value,

        UserRole.ASSISTANT_ENGINEER.value:
            UserRole.SUPERVISOR.value,

        UserRole.SUPERVISOR.value:
            UserRole.FIELD_USER.value,

        UserRole.FIELD_USER.value:
            None,
    }

    child_role = direct_child_roles.get(
        parent_user.role
    )

    # Field Users do not have subordinate system users.
    if child_role is None:
        return []

    # --------------------------------------------------------
    # CHECK 3: Load direct subordinate users.
    # --------------------------------------------------------

    subordinates = db.scalars(
        select(User)
        .where(
            User.supervisor_id == parent_user.id,
            User.role == child_role,
        )
        .order_by(
            User.id.asc()
        )
    ).all()

    return subordinates


# ============================================================
# SECTION 6: GET SINGLE USER
# Only an authenticated Admin can view a specific user.
# ============================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user = db.get(
        User,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


# ============================================================
# SECTION 7: CREATE USER
# Only an authenticated Admin may create subordinate users.
# ============================================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_admin
    ),
):

    # --------------------------------------------------------
    # CHECK 1: Validate full name.
    # --------------------------------------------------------

    if not validate_full_name(
        request.full_name
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid full name.",
        )

    # --------------------------------------------------------
    # CHECK 2: Validate username and availability.
    # --------------------------------------------------------

    if not is_username_available(
        db,
        request.username,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is invalid or already exists.",
        )

    # --------------------------------------------------------
    # CHECK 3: Lock the management unit.
    # --------------------------------------------------------

    unit = db.scalar(
        select(Upazila)
        .where(
            Upazila.id == request.upazila_id
        )
        .with_for_update()
    )

    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid management unit.",
        )

    # --------------------------------------------------------
    # CHECK 4: Validate role-specific hierarchy.
    # --------------------------------------------------------

    supervisor_id = request.supervisor_id

    if request.role == UserRole.ASSISTANT_ENGINEER.value:

        if supervisor_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Assistant Engineer supervisor is "
                    "assigned automatically to the Admin."
                ),
            )

        if not validate_assistant_engineer_creation(
            db,
            request.upazila_id,
            current_admin.id,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Assistant Engineer creation is not "
                    "allowed for this management unit."
                ),
            )

        supervisor_id = current_admin.id

    elif request.role == UserRole.SUPERVISOR.value:

        if supervisor_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Assistant Engineer ID is required "
                    "for a Supervisor."
                ),
            )

        db.scalar(
            select(User)
            .where(
                User.id == supervisor_id
            )
            .with_for_update()
        )

        if not validate_supervisor_creation(
            db,
            request.upazila_id,
            supervisor_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Supervisor hierarchy, management unit, "
                    "or account limit validation failed."
                ),
            )

    elif request.role == UserRole.FIELD_USER.value:

        if supervisor_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Supervisor ID is required "
                    "for a Field User."
                ),
            )

        db.scalar(
            select(User)
            .where(
                User.id == supervisor_id
            )
            .with_for_update()
        )

        if not validate_field_user_creation(
            db,
            request.upazila_id,
            supervisor_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Field User hierarchy, management unit, "
                    "or account limit validation failed."
                ),
            )

    # --------------------------------------------------------
    # SECTION 8: CREATE DATABASE RECORD
    # Store only the password hash.
    # --------------------------------------------------------

    new_user = User(
        full_name=request.full_name,
        username=request.username,
        password_hash=hash_password(
            request.password
        ),
        role=request.role,
        upazila_id=request.upazila_id,
        supervisor_id=supervisor_id,
        is_active=True,
    )

    db.add(
        new_user
    )

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "User could not be created because "
                "a database uniqueness rule was violated."
            ),
        )

    db.refresh(
        new_user
    )

    return new_user


# ============================================================
# SECTION 9: UPDATE USER PROFILE
# An active Admin can correct a user's name or username.
# Preserve user ID, role, hierarchy, password, and status.
# ============================================================

@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    # CHECK 1: Find and lock the account being edited.
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # CHECK 2: Validate the corrected full name.
    if not validate_full_name(request.full_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid full name.",
        )

    # CHECK 3: Validate username format without rejecting
    # the account's own current username.
    username = request.username
    if (
        not username.strip()
        or username != username.strip()
        or len(username) > 100
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username.",
        )

    other_user_id = db.scalar(
        select(User.id).where(
            func.lower(User.username) == username.lower(),
            User.id != user.id,
        )
    )

    if other_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already in use.",
        )

    # SECTION 10: SAVE PROFILE CORRECTIONS
    # No changes to role, unit, supervisor, or audit identity.
    user.full_name = request.full_name
    user.username = username

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username conflicts with an existing account.",
        )

    db.refresh(user)
    return user
