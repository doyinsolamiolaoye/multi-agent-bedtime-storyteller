"""
Bedtime Story-Teller Agent
──────────────────────────
A multi-agent system that generates high-quality bedtime stories for
children ages 5-10.  Uses an Orchestrator to coordinate a Categorizer,
Story Arc Planner, Storyteller, and LLM Judge.

Run:
    python main.py
"""

import os
import openai

"""
FUTURE FEATURES & ENHANCEMENTS :
1. Implement prompt-level optimization using the Judge's scores as a fitness
   function.  The current system does output-level refinement (the Judge
   evaluates a story and the Storyteller rewrites it), but the prompt
   templates themselves are static.  Using techniques like DSPy or automatic
   prompt engineering (APE), I would systematically evolve the prompt
   templates over many runs so that even first-draft stories improve over
   time — the system would get smarter, not just individual stories.
2. Add a Text-to-Speech (TTS) layer using OpenAI's TTS API so the story
   could be read aloud — a huge UX win for actual bedtime use.
3. Build a small Streamlit or Gradio web UI with illustrations generated
   via DALL-E for each story beat, turning the output into a mini
   picture-book experience.
4. Implement a "story memory" system that tracks previously told stories
   and the child's preferences (favourite characters, themes) so the
   agent can offer sequels or personalised recommendations.
5. Add a multi-language support layer so stories can be generated in
   different languages based on the user's preference, widening
   accessibility for non-English-speaking families.
"""


def call_model(prompt: str, max_tokens=3000, temperature=0.1) -> str:
    """Legacy helper kept for reference — the live pipeline uses config.call_model."""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content  # type: ignore


example_requests = (
    "A story about a girl named Alice and her best friend Bob, "
    "who happens to be a cat."
)


def main():
    from orchestrator import run  # local import to avoid circular deps
    run()


if __name__ == "__main__":
    main()