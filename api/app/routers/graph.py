from fastapi import APIRouter, Query

from ..database import get_pool
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.get("/structure")
async def structure_graph():
    pool = await get_pool()
    nodes = await pool.fetch(
        "SELECT api_name, display_name, type, config, maturity FROM ontology_types WHERE type = 'OBJECT'"
    )
    # Single query for all counts
    counts = {}
    count_rows = await pool.fetch(
        "SELECT object_type, COUNT(*) FROM ontology_objects GROUP BY object_type"
    )
    for cr in count_rows:
        counts[cr["object_type"]] = cr["count"]
    node_list = []
    for n in nodes:
        config = n["config"]
        node_list.append({
            "id": n["api_name"],
            "label": n["display_name"],
            "apiName": n["api_name"],
            "type": n["type"],
            "color": config.get("color", "#1890ff") if isinstance(config, dict) else "#1890ff",
            "propertyCount": counts.get(n["api_name"], 0),
        })
    edges = await pool.fetch(
        "SELECT api_name, display_name, config FROM ontology_types WHERE type = 'LINK'"
    )
    edge_list = []
    for e in edges:
        node_set = set(n["id"] for n in node_list)
        config = e["config"] if isinstance(e["config"], dict) else {}
        src = config.get("sourceType")
        tgt = config.get("targetType")
        if src is None and tgt is None:
            # Skip LINK types with no type constraints — don't generate self-loops
            continue
        elif src is not None and tgt is not None:
            if src in node_set and tgt in node_set:
                edge_list.append({
                    "id": f"{src}-{e['api_name']}-{tgt}",
                    "source": src,
                    "target": tgt,
                    "label": e["display_name"],
                    "relationship": e["api_name"],
                })
        elif src is not None:
            if src in node_set:
                for nid in node_set:
                    edge_list.append({
                        "id": f"{src}-{e['api_name']}-{nid}",
                        "source": src,
                        "target": nid,
                        "label": e["display_name"],
                        "relationship": e["api_name"],
                    })
        elif tgt is not None:
            if tgt in node_set:
                for nid in node_set:
                    edge_list.append({
                        "id": f"{nid}-{e['api_name']}-{tgt}",
                        "source": nid,
                        "target": tgt,
                        "label": e["display_name"],
                        "relationship": e["api_name"],
                    })
    return {"nodes": node_list, "edges": edge_list}


@router.get("/entities")
async def entity_graph(dataset: str = "default", depth: int = 2):
    pool = await get_pool()
    objects = await pool.fetch(
        "SELECT id, object_type, display_name, properties FROM ontology_objects WHERE dataset_id = $1",
        dataset,
    )
    node_map = {}
    for o in objects:
        props = o["properties"]
        if isinstance(props, str):
            import json; props = json.loads(props)
        if props is None:
            props = {}
        node_map[str(o["id"])] = {
            "id": str(o["id"]),
            "label": o["display_name"] or props.get("name", str(o["id"])[:8]),
            "type": o["object_type"],
        }
    links = await pool.fetch(
        "SELECT id, link_type, source_id, target_id FROM ontology_links WHERE dataset_id = $1",
        dataset,
    )
    edge_list = []
    for l in links:
        edge_list.append({
            "id": str(l["id"]),
            "source": str(l["source_id"]),
            "target": str(l["target_id"]),
            "label": l["link_type"],
            "relationship": l["link_type"],
        })
    return {"nodes": list(node_map.values()), "edges": edge_list}


# ── Advanced graph operations ──────────────────────────────────


@router.get("/path")
async def find_path(
    source: str = Query(..., description="Source node UUID"),
    target: str = Query(..., description="Target node UUID"),
    dataset: str = Query("default"),
    max_depth: int = Query(5, ge=1, le=10),
):
    """BFS shortest path between two nodes using recursive CTE."""
    pool = await get_pool()
    rows = await pool.fetch(
        """WITH RECURSIVE bfs AS (
            SELECT source_id, target_id, link_type,
                   ARRAY[source_id]::uuid[] AS path,
                   ARRAY[link_type] AS edge_labels,
                   1 AS depth
            FROM ontology_links
            WHERE dataset_id = $1 AND source_id = $2::uuid
            UNION ALL
            SELECT l.source_id, l.target_id, l.link_type,
                   bfs.path || l.source_id,
                   bfs.edge_labels || l.link_type,
                   bfs.depth + 1
            FROM ontology_links l
            JOIN bfs ON l.source_id = bfs.target_id
            WHERE l.dataset_id = $1
              AND bfs.depth < $3
              AND NOT (l.source_id = ANY(bfs.path))
        )
        SELECT * FROM bfs WHERE target_id = $4::uuid
        ORDER BY depth LIMIT 1""",
        dataset, source, max_depth, target,
    )
    if not rows:
        return {"found": False, "path": [], "length": 0}

    row = rows[0]
    node_ids = [str(n) for n in row["path"]] + [str(row["target_id"])]
    objects = await pool.fetch(
        "SELECT id, object_type, display_name, properties FROM ontology_objects WHERE id = ANY($1::uuid[])",
        [row["path"][i] for i in range(len(row["path"]))] + [row["target_id"]],
    )
    node_map = {}
    for o in objects:
        props = o["properties"]
        if isinstance(props, str):
            import json; props = json.loads(props)
        node_map[str(o["id"])] = {
            "id": str(o["id"]),
            "label": o["display_name"] or (props or {}).get("name", str(o["id"])[:8]),
            "type": o["object_type"],
        }

    return {
        "found": True,
        "path": [node_map.get(nid, {"id": nid}) for nid in node_ids],
        "edges": [str(e) for e in row["edge_labels"]],
        "length": row["depth"],
    }


@router.get("/neighbors")
async def get_neighbors(
    node: str = Query(..., description="Node UUID"),
    dataset: str = Query("default"),
    direction: str = Query("both", pattern="^(in|out|both)$"),
):
    """Get direct neighbors of a node."""
    pool = await get_pool()
    neighbor_ids = set()

    if direction in ("out", "both"):
        rows = await pool.fetch(
            "SELECT target_id FROM ontology_links WHERE dataset_id = $1 AND source_id = $2::uuid",
            dataset, node,
        )
        for r in rows:
            neighbor_ids.add(str(r["target_id"]))

    if direction in ("in", "both"):
        rows = await pool.fetch(
            "SELECT source_id FROM ontology_links WHERE dataset_id = $1 AND target_id = $2::uuid",
            dataset, node,
        )
        for r in rows:
            neighbor_ids.add(str(r["source_id"]))

    if not neighbor_ids:
        return {"node": node, "neighbors": [], "count": 0}

    objects = await pool.fetch(
        "SELECT id, object_type, display_name, properties FROM ontology_objects WHERE id = ANY($1::uuid[])",
        list(neighbor_ids),
    )
    results = []
    for o in objects:
        props = o["properties"]
        if isinstance(props, str):
            import json; props = json.loads(props)
        results.append({
            "id": str(o["id"]),
            "label": o["display_name"] or (props or {}).get("name", str(o["id"])[:8]),
            "type": o["object_type"],
        })

    return {"node": node, "neighbors": results, "count": len(results)}


@router.get("/traverse")
async def traverse_graph(
    start: str = Query(..., description="Starting node UUID"),
    dataset: str = Query("default"),
    max_depth: int = Query(3, ge=1, le=5),
    strategy: str = Query("bfs", pattern="^(bfs|dfs)$"),
):
    """Traverse the graph from a starting node using BFS or DFS via recursive CTE."""
    pool = await get_pool()

    # BFS traversal (iterative expansion by depth)
    rows = await pool.fetch(
        """WITH RECURSIVE traversal AS (
            SELECT source_id, target_id, link_type, 1 AS depth,
                   ARRAY[source_id, target_id]::uuid[] AS visited
            FROM ontology_links
            WHERE dataset_id = $1 AND source_id = $2::uuid
            UNION ALL
            SELECT l.source_id, l.target_id, l.link_type, t.depth + 1,
                   t.visited || l.target_id
            FROM ontology_links l
            JOIN traversal t ON l.source_id = t.target_id
            WHERE l.dataset_id = $1
              AND t.depth < $3
              AND NOT (l.target_id = ANY(t.visited))
        )
        SELECT DISTINCT ON (source_id, target_id) *
        FROM traversal ORDER BY source_id, target_id, depth""",
        dataset, start, max_depth,
    )

    node_ids = set()
    node_ids.add(start)
    edges = []
    for r in rows:
        node_ids.add(str(r["source_id"]))
        node_ids.add(str(r["target_id"]))
        edges.append({
            "source": str(r["source_id"]),
            "target": str(r["target_id"]),
            "label": r["link_type"],
            "depth": r["depth"],
        })

    if not node_ids:
        return {"nodes": [], "edges": [], "count": 0}

    objects = await pool.fetch(
        "SELECT id, object_type, display_name, properties FROM ontology_objects WHERE id = ANY($1::uuid[])",
        list(node_ids),
    )
    nodes = []
    for o in objects:
        props = o["properties"]
        if isinstance(props, str):
            import json; props = json.loads(props)
        nodes.append({
            "id": str(o["id"]),
            "label": o["display_name"] or (props or {}).get("name", str(o["id"])[:8]),
            "type": o["object_type"],
        })

    return {"nodes": nodes, "edges": edges, "nodeCount": len(nodes), "edgeCount": len(edges)}


@router.get("/stats")
async def graph_stats(dataset: str = Query("default")):
    """Compute graph statistics: connected components, density, average degree."""
    pool = await get_pool()

    node_count = await pool.fetchval(
        "SELECT COUNT(*) FROM ontology_objects WHERE dataset_id = $1", dataset
    )
    edge_count = await pool.fetchval(
        "SELECT COUNT(*) FROM ontology_links WHERE dataset_id = $1", dataset
    )

    # Average degree (undirected: each edge contributes 2 to total degree)
    if node_count > 0:
        avg_degree = round((2.0 * edge_count) / node_count, 2)
        # Density: actual edges / max possible edges (n*(n-1))
        max_edges = node_count * (node_count - 1)
        density = round(edge_count / max_edges, 6) if max_edges > 0 else 0.0
    else:
        avg_degree = 0.0
        density = 0.0

    # Count weakly connected components via UNION + recursive traversal sampling
    components = 0
    if node_count > 0 and edge_count > 0:
        comp_row = await pool.fetchrow(
            """WITH RECURSIVE component_labels AS (
                -- Start from all nodes that are sources in links
                SELECT DISTINCT source_id AS node_id
                FROM ontology_links WHERE dataset_id = $1
            ),
            connected AS (
                SELECT l.source_id, l.target_id
                FROM ontology_links l
                WHERE l.dataset_id = $1
            ),
            -- Approximate component count via label propagation (1 iteration)
            components AS (
                SELECT COUNT(*) AS cnt FROM (
                    SELECT DISTINCT MIN(target_id) AS component_root
                    FROM connected
                    GROUP BY source_id
                ) sub
            )
            SELECT cnt FROM components""",
            dataset,
        )
        if comp_row:
            components = comp_row["cnt"]

    # Degree distribution
    degree_rows = await pool.fetch(
        """SELECT degree, COUNT(*) AS cnt FROM (
            SELECT COALESCE(out_deg.cnt, 0) + COALESCE(in_deg.cnt, 0) AS degree
            FROM (
                SELECT source_id AS node_id, COUNT(*) AS cnt
                FROM ontology_links WHERE dataset_id = $1 GROUP BY source_id
            ) out_deg
            FULL OUTER JOIN (
                SELECT target_id AS node_id, COUNT(*) AS cnt
                FROM ontology_links WHERE dataset_id = $1 GROUP BY target_id
            ) in_deg ON out_deg.node_id = in_deg.node_id
        ) deg GROUP BY degree ORDER BY degree""",
        dataset,
    )
    degree_distribution = {str(r["degree"]): r["cnt"] for r in degree_rows}

    return {
        "nodeCount": node_count,
        "edgeCount": edge_count,
        "density": density,
        "averageDegree": avg_degree,
        "componentsApprox": components,
        "degreeDistribution": degree_distribution,
    }
