from core.agents.response_agent.agent import ResponseAgent


def test_confidence_low_when_no_docs():
    agent = ResponseAgent()
    score = agent._estimate_confidence("thoi gian ton tru ban dau", "vi", [])
    assert score == 0.0


def test_confidence_higher_with_overlap_and_preferred_source():
    agent = ResponseAgent()
    docs = [
        {
            "source": "WHO_TRS_961_eng.pdf",
            "text": "Initial hold time for sterile products must be justified by validation data.",
        }
    ]
    score = agent._estimate_confidence("initial hold time sterile products", "en", docs)
    assert score >= 0.6
