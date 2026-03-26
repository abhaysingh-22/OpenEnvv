"""Pytest configuration and fixtures."""
import pytest
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_task():
    """Provide a sample task for testing."""
    from tasks import EasyTask
    return EasyTask(
        task_id='test_1',
        title='Test Task',
        description='A test task',
        initial_data={'test': True}
    )


@pytest.fixture
def sample_grader():
    """Provide a sample grader for testing."""
    from graders import SupportGrader
    return SupportGrader()


@pytest.fixture
def sample_agent():
    """Provide a sample agent for testing."""
    from agents import DummyAgent
    return DummyAgent()
