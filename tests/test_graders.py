"""Tests for the graders module."""
import pytest
from graders import SupportGrader


def test_support_grader_initialization():
    """Test support grader initialization."""
    grader = SupportGrader()
    assert grader is not None
    assert grader.scores == []


def test_support_grader_grading(sample_grader):
    """Test support grader grading."""
    state = {'test': 'value'}
    reward = sample_grader.grade(state, is_complete=True)
    assert isinstance(reward, float)
    assert 0 <= reward <= 1


def test_score_history(sample_grader):
    """Test score history tracking."""
    sample_grader.grade({'test': 'value'}, is_complete=True)
    sample_grader.grade({'test': 'value'}, is_complete=False)
    history = sample_grader.get_score_history()
    assert len(history) == 2
