"""Main script to run OpenEnv with configurations."""
import argparse
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from env import Environment
from tasks import EasyTask, MediumTask, HardTask
from graders import SupportGrader
from agents import DummyAgent, HFAgent
from config import settings


def load_tasks(difficulty: str):
    """Load tasks based on difficulty."""
    if difficulty == 'easy':
        path = settings.TICKETS_EASY_PATH
        task_class = EasyTask
    elif difficulty == 'medium':
        path = settings.TICKETS_MEDIUM_PATH
        task_class = MediumTask
    else:
        path = settings.TICKETS_HARD_PATH
        task_class = HardTask
    
    # Load tasks from JSON file if exists
    tasks = []
    return tasks


def create_agent(agent_type: str, agent_id: str):
    """Create an agent based on type."""
    if agent_type == 'dummy':
        return DummyAgent(agent_id)
    elif agent_type == 'hf':
        config = settings.AGENT_CONFIG.get('hf', {})
        return HFAgent(agent_id, config['model_name'], config)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def run_episode(env, agent, max_steps: int):
    """Run a single episode."""
    state = env.reset()
    total_reward = 0
    
    for step in range(max_steps):
        action = agent.act(state)
        state, reward, done, info = env.step(action)
        total_reward += reward
        
        if done:
            break
    
    return total_reward, info


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run OpenEnv')
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], 
                       default='easy', help='Task difficulty')
    parser.add_argument('--agent', choices=['dummy', 'hf'], 
                       default='dummy', help='Agent type')
    parser.add_argument('--episodes', type=int, default=1, 
                       help='Number of episodes')
    parser.add_argument('--max-steps', type=int, default=100,
                       help='Maximum steps per episode')
    
    args = parser.parse_args()
    
    print(f"Running OpenEnv with:")
    print(f"  Difficulty: {args.difficulty}")
    print(f"  Agent: {args.agent}")
    print(f"  Episodes: {args.episodes}")
    print(f"  Max steps: {args.max_steps}\n")
    
    # Create sample task
    task = EasyTask(
        task_id='test_1',
        title='Test Task',
        description='A test task',
        initial_data={'status': 'open'}
    )
    
    grader = SupportGrader()
    agent = create_agent(args.agent, f"{args.agent}_0")
    env = Environment(task, grader, max_steps=args.max_steps)
    
    rewards = []
    for episode in range(args.episodes):
        reward, info = run_episode(env, agent, args.max_steps)
        rewards.append(reward)
        print(f"Episode {episode + 1}: Reward = {reward:.3f}")
    
    print(f"\nAverage reward: {sum(rewards) / len(rewards):.3f}")


if __name__ == '__main__':
    main()
