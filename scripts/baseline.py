"""Baseline script for running OpenEnv with OpenAI API."""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try importing OpenAI, but allow fallback if not installed or no key
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from env.environment import Environment
from env.models import Action
from tasks.easy import EasyTask
from tasks.medium import MediumTask
from tasks.hard import HardTask
from graders.support_grader import SupportGrader

load_dotenv()


def get_agent_action(client, obs_dict, history):
    """Simple inference logic using OpenAI."""
    system_prompt = (
        "You are an AI customer support agent. Help the customer resolve their issue. "
        "You have specific tools available. Respond ONLY with a JSON object in this format: "
        '{"tool_name": "...", "tool_args": {"arg1": "value1"}}. '
        "\\nAvailable tools: 'send_password_reset', 'reply_to_customer', 'issue_refund', 'close_ticket', 'request_logs'. "
        "\\nFor 'reply_to_customer', provide {'content': 'message'}. "
        "\\nFor 'send_password_reset', provide {'email': 'user_email'}. "
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Observation: {obs_dict}\\nHistory: {history}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.0
    )
    
    content = response.choices[0].message.content
    try:
        import re
        json_str = re.search(r'\\{.*\\}', content, re.DOTALL).group()
        action_dict = json.loads(json_str)
        return Action(**action_dict)
    except Exception as e:
        return Action(tool_name="reply_to_customer", tool_args={"content": "I am having trouble processing that."})


def get_mock_action(task_id: str, step_num: int) -> Action:
    """
    Fallback scripted agent with perfect actions (multi-step workflows).
    
    This agent:
    - Easy: Step 1 sends reset, Step 2 closes
    - Medium: Step 1 checks policy, Step 2 denies with policy explanation
    - Hard: Step 1 requests logs, Step 2 provides solution
    """
    if task_id == "easy_ticket_1":
        if step_num == 1:
            # Step 1: Send password reset
            return Action(tool_name="send_password_reset", tool_args={"email": "john@example.com"})
        else:
            # Step 2+: Close the ticket
            return Action(tool_name="close_ticket", tool_args={})
    
    elif task_id == "medium_ticket_1":
        if step_num == 1:
            # Step 1: Check policy by requesting logs/system data
            return Action(tool_name="request_logs", tool_args={})
        else:
            # Step 2+: Respond with policy-based denial
            return Action(
                tool_name="reply_to_customer",
                tool_args={"content": "Your purchase is over 30 days old. According to our refund policy, we cannot process refunds after 30 days. I'm unable to issue a refund. Is there anything else I can help you with?"}
            )
    
    elif task_id == "hard_ticket_1":
        if step_num == 1:
            # Step 1: Request logs to investigate
            return Action(tool_name="request_logs", tool_args={})
        else:
            # Step 2+: Provide solution based on error code
            return Action(
                tool_name="reply_to_customer",
                tool_args={"content": "Based on the error logs showing ERR-99, the issue is a client version incompatibility. Please update your client to v2.1 to resolve the connection issue. This version includes the fix for the /process endpoint. Let me know if that resolves the problem."}
            )
    
    # Fallback
    return Action(tool_name="close_ticket", tool_args={})


def run_baseline():
    """Run baseline evaluation with improved multi-step workflows."""
    api_key = os.getenv("OPENAI_API_KEY")
    client = None
    if api_key and OpenAI:
        client = OpenAI(api_key=api_key)
        print("Using OpenAI API for baseline.")
    else:
        print("No OPENAI_API_KEY found. Running in MOCK Mode with scripted perfect actions.")
        print("=" * 70)
        
    tasks = [EasyTask(), MediumTask(), HardTask()]
    grader = SupportGrader()
    
    total_baseline_score = 0.0
    
    for task in tasks:
        print(f"\n--- Running {task.title} ({task.task_id}) ---")
        env = Environment(task, grader, max_steps=10)
        obs = env.reset()
        
        # Reset grader episode state for new task
        grader.reset_episode()
        
        cumulative_reward = 0.0
        step_rewards = []
        
        for step in range(10):
            if client:
                action = get_agent_action(client, obs.model_dump(), getattr(obs, 'history', []))
            else:
                action = get_mock_action(task.task_id, step + 1)
                
            print(f"\nAgent Action (Step {step+1}): {action.tool_name}")
            if action.tool_args:
                print(f"  Arguments: {action.tool_args}")
            
            obs, reward, done, info = env.step(action)
            step_rewards.append(reward.value)
            cumulative_reward += reward.value  # Accumulate rewards across episode
            print(f"Step {step+1} Reward: {reward.value:.3f}")
            print(f"Info: {reward.info}")
            
            if done:
                print(f"\n✓ Task completed at step {step + 1}")
                break
        
        # Normalize score by number of steps (average per step)
        avg_episode_reward = cumulative_reward / len(step_rewards) if step_rewards else 0.0
        
        # Normalize to 0-1 range (cumulative reward / max possible)
        # Max possible is ~1.0-1.5 per task, so factor it
        normalized_score = min(1.0, cumulative_reward / 1.5)
        
        print(f"\n{'='*70}")
        print(f"Cumulative Score for {task.title}: {cumulative_reward:.3f}")
        print(f"Average Per-Step Reward: {avg_episode_reward:.3f}")
        print(f"Normalized Final Score: {normalized_score:.3f}")
        print(f"Reward Progression: {' → '.join([f'{r:.2f}' for r in step_rewards])}")
        print(f"Episode Length: {len(step_rewards)} steps")
        total_baseline_score += normalized_score
        
    print(f"\n{'='*70}")
    print(f"SUMMARY - Perfect Agent Performance:")
    print(f"  Easy Task (Password Reset): 2-step workflow")
    print(f"  Medium Task (Refund Request): 2-step workflow with policy check")
    print(f"  Hard Task (Technical Error): 2-step workflow with investigation")
    print(f"\nTotal Baseline Score: {total_baseline_score:.2f} out of 3")
    print(f"Average Score: {total_baseline_score/3:.3f}")
    print(f"\nScore Ranges (Expected):")
    print(f"  Perfect Agent: ~0.75-0.85 per task")
    print(f"  Imperfect Agent: ~0.40-0.60 per task")
    print(f"  Random Agent: ~0.0-0.25 per task")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    run_baseline()
