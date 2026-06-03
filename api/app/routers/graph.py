from fastapi import APIRouter

from ..database import get_pool

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
