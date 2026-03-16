from core.agents.orchestrator.graph import AgentGraph


def test_agent_graph_returns_answer_key():
    graph = AgentGraph()
    state = graph.run("GDP quy dinh nhiet do kho?")
    assert "answer" in state
    assert "citations" in state
    assert state.get("language") in {"vi", "en"}
