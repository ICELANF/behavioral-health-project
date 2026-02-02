"""
Unit tests for services/state_sync/manager.py

Tests cover event processing, role-based view retrieval, and pending review queries.
"""
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.state_sync.manager import (
    StateSyncManager,
    EventType,
    ViewRole,
    UiStyle,
)


@pytest.fixture()
def manager():
    """Provide a fresh StateSyncManager for each test."""
    return StateSyncManager()


# -----------------------------------------------
# process_event
# -----------------------------------------------

class TestProcessEvent:
    def test_process_event(self, manager):
        """process_event should create a record with all three views populated."""
        record = manager.process_event(
            user_id=1,
            event_type=EventType.TEXT_INPUT,
            raw_data={"text": "最近压力很大，总是焦虑"},
        )

        assert record is not None
        assert record.event_id is not None
        assert record.user_id == 1
        assert record.event_type == EventType.TEXT_INPUT
        assert record.processed is True

        # All views should be present
        assert record.client_view is not None
        assert record.coach_view is not None
        assert record.expert_view is not None

    def test_process_event_stress_detected(self, manager):
        """Text containing stress keywords should produce a stress template."""
        record = manager.process_event(
            user_id=1,
            event_type=EventType.TEXT_INPUT,
            raw_data={"text": "今天好累，压力很大"},
        )

        # Coach view should flag as YELLOW for stress
        assert record.coach_view.risk_flag == "YELLOW"
        assert "Stress" in record.coach_view.diagnosis

    def test_process_event_emotional_eating(self, manager):
        """Text about compulsive eating should produce an emotional_eating template."""
        record = manager.process_event(
            user_id=2,
            event_type=EventType.TEXT_INPUT,
            raw_data={"text": "停不下来吃零食"},
        )

        assert record.coach_view.risk_flag == "ORANGE"
        assert "Eating" in record.coach_view.diagnosis

    def test_process_event_device_glucose_high(self, manager):
        """High CGM values should produce a glucose_high template."""
        record = manager.process_event(
            user_id=3,
            event_type=EventType.DEVICE_DATA,
            raw_data={"cgm_value": 12.5},
        )

        assert record.coach_view.risk_flag == "ORANGE"
        assert "Hyperglycemia" in record.coach_view.diagnosis
        # Client view should suggest activity
        assert "companion_glucose_high" == record.client_view.msg_type

    def test_process_event_device_glucose_low(self, manager):
        """Low CGM values should produce a glucose_low template with RED flag."""
        record = manager.process_event(
            user_id=3,
            event_type=EventType.DEVICE_DATA,
            raw_data={"cgm_value": 3.0},
        )

        assert record.coach_view.risk_flag == "RED"
        assert "Hypoglycemia" in record.coach_view.diagnosis

    def test_process_event_task_complete(self, manager):
        """Completing a task should produce a task_completed template with GREEN flag."""
        record = manager.process_event(
            user_id=4,
            event_type=EventType.TASK_COMPLETE,
            raw_data={"task_id": "T-001"},
        )

        assert record.coach_view.risk_flag == "GREEN"
        assert record.client_view.ui_style == UiStyle.ENCOURAGING

    def test_process_event_stores_record(self, manager):
        """Processed events should be retrievable from the manager."""
        record = manager.process_event(
            user_id=10,
            event_type=EventType.TEXT_INPUT,
            raw_data={"text": "压力"},
        )

        events = manager.get_user_events(user_id=10, role=ViewRole.PATIENT)
        assert len(events) == 1
        assert events[0]["event_id"] == record.event_id


# -----------------------------------------------
# get_view_by_role
# -----------------------------------------------

class TestGetViewByRole:
    def test_get_view_by_role(self, manager):
        """get_view should return the correct view shape for each role."""
        record = manager.process_event(
            user_id=1,
            event_type=EventType.TEXT_INPUT,
            raw_data={"text": "焦虑"},
        )

        patient_view = manager.get_view(record.event_id, ViewRole.PATIENT)
        assert patient_view is not None
        assert "content" in patient_view
        assert "ui_style" in patient_view
        assert "msg_type" in patient_view

        coach_view = manager.get_view(record.event_id, ViewRole.COACH)
        assert coach_view is not None
        assert "risk_flag" in coach_view
        assert "diagnosis" in coach_view
        assert "suggested_action" in coach_view

        expert_view = manager.get_view(record.event_id, ViewRole.EXPERT)
        assert expert_view is not None
        assert "raw_data" in expert_view
        assert "risk_assessment" in expert_view

    def test_admin_view_has_all_fields(self, manager):
        """The ADMIN role should receive the full record (all views combined)."""
        record = manager.process_event(
            user_id=1,
            event_type=EventType.TEXT_INPUT,
            raw_data={"text": "累"},
        )

        admin_view = manager.get_view(record.event_id, ViewRole.ADMIN)
        assert admin_view is not None
        assert "client_view" in admin_view
        assert "coach_view" in admin_view
        assert "expert_view" in admin_view
        assert "event_id" in admin_view

    def test_get_view_nonexistent_event(self, manager):
        """get_view should return None for an event ID that does not exist."""
        result = manager.get_view("nonexistent-id", ViewRole.PATIENT)
        assert result is None

    def test_get_user_events_empty(self, manager):
        """get_user_events should return an empty list for a user with no events."""
        events = manager.get_user_events(user_id=9999, role=ViewRole.PATIENT)
        assert events == []


# -----------------------------------------------
# pending reviews
# -----------------------------------------------

class TestPendingReviews:
    def test_pending_reviews(self, manager):
        """Events that require expert review should appear in pending_reviews."""
        # emotional_eating and glucose_low templates set requires_review=True
        manager.process_event(
            user_id=1,
            event_type=EventType.TEXT_INPUT,
            raw_data={"text": "停不下来吃零食"},  # emotional_eating
        )

        pending = manager.get_pending_reviews()
        assert len(pending) >= 1
        assert any(r["expert_view"]["requires_review"] for r in pending)

    def test_no_pending_reviews_for_green(self, manager):
        """Task completion events should NOT require expert review."""
        manager.process_event(
            user_id=2,
            event_type=EventType.TASK_COMPLETE,
            raw_data={"task_id": "T-002"},
        )

        pending = manager.get_pending_reviews()
        # task_completed events should not be flagged for review
        for item in pending:
            assert item["event_type"] != "task_complete"

    def test_pending_reviews_glucose_low(self, manager):
        """Low glucose events should require expert review."""
        manager.process_event(
            user_id=3,
            event_type=EventType.DEVICE_DATA,
            raw_data={"cgm_value": 2.8},
        )

        pending = manager.get_pending_reviews()
        assert len(pending) >= 1
        glucose_pending = [
            r for r in pending
            if r.get("expert_view", {}).get("risk_assessment", {}).get("template_key") == "glucose_low"
        ]
        assert len(glucose_pending) >= 1

    def test_pending_reviews_empty(self, manager):
        """A manager with no events should return an empty pending list."""
        pending = manager.get_pending_reviews()
        assert pending == []
