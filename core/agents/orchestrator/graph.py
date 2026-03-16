from core.agents.compliance_agent.agent import ComplianceAgent
from core.agents.language_agent.agent import LanguageAgent
from core.agents.query_agent.agent import QueryAgent
from core.agents.response_agent.agent import ResponseAgent
from core.agents.retrieval_agent.agent import RetrievalAgent


class AgentGraph:
    def __init__(self) -> None:
        self.language_agent = LanguageAgent()
        self.query_agent = QueryAgent()
        self.retrieval_agent = RetrievalAgent()
        self.compliance_agent = ComplianceAgent()
        self.response_agent = ResponseAgent()

    def run(self, question: str) -> dict:
        state = {"question": question}
        state = self.language_agent.run(state)
        state = self.query_agent.run(state)
        state = self.retrieval_agent.run(state)
        state = self.compliance_agent.run(state)
        state = self.response_agent.run(state)
        return state
