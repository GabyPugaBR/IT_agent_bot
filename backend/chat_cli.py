from __future__ import annotations

from datetime import datetime

from main import chat
from memory.store import initialize_memory
from schemas.chat import ChatRequest


def _print_metadata(response) -> None:
    trace = response.reasoning_trace
    print(f"\nAgent: {response.agent_used} | Intent: {response.intent}")

    if trace.routing_confidence is not None:
        print(f"Routing confidence: {trace.routing_confidence}")
    if trace.routing_reasoning:
        print(f"Routing reason: {trace.routing_reasoning}")
    if trace.agent_step:
        print(f"Agent step: {trace.agent_step}")
    if trace.answer_confidence is not None:
        print(f"Answer confidence: {trace.answer_confidence}")
    if trace.retrieval_scores:
        print(f"Retrieval scores: {trace.retrieval_scores}")
    if response.sources:
        print(f"Sources: {', '.join(response.sources)}")


def main() -> None:
    initialize_memory()
    session_id = f"terminal-demo-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    print("Constellations IT Support CLI")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        try:
            response = chat(ChatRequest(message=user_input, session_id=session_id))
        except Exception as exc:
            print(f"\nBot: Something went wrong: {exc}\n")
            continue

        print(f"\nBot: {response.response}")
        _print_metadata(response)
        print()


if __name__ == "__main__":
    main()
