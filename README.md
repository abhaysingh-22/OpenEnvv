# OpenEnv

OpenEnv is an environment framework for training and evaluating agents on support ticket tasks.

## Project Structure

```
OpenEnv/
├── env/                    # Core environment module
├── tasks/                  # Task implementations
├── graders/                # Grading and reward systems
├── agents/                 # Agent implementations
├── data/                   # Task data and resources
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── config/                 # Configuration files
├── app.py                  # Main application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
└── README.md              # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd OpenEnv
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment file:
```bash
cp .env.example .env
```

## Usage

### Running the Application

```bash
python app.py
```

### Running with Scripts

**Baseline evaluation:**
```bash
python scripts/baseline.py
```

**Custom run:**
```bash
python scripts/run_env.py --difficulty easy --agent dummy --episodes 10
```

Options:
- `--difficulty`: Task difficulty (easy, medium, hard)
- `--agent`: Agent type (dummy, hf)
- `--episodes`: Number of episodes to run
- `--max-steps`: Maximum steps per episode

### Running Tests

```bash
pytest tests/
pytest tests/ -v  # Verbose output
pytest tests/ --cov=.  # With coverage
```

## Components

### Environment (`env/`)
The core environment that manages task execution and agent interactions.

### Tasks (`tasks/`)
Different task implementations organized by difficulty level.

### Graders (`graders/`)
Reward calculation and task evaluation systems.

### Agents (`agents/`)
Agent implementations including dummy agents and Hugging Face-based agents.

## Configuration

Configuration is managed through:
- `config/settings.py` - Python configuration
- `openenv.yaml` - YAML configuration file
- `.env` - Environment variables

## Docker

Build the Docker image:
```bash
docker build -t openenv:latest .
```

Run with Docker:
```bash
docker run -it openenv:latest
```

## Testing

The project includes comprehensive tests for all modules. Run tests with:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_environment.py

# Run with coverage report
pytest --cov=. tests/
```

## API Reference

### Environment

```python
from env import Environment
from tasks import EasyTask
from graders import SupportGrader

task = EasyTask('task_1', 'Title', 'Description', {})
grader = SupportGrader()
env = Environment(task, grader, max_steps=100)

state = env.reset()
observation, reward, done, info = env.step(action)
```

### Tasks

```python
from tasks import EasyTask, MediumTask, HardTask

task = EasyTask('task_id', 'title', 'description', initial_data)
state = task.reset()
state = task.step(action)
is_complete = task.is_complete()
```

### Agents

```python
from agents import DummyAgent, HFAgent

dummy = DummyAgent()
action = dummy.act(observation)

hf_agent = HFAgent('agent_1', 'gpt2', {})
action = hf_agent.act(observation)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please open an issue on the GitHub repository.
