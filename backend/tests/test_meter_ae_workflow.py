"""BMDA AE meter replacement isolated service tests.

Run: python -m pytest -q tests/test_meter_ae_workflow.py
No live database connection, writes, or server required.
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core import meter_replacement_management as service


def actor(*, role="assistant_engineer", unit=11, active=True):
    return SimpleNamespace(role=role, upazila_id=unit, is_active=active)


def request(*, state="pending_ae_approval"):
    return SimpleNamespace(
        id=21, tubewell_id=31, old_meter_id=41, status=state,
        new_meter_number="NEW-2026-01", new_meter_id=None,
        ae_reviewed_by_user_id=None, ae_reviewed_at=None,
        ae_review_comment=None,
    )


def session(*, reviewer=None, record=None, meter=None):
    db = MagicMock()
    db.get.return_value = reviewer if reviewer is not None else actor()
    record = record if record is not None else request()
    meter = meter if meter is not None else SimpleNamespace(
        id=41, tubewell_id=31, removed_at=None
    )
    db.scalar.side_effect = [record, meter]
    db.flush.side_effect = lambda: setattr(db.add.call_args.args[0], "id", 51)
    return db, record, meter


def review(db, action="approved", ae_id=7, request_id=21):
    return service.review_meter_replacement_request_by_ae(
        db, request_id=request_id, ae_id=ae_id, action=action,
        review_comment="Checked",
    )


def test_ae_approval_closes_old_and_creates_new_only_at_final_approval():
    db, record, old = session()
    result = review(db)
    assert result is record
    assert record.status == "approved"
    assert record.ae_reviewed_by_user_id == 7
    assert record.new_meter_id == 51
    assert old.removed_at == date.today()
    db.add.assert_called_once()
    new = db.add.call_args.args[0]
    assert isinstance(new, service.Meter)
    assert new.tubewell_id == 31
    assert new.meter_number == "NEW-2026-01"
    assert new.installed_at == date.today()
    assert new.removed_at is None
    db.commit.assert_called_once()


def test_ae_rejection_does_not_touch_meters():
    db, record, old = session()
    review(db, action="rejected")
    assert record.status == "rejected"
    assert record.new_meter_id is None
    assert old.removed_at is None
    db.add.assert_not_called()
    db.commit.assert_called_once()


@pytest.mark.parametrize("reviewer", [
    actor(role="supervisor"),
    actor(role="field_user"),
    actor(unit=None),
    actor(active=False),
])
def test_unauthorized_actors_cannot_review(reviewer):
    db, _, _ = session(reviewer=reviewer)
    with pytest.raises(ValueError, match="AE is not authorized"):
        review(db)
    db.scalar.assert_not_called()
    db.commit.assert_not_called()
    db.add.assert_not_called()


def test_other_management_unit_or_missing_request_cannot_review():
    db, _, _ = session()
    db.scalar.side_effect = [None]
    with pytest.raises(ValueError, match="not found or AE is not authorized"):
        review(db)
    db.commit.assert_not_called()
    db.add.assert_not_called()


def test_old_meter_already_removed_blocks_approval():
    db, _, old = session(meter=SimpleNamespace(
        id=41, tubewell_id=31, removed_at=date(2026, 1, 1)
    ))
    with pytest.raises(ValueError, match="already been removed"):
        review(db)
    assert old.removed_at == date(2026, 1, 1)
    db.commit.assert_not_called()
    db.add.assert_not_called()


def test_invalid_action_rejected_without_database_access():
    db, _, _ = session()
    with pytest.raises(ValueError, match="Review action"):
        review(db, action="pending")
    db.get.assert_not_called()
    db.commit.assert_not_called()


def test_commit_failure_rolls_back():
    db, _, _ = session()
    db.commit.side_effect = RuntimeError("Simulated commit failure")
    with pytest.raises(RuntimeError, match="Simulated commit failure"):
        review(db)
    db.rollback.assert_called_once()


def test_sae_recommendation_does_not_create_or_close_meter(monkeypatch):
    db = MagicMock()
    record = request(state="pending")
    db.refresh.return_value = None
    monkeypatch.setattr(service, "get_pending_request_for_supervisor", lambda *a, **k: record)
    monkeypatch.setattr(
        service, "validate_old_meter_for_tubewell",
        lambda *a, **k: SimpleNamespace(removed_at=None),
    )
    result = service.review_meter_replacement_request(
        db, request_id=21, supervisor_id=8,
        action="approved", review_comment="Recommended",
    )
    assert result.status == "pending_ae_approval"
    assert result.new_meter_id is None
    db.add.assert_not_called()
    db.commit.assert_called_once()
