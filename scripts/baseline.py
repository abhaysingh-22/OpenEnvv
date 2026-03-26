"""Baseline script for running OpenEnv with dummy agent."""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from env import Environment
from tasks import EasyTask
from graders import SupportGrader
from agents import DummyAgent


def run_baseline():
    """Run baseline evaluation with dummy agent."""
    print("Starting OpenEnv baseline run...")
    
    # Initialize task
    task = EasyTask(
        task_id='baseline_1',
        title='Baseline Test',
        description='A baseline test task',
        initial_data={'status': 'open'}
    )
    
    # Initialize grader
    grader = SupportGrader()
    
    # Initialize agent
    agent = DummyAgent()
    
    # Create environment
    env = Environment(task, grader, max_steps=10)
    
    # Reset environment
    state = env.reset()
    print(f"Initial state: {state}")
    
    # Run episode
    total_reward = 0
    for step in range(10):
        action = agent.act(state)
        print(f"Step {step + 1}: Action = {action}")
        
        state, reward, done, info = env.step(action)
        total_reward += reward
        
        print(f"  Reward: {reward:.3f}, Done: {done}")
        
        if done:
            print(f"Task completed at step {step + 1}")
            break
    
    print(f"\nBaseline complete!")
    print(f"Total reward: {total_reward:.3f}")
    print(f"Agent actions: {agent.get_action_history()}")


if __name__ == '__main__':
    run_baseline()
