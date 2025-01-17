import shutil
from pathlib import Path
from typing import Generator

import pytest

from se.modules.agent_controller import AgentController


@pytest.fixture
def persist_dir() -> Generator[Path, None, None]:
    path = Path("test_persist")
    path.mkdir(exist_ok=True)
    yield path
    if path.exists():
        shutil.rmtree(path)


def test_validate_purchase_agreement_valid(persist_dir: Path) -> None:
    agent = AgentController(persist_dir=persist_dir)
    data = {
        "document_type": "Purchase Agreement",
        "analysis_steps": [
            {
                "category": "obligations",
                "applicable": True,
                "type": "table",
                "columns": ["Party", "Obligation"],
                "reason": "Purchase agreements typically outline the responsibilities of the buyer and seller.",
            }
        ],
    }
    assert agent._validate_analysis_steps(data) is True


def test_validate_purchase_agreement_missing_document_type(persist_dir: Path) -> None:
    agent = AgentController(persist_dir=persist_dir)
    data = {"analysis_steps": [{"category": "obligations", "applicable": True}]}
    assert agent._validate_analysis_steps(data) is False


def test_validate_purchase_agreement_invalid_analysis_steps(persist_dir: Path) -> None:
    agent = AgentController(persist_dir=persist_dir)
    data = {"document_type": "Purchase Agreement", "analysis_steps": "invalid"}
    assert agent._validate_analysis_steps(data) is False


def test_validate_purchase_agreement_empty_steps(persist_dir: Path) -> None:
    agent = AgentController(persist_dir=persist_dir)
    data = {"document_type": "Purchase Agreement", "analysis_steps": []}
    assert agent._validate_analysis_steps(data) is False


def test_validate_purchase_agreement_invalid_step_structure(persist_dir: Path) -> None:
    agent = AgentController(persist_dir=persist_dir)
    data = {
        "document_type": "Purchase Agreement",
        "analysis_steps": [
            {"category": "obligations", "applicable": "invalid", "type": "invalid_type"}
        ],
    }
    assert agent._validate_analysis_steps(data) is False


def test_validate_purchase_agreement_invalid_columns(persist_dir: Path) -> None:
    agent = AgentController(persist_dir=persist_dir)
    data = {
        "document_type": "Purchase Agreement",
        "analysis_steps": [
            {
                "category": "obligations",
                "applicable": True,
                "type": "table",
                "columns": "invalid",
                "reason": "Purchase agreements typically outline the responsibilities of the buyer and seller.",
            }
        ],
    }
    assert agent._validate_analysis_steps(data) is False
