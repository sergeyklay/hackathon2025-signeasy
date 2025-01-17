"""Tests for the progress tracker module."""

import pytest
from flask import session

from se.modules.progress_tracker import (
    RECIPIENT_WORKFLOW,
    SENDER_WORKFLOW,
    ProgressTracker,
    get_tracker,
)


@pytest.fixture
def tracker(request_context):
    """Create a test tracker instance with request context."""
    return ProgressTracker("test", ["Step1", "Step2", "Step3"])


def test_tracker_initialization(tracker):
    """Test tracker initialization."""
    assert tracker.workflow_id == "test"
    assert tracker.steps == ["Step1", "Step2", "Step3"]
    assert tracker._session_key == "progress_tracker_test"


def test_set_current_step(tracker):
    """Test setting the current step."""
    tracker.set_current_step("Step2")
    assert session.get("progress_tracker_test") == "Step2"


def test_set_invalid_step(tracker):
    """Test setting an invalid step name."""
    tracker.set_current_step("InvalidStep")
    assert "progress_tracker_test" not in session


def test_get_current_step_none(tracker):
    """Test getting current step when none is set."""
    assert tracker.get_current_step() is None


def test_get_current_step(tracker):
    """Test getting current step after setting it."""
    tracker.set_current_step("Step2")
    assert tracker.get_current_step() == "Step2"


def test_get_progress_steps_no_current(tracker):
    """Test getting progress steps when no current step is set."""
    steps = tracker.get_progress_steps()
    assert len(steps) == 3
    assert all(not step["completed"] for step in steps)
    assert all(not step["current"] for step in steps)


def test_get_progress_steps_with_current(tracker):
    """Test getting progress steps with a current step."""
    tracker.set_current_step("Step2")
    steps = tracker.get_progress_steps()

    assert steps[0]["name"] == "Step1"
    assert steps[0]["completed"] is True
    assert steps[0]["current"] is False

    assert steps[1]["name"] == "Step2"
    assert steps[1]["completed"] is False
    assert steps[1]["current"] is True

    assert steps[2]["name"] == "Step3"
    assert steps[2]["completed"] is False
    assert steps[2]["current"] is False


def test_reset_tracker(tracker):
    """Test resetting the tracker state."""
    tracker.set_current_step("Step2")
    assert tracker.get_current_step() == "Step2"

    tracker.reset()
    assert tracker.get_current_step() is None


def test_get_tracker_sender(request_context):
    """Test getting a sender workflow tracker."""
    tracker = get_tracker("sender")
    assert tracker.workflow_id == SENDER_WORKFLOW["id"]
    assert tracker.steps == SENDER_WORKFLOW["steps"]


def test_get_tracker_recipient(request_context):
    """Test getting a recipient workflow tracker."""
    tracker = get_tracker("recipient")
    assert tracker.workflow_id == RECIPIENT_WORKFLOW["id"]
    assert tracker.steps == RECIPIENT_WORKFLOW["steps"]


def test_get_tracker_invalid(request_context):
    """Test getting tracker with invalid workflow ID."""
    with pytest.raises(ValueError) as exc:
        get_tracker("invalid_workflow")
    assert str(exc.value) == "Unknown workflow ID: invalid_workflow"
