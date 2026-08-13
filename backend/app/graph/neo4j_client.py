"""
Neo4j graph integration.

Writes entity nodes and relationship edges with provenance. Graceful
degradation: when NEO4J_URI is not configured, sync is a no-op (logged),
never a fake success.
"""

from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("graph")

NODE_LABELS = {
    "PERSON", "PHONE", "EMAIL", "ACCOUNT", "DEVICE", "LOCATION",
    "ORGANIZATION", "VEHICLE", "IP", "URL", "USERNAME",
}

VALID_RELATIONS = {
    "CONTACTED", "MESSAGED", "CALLED", "EMAILED", "USED", "OWNED",
    "VISITED", "LOCATED_AT", "ASSOCIATED_WITH", "CONNECTED_TO", "SUPPORTED_BY",
}

RELATION_TYPE_MAP = {
    "CALLED": "CALLED",
    "MESSAGED": "MESSAGED",
    "EMAILED": "EMAILED",
    "CONTACTED": "CONTACTED",
    "USED": "USED",
    "OWNED": "OWNED",
    "VISITED": "VISITED",
    "LOCATED_AT": "LOCATED_AT",
    "WORKS_AT": "ASSOCIATED_WITH",
    "ASSOCIATED_WITH": "ASSOCIATED_WITH",
    "CONNECTED_TO": "CONNECTED_TO",
}


class Neo4jGraphClient:
    """Thin wrapper around the neo4j driver; None-when-disabled."""

    def __init__(self) -> None:
        self._driver = None
        self._enabled = False
        if settings.NEO4J_URI:
            try:
                from neo4j import GraphDatabase

                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                )
                self._enabled = True
                logger.info("Neo4j client enabled at %s", settings.NEO4J_URI)
            except Exception as exc:
                logger.warning("Neo4j initialization failed (graph features disabled): %s", exc)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def clear_case(self, case_id: str) -> None:
        if not self._enabled:
            return
        with self._driver.session() as session:
            session.run("MATCH (n {case_id: $case_id}) DETACH DELETE n", case_id=case_id)

    def sync(self, case_id: str, entities: List[dict], relationships: List[dict]) -> dict:
        """Build/refresh the case graph from entities and relationships."""
        if not self._enabled:
            return {"enabled": False, "nodes": 0, "edges": 0, "note": "Neo4j not configured"}

        stats = {"nodes": 0, "edges": 0}
        try:
            with self._driver.session() as session:
                session.execute_write(
                    self._tx_clear, case_id
                )
                for ent in entities[:2000]:
                    label = ent.get("entity_type", "OTHER").upper()
                    label = label if label in NODE_LABELS else "OTHER"
                    session.execute_write(
                        self._tx_upsert_entity,
                        case_id, ent.get("entity_id", ""), label,
                        ent.get("normalized_value") or ent.get("value", ""),
                        float(ent.get("confidence", 0.0)),
                    )
                    stats["nodes"] += 1
                for rel in relationships[:5000]:
                    rtype = RELATION_TYPE_MAP.get(rel.get("relation_type", ""), "ASSOCIATED_WITH")
                    session.execute_write(
                        self._tx_add_relation,
                        case_id, rtype,
                        rel.get("source_entity_id", ""), rel.get("target_entity_id", ""),
                        rel.get("supporting_evidence_ids", []),
                        float(rel.get("confidence", 0.0)),
                    )
                    stats["edges"] += 1
        except Exception as exc:
            logger.error("Neo4j sync failed for case %s: %s", case_id, exc)
            return {"enabled": True, "nodes": 0, "edges": 0, "error": str(exc)}
        return {"enabled": True, "nodes": stats["nodes"], "edges": stats["edges"]}

    def _tx_clear(self, tx, case_id: str) -> None:
        tx.run("MATCH (n {case_id: $case_id}) DETACH DELETE n", case_id=case_id)

    def _tx_upsert_entity(self, tx, case_id: str, entity_id: str, label: str, value: str, confidence: float) -> None:
        tx.run(
            (
                f"MERGE (n:{label} {{entity_id: $eid}}) "
                "SET n.case_id = $case_id, n.value = $value, n.confidence = $confidence"
            ),
            eid=entity_id, case_id=case_id, value=value, confidence=confidence,
        )

    def _tx_add_relation(
        self, tx, case_id: str, rtype: str, src_id: str, tgt_id: str, evidence_ids: List[str], confidence: float
    ) -> None:
        tx.run(
            (
                "MATCH (a {entity_id: $src}), (b {entity_id: $tgt}) "
                f"MERGE (a)-[r:{rtype}]->(b) "
                "SET r.case_id = $case_id, r.confidence = $confidence, "
                "r.evidence_ids = $evidence_ids"
            ),
            src=src_id, tgt=tgt_id, case_id=case_id, confidence=confidence,
            evidence_ids=evidence_ids,
        )

    def query_connections(self, case_id: str, value: str, limit: int = 30) -> List[dict]:
        """Find nodes connected to a given entity value (investigator exploration)."""
        if not self._enabled:
            return []
        with self._driver.session() as session:
            result = session.run(
                (
                    "MATCH (n {case_id: $case_id}) WHERE toLower(n.value) CONTAINS toLower($value) "
                    "OPTIONAL MATCH (n)-[r]-(m) "
                    "RETURN n.entity_id AS node, labels(n) AS labels, n.value AS value, "
                    "type(r) AS rel, m.value AS connected_to "
                    "LIMIT $limit"
                ),
                case_id=case_id, value=value, limit=limit,
            )
            return [dict(rec) for rec in result]


_client: Optional[Neo4jGraphClient] = None


def get_graph_client() -> Neo4jGraphClient:
    """Singleton graph client (lazy)."""
    global _client
    if _client is None:
        _client = Neo4jGraphClient()
    return _client