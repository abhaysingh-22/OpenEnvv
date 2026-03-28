# 🚨 🚨 SUBMISSION REQUIREMENTS (NON-NEGOTIABLE)

If ANY of these fail → you're disqualified

## 🟢 1. Hugging Face Space MUST WORK

**Requirement:**
- Your project must be deployed on Hugging Face Spaces
- It must:
  - start successfully
  - respond to requests

**Critical check:**

`"Ping URL → returns 200 + responds to reset()"`

**What you must ensure:**
- Your app runs on startup (app.py or server)
- There is an endpoint like:
  - `/reset`

👉 If this fails → instant rejection

## 🟢 2. OpenEnv Spec Compliance

**Must include:**
- ✔ openenv.yaml
- ✔ Typed models (Pydantic)
- ✔ Functions:
  - step()
  - reset()
  - state()

**They will validate:**
- structure
- correctness
- consistency

👉 If spec is broken → reject

## 🟢 3. Dockerfile MUST BUILD

**Requirement:**

They will run:
- `docker build .`
- `docker run ...`

**Your Dockerfile must:**
- install dependencies
- start your app
- not crash

👉 If Docker fails → reject

## 🟢 4. Baseline MUST RUN (VERY IMPORTANT)

**Requirement:**

They will run your script:
- `python inference.py`

**It must:**
- run without error
- complete execution
- output scores

👉 If script crashes → reject

## 🟢 5. You MUST HAVE 3+ TASKS

**Requirement:**
- Easy
- Medium
- Hard

**Each must:**
- have a grader
- produce score between:
  - 0.0 → 1.0

👉 If tasks are missing or broken → reject

## 🟢 6. Environment Variables (MANDATORY)

**You MUST support:**
- API_BASE_URL
- MODEL_NAME
- HF_TOKEN

**Meaning:**
- Your OpenAI calls must use these variables
- NOT hardcoded keys

👉 If missing → reject

## 🟢 7. inference.py (STRICT)

**Requirement:**
- File name MUST be: `inference.py`
- It must be in: root directory

**It must:**
- run all tasks
- call LLM via OpenAI client
- print results

👉 Wrong filename or location → reject

## 🟢 8. Must Use OpenAI Client

**Requirement:**

**You MUST:**
- use OpenAI API client
- NOT random HTTP calls

👉 If not → reject

## 🟢 9. Runtime Constraint

**Requirement:**
- Total runtime < 20 minutes
- Runs on:
  - CPU: 2 cores
  - RAM: 8GB

👉 If too slow → reject

## 🟢 10. Pre-Submission Validator

**They will run:**
- 👉 validation script

**You should ALSO run it before submitting.**

## 💥 Hidden Requirements (IMPORTANT)

These are not written clearly but implied:

### ⚠️ Your system must be STABLE
- No random crashes
- No infinite loops
- No API failures

### ⚠️ Scores must be meaningful
- Not all 1.0
- Not all 0.0
- Proper differentiation
