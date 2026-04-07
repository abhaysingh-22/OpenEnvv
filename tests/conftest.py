"""Pytest fixtures for OpenEnv test suite."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def env():
    """Provide a fresh SupportEnvironment instance."""
    from support_env.server.support_environment import SupportEnvironment
    return SupportEnvironment()


