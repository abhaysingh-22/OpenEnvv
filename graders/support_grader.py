"""Support grader for customer support tasks with advanced reward shaping."""
from typing import Any, Dict, List
from .base_grader import BaseGrader
from env.models import State, Action, Reward
from .rewards import RewardCalculator


class SupportGrader(BaseGrader):
    """
    Grader for customer support and ticket tasks.
    
    Uses advanced reward shaping with:
    - State tracking across steps
    - Gradual reward accumulation
    - Efficiency penalties
    - Multi-step task validation
    """
    
    def __init__(self, answer_key: Dict[str, Any] = None, policy: Dict[str, Any] = None):
        """Initialize the support grader."""
        super().__init__()
        self.answer_key = answer_key or {}
        self.policy = policy or {}
        self.calculator = RewardCalculator(efficiency_penalty=0.05)
        self.episode_state: Dict[str, Any] = {}
        self.reset_episode()
    
    def reset_episode(self) -> None:
        """Reset episode state for a new task."""
        self.episode_state = {
            'task_id': None,
            'step_count': 0,
            'action_history': [],
            'logs_requested': False,
            'policy_checked': False,
            'verification_sent': False,
            'final_response_given': False,
            'cumulative_reward': 0.0
        }
        self.calculator.reset_history()
    
    def grade(self, state: State, action: Action, is_complete: bool) -> Reward:
        """
        Grade the support task completion with state tracking.
        
        Uses multi-step workflows:
        - Easy: Verify action → Execute
        - Medium: Check policy → Respond
        - Hard: Request logs → Diagnose → Respond
        """
        # Initialize episode state if needed
        if not self.episode_state['task_id']:
            self.episode_state['task_id'] = state.task_id
        
        self.episode_state['step_count'] += 1
        step_reward = 0.0
        info = ""
        
        # ========== EASY TASK: Password Reset ==========
        if state.task_id == "easy_ticket_1":
            step_reward = self._grade_easy_task(action, step_number=self.episode_state['step_count'])
            info = self._get_easy_task_info(action, step_reward)
        
        # ========== MEDIUM TASK: Refund Request ==========
        elif state.task_id == "medium_ticket_1":
            step_reward = self._grade_medium_task(action, step_number=self.episode_state['step_count'])
            info = self._get_medium_task_info(action, step_reward)
        
        # ========== HARD TASK: Technical Troubleshooting ==========
        elif state.task_id == "hard_ticket_1":
            step_reward = self._grade_hard_task(action, state, step_number=self.episode_state['step_count'])
            info = self._get_hard_task_info(action, step_reward)
        
        # Clamp reward to valid range
        step_reward = max(0.0, min(1.0, step_reward))
        self.episode_state['cumulative_reward'] = step_reward
        
        self.scores.append(step_reward)
        
        return Reward(
            value=step_reward,
            is_complete=is_complete,
            info=info.strip()
        )
    
    def _grade_easy_task(self, action: Action, step_number: int) -> float:
        """
        Grade easy task (Password Reset) - requires 1-2 steps minimum.
        
        Step 1: Should use send_password_reset
        Step 2+: Should close the ticket
        """
        if step_number == 1:
            if action.tool_name == "send_password_reset" and action.tool_args.get("email") == "john@example.com":
                # First step correct: good routing + response
                reward = self.calculator.calculate_step_reward(
                    routing_score=0.4,      # Perfect routing
                    response_quality=0.25,  # Good response
                    tone_quality=0.15,      # Good tone
                    step_number=step_number
                )
                self.episode_state['verification_sent'] = True
                return reward
            elif action.tool_name == "reply_to_customer":
                # Wrong action on step 1
                return self.calculator.calculate_penalty("wrong_routing")
            else:
                return self.calculator.calculate_penalty("invalid_action")
        
        else:  # step 2+
            if action.tool_name == "close_ticket" and self.episode_state['verification_sent']:
                # Proper closure after password reset
                reward = self.calculator.calculate_step_reward(
                    routing_score=0.25,     # Good routing (completing task)
                    response_quality=0.15,  # Adequate response (closure)
                    tone_quality=0.1,       # Adequate tone
                    step_number=step_number
                )
                # No extra penalty for step 2 since it's part of workflow
                return reward
            elif action.tool_name == "send_password_reset":
                # Duplicate action
                return 0.0
            else:
                return self.calculator.calculate_penalty("invalid_action")
    
    def _grade_medium_task(self, action: Action, step_number: int) -> float:
        """
        Grade medium task (Refund Request) - requires 2-3 steps minimum.
        
        Step 1: Should check policy/system (request_logs style) or start response
        Step 2+: Should deny with policy explanation
        """
        if step_number == 1:
            # First step: encourage policy checking or direct response
            if action.tool_name == "request_logs":
                # Checking system/policy data
                self.episode_state['policy_checked'] = True
                reward = self.calculator.calculate_step_reward(
                    routing_score=0.2,
                    response_quality=0.2,
                    tone_quality=0.1,
                    step_number=step_number
                )
                return reward
            elif action.tool_name == "reply_to_customer":
                # Immediate response without checking (suboptimal but may still reward)
                content = str(action.tool_args.get("content", "")).lower()
                if any(keyword in content for keyword in ["deny", "policy", "cannot", "30"]):
                    return self.calculator.calculate_step_reward(
                        routing_score=0.3,
                        response_quality=0.2,
                        tone_quality=0.1,
                        step_number=step_number
                    )
                else:
                    return self.calculator.calculate_penalty("weak_response")
            elif action.tool_name == "issue_refund":
                return self.calculator.calculate_penalty("policy_violation")
            else:
                return self.calculator.calculate_penalty("invalid_action")
        
        else:  # step 2+
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(keyword in content for keyword in ["deny", "policy", "cannot", "30"]):
                    reward = self.calculator.calculate_step_reward(
                        routing_score=0.4,      # Good routing
                        response_quality=0.25,  # Clear response
                        tone_quality=0.2,       # Professional tone
                        step_number=step_number
                    )
                    # Bonus for completing efficiently
                    bonus = self.calculator.calculate_completion_bonus(step_number, min_steps=2)
                    return reward + bonus
                else:
                    return self.calculator.calculate_penalty("weak_response")
            elif action.tool_name == "issue_refund":
                return self.calculator.calculate_penalty("policy_violation")
            elif action.tool_name == "close_ticket":
                # Closing without proper response
                return self.calculator.calculate_penalty("weak_response")
            else:
                return self.calculator.calculate_penalty("invalid_action")
    
    def _grade_hard_task(self, action: Action, state: State, step_number: int) -> float:
        """
        Grade hard task (Technical Troubleshooting) - requires 3+ steps.
        
        Step 1: Should request logs
        Step 2: Can ask more questions or provide response (but logs help)
        Step 3+: Should provide correct fix based on logs
        """
        if step_number == 1:
            if action.tool_name == "request_logs":
                # Correct first step
                self.episode_state['logs_requested'] = True
                reward = self.calculator.calculate_step_reward(
                    routing_score=0.2,      # Investigating
                    response_quality=0.15,  # Proactive
                    tone_quality=0.15,      # Professional
                    step_number=step_number
                )
                return reward
            elif action.tool_name == "reply_to_customer":
                # Responding without logs (suboptimal)
                content = str(action.tool_args.get("content", "")).lower()
                if "update client to v2.1" in content or "v2.1" in content:
                    # Right answer but wrong path (no investigation)
                    reward = self.calculator.calculate_step_reward(
                        routing_score=0.2,
                        response_quality=0.2,
                        tone_quality=0.1,
                        step_number=step_number
                    )
                    return reward
                else:
                    return self.calculator.calculate_penalty("weak_response")
            else:
                return self.calculator.calculate_penalty("invalid_action")
        
        elif step_number == 2:
            if self.episode_state['logs_requested']:
                # After logs requested
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if "update client to v2.1" in content or "v2.1" in content:
                        # Correct response after investigation
                        reward = self.calculator.calculate_step_reward(
                            routing_score=0.4,      # Good solution based on logs
                            response_quality=0.25,  # Clear instructions
                            tone_quality=0.2,       # Helpful tone
                            step_number=step_number
                        )
                        self.episode_state['final_response_given'] = True
                        return reward
                    else:
                        return self.calculator.calculate_penalty("weak_response")
                elif action.tool_name == "request_logs":
                    # Duplicate logs request
                    return self.calculator.calculate_penalty("invalid_action")
                else:
                    return self.calculator.calculate_penalty("invalid_action")
            else:
                # Step 2 without logs first
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if "update client to v2.1" in content or "v2.1" in content:
                        # Right answer but poor process
                        reward = self.calculator.calculate_step_reward(
                            routing_score=0.2,
                            response_quality=0.2,
                            tone_quality=0.1,
                            step_number=step_number
                        )
                        return reward
                    else:
                        return self.calculator.calculate_penalty("weak_response")
                else:
                    return self.calculator.calculate_penalty("invalid_action")
        
        else:  # step 3+
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if "update client to v2.1" in content or "v2.1" in content:
                    if self.episode_state['logs_requested']:
                        reward = self.calculator.calculate_step_reward(
                            routing_score=0.4,
                            response_quality=0.25,
                            tone_quality=0.2,
                            step_number=step_number
                        )
                        # Slight penalty for extra steps
                        return max(0.0, reward - 0.05)
                    else:
                        reward = self.calculator.calculate_step_reward(
                            routing_score=0.2,
                            response_quality=0.2,
                            tone_quality=0.1,
                            step_number=step_number
                        )
                        return reward
                else:
                    return self.calculator.calculate_penalty("weak_response")
            elif action.tool_name == "close_ticket":
                if self.episode_state['final_response_given']:
                    # Proper closure after fix
                    reward = self.calculator.calculate_step_reward(
                        routing_score=0.1,
                        response_quality=0.05,
                        tone_quality=0.05,
                        step_number=step_number
                    )
                    return reward
                else:
                    return self.calculator.calculate_penalty("invalid_action")
            else:
                return self.calculator.calculate_penalty("invalid_action")
    
    def _get_easy_task_info(self, action: Action, reward: float) -> str:
        """Get info string for easy task."""
        step = self.episode_state['step_count']
        
        if step == 1:
            if action.tool_name == "send_password_reset":
                return "✓ Sent password reset. Now need verification/closure."
            else:
                return "✗ Should send password reset link first."
        else:
            if action.tool_name == "close_ticket" and self.episode_state['verification_sent']:
                return f"✓ Properly closed ticket. Final reward: {reward:.2f}"
            else:
                return "✗ Should close ticket after password reset."
    
    def _get_medium_task_info(self, action: Action, reward: float) -> str:
        """Get info string for medium task."""
        step = self.episode_state['step_count']
        action_name = action.tool_name
        
        if step == 1:
            if action_name == "request_logs":
                return "✓ Checking policy/system. Now need to respond."
            elif action_name == "reply_to_customer":
                return "✓ Responded (could check policy first for higher score)."
            elif action_name == "issue_refund":
                return "✗ POLICY VIOLATION: Cannot refund after 30 days."
            else:
                return "✗ Invalid action."
        else:
            if action_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(kw in content for kw in ["deny", "policy", "cannot", "30"]):
                    return f"✓ Correctly denied refund with policy. Reward: {reward:.2f}"
                else:
                    return "✗ Response too vague. Use clear policy language."
            elif action_name == "issue_refund":
                return "✗ POLICY VIOLATION: Cannot refund after 30 days."
            else:
                return "✗ Invalid action."
    
    def _get_hard_task_info(self, action: Action, reward: float) -> str:
        """Get info string for hard task."""
        step = self.episode_state['step_count']
        
        if step == 1:
            if action.tool_name == "request_logs":
                return "✓ Requesting logs to investigate. Reward: {:.2f}".format(reward)
            elif action.tool_name == "reply_to_customer":
                return "⚠ Responding without logs (suboptimal investigation)."
            else:
                return "✗ Invalid action."
        elif step == 2:
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if "v2.1" in content:
                    logs_msg = " (after logs)" if self.episode_state['logs_requested'] else " (without logs)"
                    return f"✓ Provided correct fix{logs_msg}. Reward: {reward:.2f}"
                else:
                    return "✗ Incorrect solution."
            else:
                return "✗ Invalid action."
        else:
            if action.tool_name == "reply_to_customer":
                return "⚠ Extra communication (efficiency penalty applied)."
            elif action.tool_name == "close_ticket":
                return f"✓ Ticket closed. Final reward: {reward:.2f}"
            else:
                return "✗ Invalid action."
