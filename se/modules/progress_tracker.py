"""Progress tracker module for managing step-based workflows."""

from typing import Dict, List, Optional

from flask import session


class ProgressTracker:
    """Manages progress steps for different workflows in the application."""

    def __init__(self, workflow_id: str, steps: List[str]):
        """Initialize a progress tracker for a specific workflow.

        Args:
            workflow_id: Unique identifier for the workflow (e.g. 'sender', 'recipient')
            steps: List of step names in order
        """
        self.workflow_id = workflow_id
        self.steps = steps
        self._session_key = f"progress_tracker_{workflow_id}"

    def get_current_step(self) -> Optional[str]:
        """Get the current active step name."""
        return session.get(self._session_key)

    def set_current_step(self, step: str) -> None:
        """Set the current active step.

        Args:
            step: Name of the step to set as current
        """
        if step in self.steps:
            session[self._session_key] = step

    def get_progress_steps(self) -> List[Dict]:
        """Get the progress steps with their current state.

        Returns:
            List of dicts containing step info with completion status
        """
        current_step = self.get_current_step()
        current_step_index = self.steps.index(current_step) if current_step else 0

        return [
            {
                "name": step,
                "completed": i < current_step_index,
                "current": step == current_step,
            }
            for i, step in enumerate(self.steps)
        ]

    def reset(self) -> None:
        """Reset the progress tracker state."""
        if self._session_key in session:
            session.pop(self._session_key)


# Pre-defined workflow configurations
SENDER_WORKFLOW = {
    "id": "sender",
    "steps": ["Welcome", "Upload", "Review", "Sign", "Send"],
}

RECIPIENT_WORKFLOW = {
    "id": "recipient",
    "steps": ["Welcome", "Deal", "Review", "Sign", "Complete"],
}


def get_tracker(workflow_id: str) -> ProgressTracker:
    """Factory function to get a configured ProgressTracker instance.

    Args:
        workflow_id: ID of the workflow to get tracker for

    Returns:
        Configured ProgressTracker instance
    """
    workflows = {"sender": SENDER_WORKFLOW, "recipient": RECIPIENT_WORKFLOW}

    workflow = workflows.get(workflow_id)
    if not workflow:
        raise ValueError(f"Unknown workflow ID: {workflow_id}")

    return ProgressTracker(workflow["id"], workflow["steps"])
