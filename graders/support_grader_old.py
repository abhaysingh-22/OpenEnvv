"""Support grader for customer support tasks with advanced reward shaping.

================================================================================
SCORING SYSTEM DOCUMENTATION
================================================================================

REWARD COMPONENTS:
All rewards are built from these components:
- Routing Score:          -0.4 to +0.4 (decision quality)
- Response Quality:       0.0 to +0.3  (clarity and completeness)
- Tone Quality:          0.0 to +0.2  (professionalism and empathy)
- Efficiency Penalty:    -0.05 per step (encourages quick resolution)

CONSISTENT PENALTIES (all tasks):
- invalid_action:        -0.15  (wrong tool used)
- policy_violation:      -0.3   (violates company policy)
- forbidden_phrase:      -0.2   (uses forbidden language)
- wrong_routing:         -0.4   (completely wrong direction)
- bad_tone:             -0.15  (unprofessional communication)
- weak_response:        -0.1   (insufficient or unclear)
- failure_condition:    -0.5   (task cannot be completed)

HARD TASK SEQUENCE PENALTIES:
- Step 1: Wrong action   -0.5   (must request logs first)
- Step 2: Wrong action   -0.4   (must diagnose after logs)
- Step 3+: Wrong action  -0.3   (must respond properly)

EXPECTED SCORE RANGES (after step rewards + penalties + efficiency):
- Perfect agent (optimal sequence):  0.6-0.9+
- Imperfect agent (some errors):     0.3-0.6
- Random agent (poor choices):       0.0-0.2
- Failure condition triggered:       Max 0.0 (episode reset)

TASK-SPECIFIC RULES:
1. EASY TASK (Password Reset):
   - Failure: Closing without sending reset → -0.5
   - Step 1: Send password reset (routing=0.35, response=0.25, tone=0.15)
   - Step 2: Close ticket (routing=0.25, response=0.15, tone=0.1)

2. MEDIUM TASK (Refund Request):
   - Failure: Issuing refund after 30 days → -0.5
   - Step 1: Check policy (routing=0.25) or respond (routing=0.15)
   - Step 2+: Deny with policy (routing=0.35, response=0.25, tone=0.2 + bonus)

3. HARD TASK (Technical Troubleshooting):
   - Phase 1: Request logs only (routing=0.25, response=0.15, tone=0.15)
   - Phase 2: Diagnose (routing=0.35, response=0.25, tone=0.15)
   - Phase 3: Respond/Close (routing=0.3+, response=0.2, tone=0.15)
   - Sequence violations: -0.5, -0.4, -0.3 respectively

================================================================================
"""
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
    - Multi-step task validation
    """
    
    def __init__(self, answer_key: Dict[str, Any] = None, policy: Dict[str, Any] = None):
        """Initialize the support grader."""
        super().__init__()
        self.answer_key = answer_key or {}
        self.policy = policy or {}
        self.calculator = RewardCalculator(efficiency_penalty=0.02)  # Reduced from 0.05 to allow higher scores
        self.episode_state: Dict[str, Any] = {}
        self.reset_episode()
    
    def reset_episode(self) -> None:
        """Reset episode state for a new task."""
        self.episode_state = {
            'task_id': None,
            'step_count': 0,
            'action_history': [],
            'logs_requested': False,
            'diagnosed': False,           # Track diagnosis phase
            'policy_checked': False,
            'verification_sent': False,
            'final_response_given': False,
            'cumulative_reward': 0.0,
            'failure_condition': None,    # Track if task failed
            'wrong_response_count': 0,    # Track wrong responses in hard task
            'minimum_threshold_breached': False  # Track if minimum score threshold broken
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
        
        # Check minimum threshold
        if self._check_minimum_threshold(step_reward, state.task_id):
            self.episode_state['minimum_threshold_breached'] = True
        
        self.scores.append(step_reward)
        
        return Reward(
            value=step_reward,
            is_complete=is_complete,
            info=info.strip()
        )
    
    def _check_minimum_threshold(self, reward: float, task_id: str) -> bool:
        """
        Check if reward meets minimum threshold for task completion.
        
        Minimum thresholds per task:
        - Easy: 0.5 (simple task, should score well)
        - Medium: 0.4 (policy checking required)
        - Hard: 0.3 (complex sequence required)
        
        Args:
            reward: Current step reward
            task_id: Task identifier
            
        Returns:
            True if threshold is breached (reward too low)
        """
        min_thresholds = {
            'easy_ticket_1': 0.5,
            'medium_ticket_1': 0.4,
            'hard_ticket_1': 0.3
        }
        
        threshold = min_thresholds.get(task_id, 0.3)
        return reward < threshold
    
    def _grade_easy_task(self, action: Action, step_number: int) -> float:
        """
        Grade easy task (Password Reset) with component-based rewards.
        
        FAILURE CONDITION: Closing ticket without password reset → immediate -0.5 penalty
        
        Required steps:
        Step 1: Send password reset verification
        Step 2: Verify and close ticket
        """
        
        # ===================================
        # FAILURE CONDITION CHECK
        # ===================================
        if action.tool_name == "close_ticket" and not self.episode_state['verification_sent']:
            # FAILURE: Closing without sending reset
            self.episode_state['failure_condition'] = "incomplete_task"
            return self.calculator.apply_failure_condition("closure_without_reset")
        
        # ===================================
        # STEP 1: Send password reset
        # ===================================
        if step_number == 1:
            if action.tool_name == "send_password_reset" and action.tool_args.get("email") == "john@example.com":
                # Correct routing and action
                components = self.calculator.calculate_component_rewards(
                    routing_score=0.4,       # Excellent routing (was 0.35)
                    response_quality=0.3,    # Quality response (was 0.25)
                    tone_quality=0.2,        # Professional tone (was 0.15)
                    step_number=step_number
                )
                self.episode_state['verification_sent'] = True
                return components['total']
            
            elif action.tool_name == "reply_to_customer":
                # Wrong action on step 1 (explaining instead of acting)
                return self.calculator.calculate_penalty("wrong_routing")
            else:
                return self.calculator.calculate_penalty("invalid_action")
        
        # ===================================
        # STEP 2+: Close ticket after verification
        # ===================================
        else:
            if action.tool_name == "close_ticket" and self.episode_state['verification_sent']:
                # Proper closure after password reset
                components = self.calculator.calculate_component_rewards(
                    routing_score=0.3,       # Good routing (was 0.25)
                    response_quality=0.2,    # Adequate response (was 0.15)
                    tone_quality=0.15,       # Adequate tone (was 0.1)
                    step_number=step_number
                )
                return components['total']
            
            elif action.tool_name == "send_password_reset":
                # Duplicate action
                return 0.0
            else:
                return self.calculator.calculate_penalty("invalid_action")
    
    def _grade_medium_task(self, action: Action, step_number: int) -> float:
        """
        Grade medium task (Refund Request) with component-based rewards.
        
        FAILURE CONDITION: Issuing refund after 30 days → immediate -0.5 penalty
        
        Required steps:
        Step 1: Check policy/system or respond (optional)
        Step 2+: Deny refund with clear policy explanation
        
        Component rewards separated:
        - Routing: Policy checking vs direct response
        - Response Quality: Clarity and firmness of denial
        - Tone Quality: Professional and empathetic delivery
        """
        
        # ===================================
        # FAILURE CONDITION CHECK
        # ===================================
        if action.tool_name == "issue_refund":
            # FAILURE: Cannot issue refund after 30 days
            # Task ends immediately with penalty
            self.episode_state['failure_condition'] = "policy_violation"
            return self.calculator.apply_failure_condition("refund_after_30_days")
        
        # ===================================
        # STEP 1: Policy checking or response
        # ===================================
        if step_number == 1:
            if action.tool_name == "request_logs":
                # Checking policy/system data (good practice)
                self.episode_state['policy_checked'] = True
                components = self.calculator.calculate_component_rewards(
                    routing_score=0.25,      # Good: investigating policy
                    response_quality=0.15,   # Informational step
                    tone_quality=0.1,        # Neutral tone
                    step_number=step_number
                )
                return components['total']
            
            elif action.tool_name == "reply_to_customer":
                # Direct response without checking (suboptimal but acceptable)
                content = str(action.tool_args.get("content", "")).lower()
                if any(keyword in content for keyword in ["deny", "policy", "cannot", "30"]):
                    # Decent response even without explicit policy check
                    components = self.calculator.calculate_component_rewards(
                        routing_score=0.15,      # Less optimal routing
                        response_quality=0.2,    # Decent response
                        tone_quality=0.1,        # Professional tone
                        step_number=step_number
                    )
                    self.episode_state['policy_checked'] = True
                    return components['total']
                else:
                    return self.calculator.calculate_penalty("weak_response")
            else:
                return self.calculator.calculate_penalty("invalid_action")
        
        # ===================================
        # STEP 2+: Final denial with policy
        # ===================================
        else:
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(keyword in content for keyword in ["deny", "policy", "cannot", "30"]):
                    # Proper denial with policy explanation
                    components = self.calculator.calculate_component_rewards(
                        routing_score=0.35,      # Excellent: correct decision
                        response_quality=0.25,   # Clear and firm
                        tone_quality=0.2,        # Professional and empathetic
                        step_number=step_number
                    )
                    
                    # Completion bonus if done efficiently
                    bonus = self.calculator.calculate_completion_bonus(
                        steps_taken=step_number,
                        min_steps=2
                    )
                    return components['total'] + bonus
                else:
                    return self.calculator.calculate_penalty("weak_response")
            
            elif action.tool_name == "close_ticket":
                # Closing without proper response
                return self.calculator.calculate_penalty("weak_response")
            
            else:
                return self.calculator.calculate_penalty("invalid_action")
    
    def _grade_hard_task(self, action: Action, state: State, step_number: int) -> float:
        """
        Grade hard task (Technical Troubleshooting) with STRICT sequence dependency.
        
        REQUIRED SEQUENCE:
        1. logs_requested: Must request logs FIRST
        2. diagnosed: Must analyze/explain after logs
        3. responded: Must provide final response
        
        State-based penalties for violations:
        - Step 1: If not request_logs → -0.5 penalty
        - Step 2: If not reply_to_customer (analysis) → -0.4 penalty
        - Step 3+: If not proper closure → -0.3 penalty
        """
        # Track state transitions
        logs_requested = self.episode_state.get('logs_requested', False)
        diagnosed = self.episode_state.get('diagnosed', False)
        responded = self.episode_state.get('final_response_given', False)
        
        # ===================================
        # PHASE 1: Must request logs first
        # ===================================
        if not logs_requested:
            if action.tool_name != "request_logs":
                # STRICT PENALTY: Wrong action at critical sequence point
                return self.calculator.apply_sequence_penalty(
                    is_sequence_violation=True,
                    step_number=step_number
                )
            else:
                # Correct action: Request logs
                self.episode_state['logs_requested'] = True
                reward = self.calculator.calculate_step_reward(
                    routing_score=0.3,        # Good investigation start (was 0.25)
                    response_quality=0.2,     # Proactive (was 0.15)
                    tone_quality=0.2,         # Professional (was 0.15)
                    step_number=step_number
                )
                return reward
        
        # ===================================
        # PHASE 2: Analyze and diagnose (after logs)
        # ===================================
        elif not diagnosed:
            if action.tool_name != "reply_to_customer":
                # STRICT PENALTY: Wrong action at sequence point
                return self.calculator.apply_sequence_penalty(
                    is_sequence_violation=True,
                    step_number=step_number
                )
            else:
                # Check if response makes sense (diagnosis based on logs)
                content = str(action.tool_args.get("content", "")).lower()
                
                # Verify diagnosis is reasonable given the logs (ERR-99 → v2.1)
                if "update client to v2.1" in content or "v2.1" in content:
                    self.episode_state['diagnosed'] = True
                    reward = self.calculator.calculate_step_reward(
                        routing_score=0.4,       # Excellent diagnosis (was 0.35)
                        response_quality=0.3,    # Clear explanation (was 0.25)
                        tone_quality=0.2,        # Helpful tone (was 0.15)
                        step_number=step_number
                    )
                    return reward
                else:
                    # Wrong diagnosis even after logs
                    return self.calculator.calculate_penalty("weak_response")
        
        # ===================================
        # PHASE 3: Final response/closure (after diagnosis)
        # ===================================
        else:
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                
                # Verify consistent solution
                if "update client to v2.1" in content or "v2.1" in content:
                    reward = self.calculator.calculate_step_reward(
                        routing_score=0.35,      # Good completion (was 0.3)
                        response_quality=0.25,   # Final response (was 0.2)
                        tone_quality=0.2,        # Helpful (was 0.15)
                        step_number=step_number
                    )
                    # Slight penalty for excessive communication
                    if step_number > 3:
                        reward = max(0.0, reward - 0.05)
                    self.episode_state['final_response_given'] = True
                    return reward
                else:
                    # Wrong solution
                    self.episode_state['wrong_response_count'] += 1
                    
                    # FAILURE CONDITION: Wrong solution twice means task cannot be completed
                    if self.episode_state['wrong_response_count'] >= 2:
                        self.episode_state['failure_condition'] = "wrong_solution_repeated"
                        return self.calculator.apply_failure_condition("wrong_solution_twice")
                    
                    return self.calculator.calculate_penalty("weak_response")
            
            elif action.tool_name == "close_ticket":
                # Proper closure after all phases
                if self.episode_state['final_response_given']:
                    reward = self.calculator.calculate_step_reward(
                        routing_score=0.2,       # Completion (was 0.15)
                        response_quality=0.15,   # Final action (was 0.1)
                        tone_quality=0.15,       # Professional (was 0.1)
                        step_number=step_number
                    )
                    return reward
                else:
                    return self.calculator.calculate_penalty("invalid_action")
            
            else:
                return self.calculator.calculate_penalty("invalid_action")
    
    def _get_easy_task_info(self, action: Action, reward: float) -> str:
        """Get detailed info string for easy task with component breakdown."""
        step = self.episode_state['step_count']
        
        if step == 1:
            if action.tool_name == "send_password_reset":
                return f"✓ Step 1: Sent password reset. Reward: {reward:.2f}\n  Components: routing=0.35, response=0.25, tone=0.15"
            elif action.tool_name == "close_ticket":
                return "✗ FAILURE: Cannot close without sending reset first! Penalty: -0.5"
            else:
                return "✗ Should send password reset link first."
        else:
            if action.tool_name == "close_ticket" and self.episode_state['verification_sent']:
                return f"✓ Step {step}: Properly closed ticket. Reward: {reward:.2f}\n  Components: routing=0.25, response=0.15, tone=0.1"
            elif action.tool_name == "close_ticket":
                return "✗ FAILURE: Cannot close without password reset! Penalty: -0.5"
            else:
                return "✗ Should close ticket after password reset."
    
    def _get_medium_task_info(self, action: Action, reward: float) -> str:
        """Get detailed info string for medium task with component breakdown."""
        step = self.episode_state['step_count']
        action_name = action.tool_name
        
        if action_name == "issue_refund":
            return "✗ FAILURE: Cannot refund after 30 days! Policy violation. Penalty: -0.5"
        
        if step == 1:
            if action_name == "request_logs":
                return f"✓ Step 1: Checking policy/system. Reward: {reward:.2f}\n  Components: routing=0.25, response=0.15, tone=0.1"
            elif action_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(kw in content for kw in ["deny", "policy", "cannot", "30"]):
                    return f"✓ Step 1: Direct response (skipped policy check). Reward: {reward:.2f}\n  Components: routing=0.15, response=0.2, tone=0.1"
                else:
                    return "✗ Weak response: Need to deny refund with policy explanation."
            else:
                return "✗ Invalid action."
        else:
            if action_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if any(kw in content for kw in ["deny", "policy", "cannot", "30"]):
                    return f"✓ Step {step}: Properly denied refund. Reward: {reward:.2f}\n  Components: routing=0.35, response=0.25, tone=0.2 (+bonus)"
                else:
                    return "✗ Weak response: Use clear policy language."
            elif action_name == "close_ticket":
                return "✗ Cannot close without proper denial response."
            else:
                return "✗ Invalid action."
    
    def _get_hard_task_info(self, action: Action, reward: float) -> str:
        """Get detailed info string for hard task with sequence feedback."""
        step = self.episode_state['step_count']
        logs_requested = self.episode_state['logs_requested']
        diagnosed = self.episode_state['diagnosed']
        
        if step == 1:
            if action.tool_name == "request_logs":
                return f"✓ PHASE 1: Requesting logs (investigation). Reward: {reward:.2f}"
            elif action.tool_name == "reply_to_customer":
                return "✗ SEQUENCE VIOLATION: Must request logs first! Penalty: -0.5"
            else:
                return "✗ Invalid action. Must request logs first."
        
        elif step == 2:
            if logs_requested:
                if action.tool_name == "reply_to_customer":
                    content = str(action.tool_args.get("content", "")).lower()
                    if "v2.1" in content:
                        return f"✓ PHASE 2: Diagnosis complete with logs. Reward: {reward:.2f}"
                    else:
                        return "✗ Incorrect diagnosis. Expected v2.1 solution."
                else:
                    return "✗ SEQUENCE VIOLATION: Must diagnose after logs! Penalty: -0.4"
            else:
                if action.tool_name == "reply_to_customer":
                    return "⚠ Response without logs (poor process). Suboptimal reward."
                else:
                    return "✗ Invalid action. Must respond with solution."
        
        else:  # step 3+
            if action.tool_name == "reply_to_customer":
                return f"⚠ Extra communication (efficiency penalty). Reward: {reward:.2f}"
            elif action.tool_name == "close_ticket":
                return f"✓ PHASE 3: Ticket closed properly. Reward: {reward:.2f}"
            else:
                return "✗ Invalid action."
