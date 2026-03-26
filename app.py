"""Main application entry point for OpenEnv."""
import logging
from pathlib import Path
from env import Environment
from tasks import EasyTask
from graders import SupportGrader
from agents import DummyAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main application function."""
    logger.info("Starting OpenEnv application")
    
    # Initialize components
    task = EasyTask(
        task_id='app_task_1',
        title='Application Test Task',
        description='A test task for the application',
        initial_data={'status': 'open', 'priority': 'high'}
    )
    
    grader = SupportGrader()
    agent = DummyAgent()
    env = Environment(task, grader, max_steps=50)
    
    # Run episode
    state = env.reset()
    logger.info(f"Environment initialized with state: {state}")
    
    total_reward = 0
    for step in range(50):
        action = agent.act(state)
        state, reward, done, info = env.step(action)
        total_reward += reward
        
        if step % 10 == 0:
            logger.info(f"Step {step}: Reward = {reward:.3f}")
        
        if done:
            logger.info(f"Task completed at step {step}")
            break
    
    logger.info(f"Episode finished. Total reward: {total_reward:.3f}")
    return total_reward


if __name__ == '__main__':
    main()
