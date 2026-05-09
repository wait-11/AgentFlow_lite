# Import the solver
from agentflow.agentflow.solver import construct_solver

# Set the LLM engine name
# llm_engine_name = "gpt-4o"
llm_engine_name = "dashscope"  # using DashScope Qwen-2.5-7B-Instruct via Alibaba Cloud

# Construct the solver
solver = construct_solver(
    llm_engine_name=llm_engine_name,
    model_engine=["trainable", "dashscope", "dashscope", "dashscope"]
)

# Solve the user query
output = solver.solve("What is the capital of France?")
print(output["direct_output"])