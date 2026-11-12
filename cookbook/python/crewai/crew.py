"""CrewAI on UberLLM: two agents (researcher, writer) on one UberLLM model.

The "openai/" prefix plus base_url makes CrewAI use its OpenAI-compatible
client; the rest of the name is the UberLLM model id.

    pip install crewai
    export UBERLLM_API_KEY=ull_...
    python crew.py
"""
import os

from crewai import LLM, Agent, Crew, Process, Task

llm = LLM(
    model="openai/" + os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
    temperature=0.3,
)

researcher = Agent(
    role="Researcher",
    goal="List the facts a reader needs about {topic}",
    backstory="You check facts and keep notes short.",
    llm=llm,
)
writer = Agent(
    role="Writer",
    goal="Turn research notes into a clear paragraph",
    backstory="You write plain, concrete English.",
    llm=llm,
)

research = Task(
    description="Write 4 bullet points of key facts about {topic}.",
    expected_output="4 bullet points",
    agent=researcher,
)
write = Task(
    description="Write one 80-word paragraph for a newsletter from the research notes.",
    expected_output="One paragraph, about 80 words",
    agent=writer,
    context=[research],
)

crew = Crew(agents=[researcher, writer], tasks=[research, write], process=Process.sequential)
result = crew.kickoff(inputs={"topic": "how HTTP caching headers work"})
print(result.raw)
print(result.token_usage)
