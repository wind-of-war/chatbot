from core.agents.orchestrator.graph import AgentGraph
from core.services.cache.redis_cache import RedisCache
from core.services.embedding_service.embedder import Embedder


class Container:
    def __init__(self) -> None:
        self.agent_graph = AgentGraph()
        self.embedder = Embedder()
        self.cache = RedisCache()


container = Container()