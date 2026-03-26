"""Hugging Face based agent."""
from typing import Any, Dict, Optional
from .base_agent import BaseAgent


class HFAgent(BaseAgent):
    """Agent powered by Hugging Face models."""
    
    def __init__(self, agent_id: str, model_name: str, config: Dict[str, Any]):
        """
        Initialize the Hugging Face agent.
        
        Args:
            agent_id: Unique identifier for the agent
            model_name: Name of the HF model to use
            config: Configuration dictionary
        """
        super().__init__(agent_id, f"HFAgent_{model_name}")
        self.model_name = model_name
        self.config = config
        self.model = None
        self.tokenizer = None
    
    def load_model(self) -> None:
        """Load the Hugging Face model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        except ImportError:
            raise ImportError("transformers library is required for HFAgent")
    
    def act(self, observation: Dict[str, Any]) -> str:
        """
        Generate an action using the HF model.
        
        Args:
            observation: Current environment observation
            
        Returns:
            Action from the model
        """
        if self.model is None:
            self.load_model()
        
        # Convert observation to prompt
        prompt = self._format_prompt(observation)
        
        # Generate action using model
        action = self._generate_action(prompt)
        
        self.action_history.append(action)
        return action
    
    def _format_prompt(self, observation: Dict[str, Any]) -> str:
        """Format observation into a prompt."""
        return str(observation)
    
    def _generate_action(self, prompt: str) -> str:
        """Generate action from prompt."""
        # Placeholder for actual generation logic
        return "generated_action"
