"""Validation script to test scoring system with different agent types."""

import sys
import random
from pathlib import Path
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from env import Environment, models
from tasks import EasyTask, MediumTask, HardTask
from graders import SupportGrader
import json


class BaseAgent(ABC):
    """Abstract base class for agents."""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.action_history = []
    
    @abstractmethod
    def act(self, observation: Dict) -> models.Action:
        pass
    
    def reset(self) -> None:
        self.action_history = []


class RandomAgent(BaseAgent):
    """Agent that takes random actions."""
    
    def __init__(self, agent_id: str = "random_0"):
        """Initialize the random agent."""
        super().__init__(agent_id, "RandomAgent")
        self.actions = [
            ("send_password_reset", {"email": "john@example.com"}),
            ("send_password_reset", {"email": "wrong@example.com"}),
            ("request_logs", {}),
            ("reply_to_customer", {"content": "random response"}),
            ("reply_to_customer", {"content": "This is completely wrong"}),
            ("issue_refund", {}),
            ("close_ticket", {}),
            ("analyze_logs", {}),
        ]
    
    def act(self, observation: Dict) -> models.Action:
        """Take a completely random action."""
        tool_name, args = random.choice(self.actions)
        action = models.Action(tool_name=tool_name, tool_args=args)
        self.action_history.append(action)
        return action


class PerfectAgent(BaseAgent):
    """Agent that takes optimal actions for each task."""
    
    def __init__(self, agent_id: str = "perfect_0"):
        """Initialize the perfect agent."""
        super().__init__(agent_id, "PerfectAgent")
        self.task_type = None
        self.step = 0
    
    def reset(self) -> None:
        """Reset agent state."""
        super().reset()
        self.step = 0
        self.task_type = None
    
    def act(self, observation: dict) -> models.Action:
        """Take optimal action based on task type."""
        self.step += 1
        
        # Determine task type from observation
        obs_str = str(observation).lower() if observation else ""
        
        if "password" in obs_str and self.task_type != "medium":
            self.task_type = "easy"
        elif "refund" in obs_str:
            self.task_type = "medium"
        elif "process" in obs_str or "error" in obs_str or "api" in obs_str:
            self.task_type = "hard"
        
        # Perform optimal action based on task type
        if self.task_type == "easy":
            return self._perfect_easy_action()
        elif self.task_type == "medium":
            return self._perfect_medium_action()
        else:
            return self._perfect_hard_action()
    
    def _perfect_easy_action(self) -> models.Action:
        """Perfect action for easy task."""
        if self.step == 1:
            return models.Action(
                tool_name="send_password_reset",
                tool_args={"email": "john@example.com"}
            )
        else:
            return models.Action(
                tool_name="close_ticket",
                tool_args={}
            )
    
    def _perfect_medium_action(self) -> models.Action:
        """Perfect action for medium task."""
        if self.step == 1:
            return models.Action(
                tool_name="request_logs",
                tool_args={}
            )
        else:
            return models.Action(
                tool_name="reply_to_customer",
                tool_args={"content": "I cannot approve this refund as it is beyond the 30-day policy window. Our refund policy clearly states refunds are only available within 30 days of purchase. Please contact management if you have extenuating circumstances."}
            )
    
    def _perfect_hard_action(self) -> models.Action:
        """Perfect action for hard task."""
        if self.step == 1:
            return models.Action(
                tool_name="request_logs",
                tool_args={}
            )
        elif self.step == 2:
            return models.Action(
                tool_name="reply_to_customer",
                tool_args={"content": "Based on the error logs retrieved, I can see the issue is ERR-99. The solution is to update your client to v2.1. This resolves the compatibility issue with our API."}
            )
        else:
            return models.Action(
                tool_name="close_ticket",
                tool_args={}
            )


class ImperfectAgent(BaseAgent):
    """Agent that makes occasional mistakes."""
    
    def __init__(self, agent_id: str = "imperfect_0"):
        """Initialize the imperfect agent."""
        super().__init__(agent_id, "ImperfectAgent")
        self.step = 0
        self.task_type = None
    
    def reset(self) -> None:
        """Reset agent state."""
        super().reset()
        self.step = 0
        self.task_type = None
    
    def act(self, observation: dict) -> models.Action:
        """Take action with occasional mistakes for the actual task."""
        self.step += 1
        
        # Detect task type from observation
        obs_str = str(observation).lower() if observation else ""
        
        if "password" in obs_str:
            self.task_type = "easy"
        elif "refund" in obs_str:
            self.task_type = "medium"
        else:
            self.task_type = "hard"
        
        # Task-specific behavior
        if self.task_type == "easy":
            return self._easy_action()
        elif self.task_type == "medium":
            return self._medium_action()
        else:
            return self._hard_action()
    
    def _easy_action(self) -> models.Action:
        """Imperfect easy task behavior - 30% error on step 1."""
        if self.step == 1:
            if random.random() < 0.3:  # 30% chance of wrong action
                return models.Action(tool_name="close_ticket", tool_args={})
            else:
                return models.Action(
                    tool_name="send_password_reset",
                    tool_args={"email": "john@example.com"}
                )
        else:
            return models.Action(tool_name="close_ticket", tool_args={})
    
    def _medium_action(self) -> models.Action:
        """Imperfect medium task behavior - 40% error step 1, 45% weak response step 2."""
        if self.step == 1:
            if random.random() < 0.40:  # 40% chance to skip logs
                return models.Action(
                    tool_name="reply_to_customer",
                    tool_args={"content": "We cannot refund this."}
                )
            else:
                return models.Action(tool_name="request_logs", tool_args={})
        else:
            # 45% chance of weak response
            if random.random() < 0.45:
                return models.Action(
                    tool_name="reply_to_customer",
                    tool_args={"content": "No refund available."}
                )
            else:
                return models.Action(
                    tool_name="reply_to_customer",
                    tool_args={"content": "Our policy only allows refunds within 30 days of purchase."}
                )
    
    def _hard_action(self) -> models.Action:
        """Imperfect hard task behavior - 35% error step 1, 40% weak response step 2."""
        if self.step == 1:
            if random.random() < 0.35:  # 35% chance to skip logs
                return models.Action(
                    tool_name="reply_to_customer",
                    tool_args={"content": "Try update to v2.1"}
                )
            else:
                return models.Action(tool_name="request_logs", tool_args={})
        elif self.step == 2:
            if random.random() < 0.40:  # 40% chance of weak response
                return models.Action(
                    tool_name="reply_to_customer",
                    tool_args={"content": "Not sure what the fix is."}
                )
            else:
                return models.Action(
                    tool_name="reply_to_customer",
                    tool_args={"content": "Update your client to v2.1 to fix ERR-99."}
                )
        else:
            return models.Action(tool_name="close_ticket", tool_args={})


def run_episode(env: Environment, agent: BaseAgent, max_steps: int, debug: bool = False) -> Tuple[float, List[float]]:
    """
    Run a single episode and return final task score and individual step rewards.
    
    The final score is the reward from the last step (after task completion),
    as the grading system accumulates context across steps.
    
    Args:
        env: Environment instance
        agent: Agent instance
        max_steps: Maximum number of steps
        debug: Whether to print step-by-step details
        
    Returns:
        Tuple of (final_score, step_rewards)
    """
    state = env.reset()
    agent.reset()
    final_score = 0.0
    step_rewards = []
    actions = []
    
    for step in range(max_steps):
        action = agent.act(state)
        actions.append(action.tool_name)
        state, reward_obj, done, info = env.step(action)
        
        # Extract reward value from Reward object
        if hasattr(reward_obj, 'value'):
            reward_value = reward_obj.value
        else:
            reward_value = 0.0
        
        # Track all step rewards
        step_rewards.append(reward_value)
        final_score = reward_value  # Use final step's reward as task score
        
        if debug and step < 3:
            print(f"      DEBUG Step {step+1}: action={action.tool_name}, score={reward_value:.3f}")
        
        if done:
            break
    
    if debug:
        print(f"      DEBUG Actions: {' → '.join(actions)}")
    
    return final_score, step_rewards


def test_difficulty_level(
    difficulty: str,
    agent_class: type,
    agent_name: str,
    num_episodes: int = 5,
    max_steps: int = 20,
    verbose: bool = False
) -> Dict[str, float]:
    """
    Test a specific difficulty level with a specific agent.
    
    Args:
        difficulty: 'easy', 'medium', or 'hard'
        agent_class: Agent class to instantiate
        agent_name: Name of agent type
        num_episodes: Number of episodes to run
        max_steps: Maximum steps per episode
        verbose: Print debugging info
        
    Returns:
        Dictionary with statistics: mean, min, max, std
    """
    # Create appropriate task
    if difficulty == 'easy':
        task = EasyTask(
            task_id="easy_ticket_1",
            title="Password Reset",
            description="User needs password reset"
        )
    elif difficulty == 'medium':
        task = MediumTask(
            task_id="medium_ticket_1",
            title="Refund Request",
            description="Customer requesting refund after 30 days"
        )
    else:
        task = HardTask(
            task_id="hard_ticket_1",
            title="Technical Error",
            description="API returning 500 error"
        )
    
    grader = SupportGrader()
    env = Environment(task, grader, max_steps=max_steps)
    
    rewards = []
    detailed_rewards = []
    
    for episode in range(num_episodes):
        agent = agent_class()
        # Enable debug for imperfect agents on first episode
        is_debug = (agent_name == "ImperfectAgent" and episode == 0)
        final_score, step_rewards = run_episode(env, agent, max_steps, debug=is_debug)
        rewards.append(final_score)
        detailed_rewards.append({
            'episode': episode + 1,
            'total': final_score,
            'steps': len(step_rewards),
            'step_rewards': step_rewards
        })
        
        if verbose:
            print(f"    Episode {episode + 1}: score={final_score:.3f}, steps={len(step_rewards)}")
            if step_rewards:
                print(f"      Step rewards: {[f'{r:.3f}' for r in step_rewards[:5]]}")
    
    # Calculate statistics
    import statistics
    stats = {
        'mean': statistics.mean(rewards),
        'min': min(rewards),
        'max': max(rewards),
        'std': statistics.stdev(rewards) if len(rewards) > 1 else 0.0,
        'detailed': detailed_rewards
    }
    
    return stats


def print_results(results: Dict) -> None:
    """Print test results in formatted table."""
    print("\n" + "=" * 100)
    print("VALIDATION RESULTS: OpenEnv Scoring System")
    print("=" * 100)
    
    expected = {
        'easy': {'perfect': 0.85, 'imperfect': 0.6, 'random': 0.2},
        'medium': {'perfect': 0.75, 'imperfect': 0.5, 'random': 0.2},
        'hard': {'perfect': 0.65, 'imperfect': 0.4, 'random': 0.1}
    }
    
    for difficulty in ['easy', 'medium', 'hard']:
        print(f"\n{'TASK':<12} {'AGENT':<15} {'Expected':<12} {'Actual':<12} {'Status':<10}")
        print("-" * 60)
        
        for agent_type in ['perfect', 'imperfect', 'random']:
            key = f"{difficulty}_{agent_type}"
            if key in results:
                actual = results[key]['mean']
                expected_val = expected[difficulty][agent_type]
                
                # Check if within reasonable range (±0.15)
                tolerance = 0.15
                if abs(actual - expected_val) <= tolerance:
                    status = "✓ PASS"
                else:
                    status = "✗ FAIL"
                
                print(f"{difficulty:<12} {agent_type:<15} {expected_val:<12.2f} {actual:<12.2f} {status:<10}")
                
                # Print detailed breakdown for first episode
                if results[key]['detailed']:
                    first = results[key]['detailed'][0]
                    print(f"  └─ Episode 1: {first['total']:.2f} ({first['steps']} steps)")
    
    print("\n" + "=" * 100)
    print("VALIDATION COMPLETE")
    print("=" * 100)


def main() -> None:
    """Main validation entry point."""
    print("\n" + "=" * 100)
    print("OpenEnv Scoring System Validation")
    print("=" * 100)
    print("\nTesting with expected baselines:")
    print("- Perfect agent: Follows optimal sequence")
    print("- Imperfect agent: Occasional errors")
    print("- Random agent: Random actions\n")
    
    results = {}
    
    # Test all combinations
    for difficulty in ['easy', 'medium', 'hard']:
        print(f"\nTesting {difficulty.upper()} task...")
        
        for agent_class, agent_name in [
            (PerfectAgent, 'perfect'),
            (ImperfectAgent, 'imperfect'),
            (RandomAgent, 'random')
        ]:
            key = f"{difficulty}_{agent_name}"
            print(f"  {agent_name.capitalize():15s}...", end=' ')
            stats = test_difficulty_level(difficulty, agent_class, agent_name, num_episodes=3)
            results[key] = stats
            print(f"Mean: {stats['mean']:.3f} ±{stats['std']:.3f}")
    
    # Print summary
    print_results(results)


if __name__ == "__main__":
    main()
