"""
Test AgentFlow on real benchmark questions - paper config (all DashScope qwen2.5-7b-instruct)
"""
import time, re
from agentflow.agentflow.solver import construct_solver

def make_solver():
    return construct_solver(
        llm_engine_name="dashscope",
        enabled_tools=["Base_Generator_Tool", "Python_Coder_Tool", "SerpBase_Search_Tool", "Wikipedia_Search_Tool"],
        model_engine=["trainable", "trainable", "trainable", "trainable"],
        tool_engine=["Default", "Default", "Default", "Default"],
        output_types="final,direct",
        max_steps=5,
        max_time=120,
        verbose=True,
        temperature=0.0
    )

def clean_question(q):
    """Remove benchmark format instructions like <answer> tags"""
    q = re.sub(r'When ready, output.*?</answer>\s*tags?\.?\s*$', '', q, flags=re.IGNORECASE)
    return q.strip()

questions = [
    # Multi-hop comparison - needs search + reasoning
    ("HotpotQA", "Who released the song \"With or Without You\" first, Jai McDowall or U2?"),
    # Multi-hop factoid - needs search for director then director's birthday
    ("2Wiki", "When is the director of film Les Tuche 2's birthday?"),
]

for dataset, question in questions:
    question = clean_question(question)
    print("\n" + "=" * 70)
    print(f"DATASET: {dataset}")
    print(f"QUESTION: {question}")
    print("=" * 70)

    solver = make_solver()
    start = time.time()
    result = solver.solve(question)
    elapsed = time.time() - start

    print(f"\n--- ANSWER ---")
    print(result.get("direct_output", "N/A"))
    print(f"\n[TOTAL TIME: {elapsed:.1f}s, STEPS: {result.get('step_count', '?')}]")
