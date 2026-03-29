"""Pytest fixtures for OpenEnv test suite."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_task():
    from tasks import EasyTask
    return EasyTask(
        task_id="test_1",
        title="Test Task",
        description="A test task",
        initial_data={"test": True},
    )


@pytest.fixture
def sample_grader():
    from graders import SupportGrader
    return SupportGrader()
