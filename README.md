# 🌙 Bedtime Story-Teller Agent

A multi-agent system that generates high-quality bedtime stories for children ages 5-10, powered by OpenAI's `gpt-3.5-turbo`.

## ✨ Features

- **Intelligent Categorization** — Automatically classifies story requests (adventure, fantasy, animal, friendship, mystery, educational, fairy-tale) and tailors generation accordingly.
- **Structured Story Arcs** — Plans a 5-beat narrative structure (Setup → Rising Action → Climax → Falling Action → Resolution) before writing.
- **LLM Judge** — Evaluates every story on 5 quality criteria (age-appropriateness, engagement, structure, language, moral) and triggers automatic refinement if the score is below threshold.
- **Safety Filter** — An independent hard safety gate that scans for frightening, violent, or inappropriate content. This is **separate from the Judge** because the Judge uses averages — a story could score 0 on age-appropriateness but 10 on everything else and still pass a 7/10 threshold. The Safety Filter catches exactly these cases with a binary pass/fail.
- **Iterative Refinement** — Up to 3 rounds of judge-guided improvement to ensure quality, plus up to 2 rounds of safety-guided rewrites.
- **Interactive Feedback** — Users can request changes after seeing the story, and the agent will revise accordingly (with automatic safety re-check).
- **Category-Specific Guidelines** — Each story category has tailored writing guidelines (e.g., "sparkle words" for fantasy, "fun clues" for mystery).

## 🏗️ Architecture

See [`system_diagram.md`](system_diagram.md) for the full block diagram.

```
User → Orchestrator → Categorizer → Arc Planner → Storyteller ↔ Judge ↔ Safety Filter → User
                                                        ↑                                 │
                                                        └──────── User Feedback ──────────┘
```

| Component | File | Role |
|---|---|---|
| Orchestrator | `orchestrator.py` | Coordinates the full pipeline with two independent gates |
| Categorizer | `categorizer.py` | Classifies story requests |
| Arc Planner | `story_arc.py` | Creates 5-beat narrative outlines |
| Storyteller | `storyteller.py` | Generates, refines, revises, and safety-fixes stories |
| Judge | `judge.py` | Quality gate — scores stories on 5 criteria (average ≥ 7) |
| Safety Filter | `safety_filter.py` | Safety gate — hard pass/fail scan for harmful content |
| Config | `config.py` | Shared LLM client and settings |
| Prompts | `prompts.py` | All prompt templates |

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/story-teller-agent.git
cd story-teller-agent
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your OpenAI API key

```bash
cp .env.example .env
# Edit .env and paste your API key
```

> ⚠️ **Never commit your `.env` file.** The `.gitignore` is configured to exclude it.

### 5. Run the agent

```bash
python main.py
```

## 💬 Usage

```
════════════════════════════════════════════════════════════
  🌙  Bedtime Story-Teller Agent  🌙
════════════════════════════════════════════════════════════
  Tell me what kind of story you'd like to hear!
  (Type 'quit' or 'exit' to leave)

  📖  Your story request: A story about a brave little dragon who learns to share

  📂  Categorizing your request…
  ✓   Category: fantasy — Themes: bravery, sharing, friendship
  📐  Planning the story arc…
  ✓   Story arc ready
  ✍️  Writing your story…
  ✓   First draft complete
  ⚖️  Evaluating story (round 1)…

  ┌─────────────────────────────────┬───────┐
  │  Criterion                      │ Score │
  ├─────────────────────────────────┼───────┤
  │  Age Appropriateness            │    9  │
  │  Engagement And Pacing          │    8  │
  │  Narrative Structure            │    8  │
  │  Language And Vocabulary        │    9  │
  │  Moral And Lesson               │    8  │
  ├─────────────────────────────────┼───────┤
  │  Overall                        │  8.4  │
  └─────────────────────────────────┴───────┘

  🎉  Story passed quality check!
  🛡️  Running safety filter (check 1)…

  🛡️  Safety Check: ✅ PASSED (severity: none)

  ✅  Story passed safety check!

════════════════════════════════════════════════════════════
  📖  Your Bedtime Story
════════════════════════════════════════════════════════════

  # Ember's Golden Gift
  ...
```

## 📁 Project Structure

```
story-teller-agent/
├── main.py              # Entry point
├── orchestrator.py      # Pipeline coordinator (two independent gates)
├── categorizer.py       # Story request classifier
├── story_arc.py         # 5-beat narrative planner
├── storyteller.py       # Story generator, refiner & safety rewriter
├── judge.py             # Quality gate (average score ≥ 7)
├── safety_filter.py     # Safety gate (hard pass/fail)
├── config.py            # Shared LLM client & settings
├── prompts.py           # All prompt templates
├── system_diagram.md    # Architecture diagram
├── requirements.txt     # Python dependencies
├── .env.example         # API key template
├── .gitignore           # Git exclusions
└── README.md            # This file
```

## 🔧 Configuration

Key settings in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `MODEL_NAME` | `gpt-3.5-turbo` | OpenAI model (do not change) |
| `CREATIVE_TEMPERATURE` | `0.8` | Temperature for story generation |
| `PRECISE_TEMPERATURE` | `0.1` | Temperature for judge/categorizer/safety |
| `JUDGE_PASS_THRESHOLD` | `7` | Minimum overall score to accept (quality gate) |
| `MAX_REFINEMENT_ITERATIONS` | `3` | Max judge→refine loops |
| `MAX_SAFETY_REWRITES` | `2` | Max safety→rewrite loops (in `orchestrator.py`) |

## 📝 Prompting Strategies

1. **Role-Based System Design** — Each agent has a clearly defined role with specific expertise (categorizer, planner, storyteller, critic, safety scanner).
2. **Structured Output** — Categorizer, Arc Planner, Judge, and Safety Filter return JSON for reliable parsing.
3. **Category-Tailored Generation** — 8 different sets of storytelling guidelines ensure the style matches the genre.
4. **Iterative Refinement** — The judge provides actionable, criterion-specific feedback that the storyteller uses to improve.
5. **Separation of Concerns** — Creative generation (temp 0.8) is kept separate from analytical evaluation (temp 0.1).
6. **Defence in Depth** — Two independent gates (quality + safety) ensure that average-score vulnerabilities cannot bypass child safety checks. The Safety Filter uses binary pass/fail, not averages.

## 🧪 Testing

All tests mock the OpenAI API and run **offline — no API key required**.

```bash
python -m pytest tests/ -v
```

**69 tests** across 7 test files:

| Test File | Tests | What It Covers |
|---|---|---|
| `test_config.py` | 7 | JSON parsing: clean input, JSON-in-prose extraction, markdown fences, garbage input, nested structures |
| `test_categorizer.py` | 4 | Category parsing, fallback defaults, missing key filling, prompt construction |
| `test_story_arc.py` | 4 | Arc parsing, defaults, partial responses, category metadata in prompt |
| `test_judge.py` | 9 | Evaluation parsing, score computation, threshold pass/fail, **average-score vulnerability proof** |
| `test_safety_filter.py` | 12 | Safe/unsafe parsing, string boolean normalisation, `is_safe` helper, fallback defaults |
| `test_storyteller.py` | 12 | All 4 storyteller functions — prompt content verification and temperature checks |
| `test_prompts.py` | 21 | All 8 prompt templates format correctly, category guidelines for all 8 categories, prompt content validation |

> 💡 **Notable test**: `test_average_vulnerability_example` in `test_judge.py` explicitly proves that a story scoring 0 on age-appropriateness + 10 on everything else = 8.0 average → **passes the Judge** — demonstrating exactly why the Safety Filter exists as an independent gate.

---