"""Isolated tests for PATCH /users/{user_id}/status.

Run from E:\\BMDA\\backend:
    python -m pytest -q tests/test_user_status_phase06_step37.py

Uses MagicMock sessions only; never opens a database connection or HTTP server.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.users import UserStatusRequest, change_user_status


def account(*, uid=8, role="field_user", active=True, parent_id=7, unit=2):
    return SimpleNamespace(
        id=uid, role=role, is_active=active,
        supervisor_id=parent_id, upazila_id=unit,
    )


def invoke(db, user, *, active, admin=None, user_id=None):
    return change_user_status(
        user_id=user.id if user_id is None else user_id,
        request=UserStatusRequest(is_active=active),
        db=db,
        current_admin=admin or account(uid=1, role="admin", parent_id=None, unit=None),
    )


def session(user, *, child_id=None, parent=None):
    db = MagicMock()
    db.get.return_value = user
    # Unit lock, target lock, then (optional) child lookup or parent lock.
    db.scalar.side_effect = [
        object(), user,
        parent if parent is not None else child_id,
    ]
    return db


def assert_http(exc, code):
    assert exc.value.status_code == code


def test_deactivate_leaf_user():
    user = account()
    db = session(user)
    assert invoke(db, user, active=False) is user
    assert user.is_active is False
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)
    db.delete.assert_not_called()


def test_reactivate_with_active_reporting_officer():
    user = account(active=False)
    db = session(user, parent=account(uid=7, role="supervisor", parent_id=3))
    assert invoke(db, user, active=True) is user
    assert user.is_active is True
    db.commit.assert_called_once()


def test_deactivate_with_active_direct_report_is_blocked():
    user = account(uid=7, role="supervisor", parent_id=3)
    db = session(user, child_id=15)
    with pytest.raises(HTTPException) as exc:
        invoke(db, user, active=False)
    assert_http(exc, 409)
    assert user.is_active is True
    db.commit.assert_not_called()


def test_reactivate_with_inactive_reporting_officer_is_blocked():
    user = account(active=False)
    db = session(user, parent=account(uid=7, role="supervisor", active=False))
    with pytest.raises(HTTPException) as exc:
        invoke(db, user, active=True)
    assert_http(exc, 409)
    assert user.is_active is False
    db.commit.assert_not_called()


def test_reactivate_cross_unit_reporting_officer_is_blocked():
    user = account(active=False)
    db = session(user, parent=account(uid=7, role="supervisor", unit=3))
    with pytest.raises(HTTPException) as exc:
        invoke(db, user, active=True)
    assert_http(exc, 409)
    db.commit.assert_not_called()


@pytest.mark.parametrize("user", [
    account(uid=1, role="admin", parent_id=None, unit=None),
    account(uid=9, role="admin", parent_id=None, unit=None),
])
def test_admin_accounts_cannot_be_changed(user):
    db = MagicMock()
    db.get.return_value = user
    with pytest.raises(HTTPException) as exc:
        invoke(db, user, active=False)
    assert_http(exc, 403)
    db.commit.assert_not_called()


def test_unchanged_status_does_not_commit():
    user = account(active=True)
    db = session(user)
    assert invoke(db, user, active=True) is user
    db.commit.assert_not_called()


def test_missing_user_is_404():
    db = MagicMock()
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        invoke(db, account(), active=False)
    assert_http(exc, 404)
    db.commit.assert_not_called()


def test_invalid_id_is_404_without_db_read():
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        invoke(db, account(), active=False, user_id=0)
    assert_http(exc, 404)
    db.get.assert_not_called()


def test_commit_integrity_error_rolls_back():
    from sqlalchemy.exc import IntegrityError
    user = account()
    db = session(user)
    db.commit.side_effect = IntegrityError("UPDATE users", {}, Exception("constraint"))
    with pytest.raises(HTTPException) as exc:
        invoke(db, user, active=False)
    assert_http(exc, 409)
    db.rollback.assert_called_once()


def test_status_request_rejects_unexpected_fields():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserStatusRequest(is_active=False, role="admin")
