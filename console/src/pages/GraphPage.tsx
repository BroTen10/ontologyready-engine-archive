import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Card,
  Spin,
  Tabs,
  Button,
  Dropdown,
  Tooltip,
  Tag,
  Segmented,
  message,
  Space,
  Input,
  Alert,
  Descriptions,
  Divider,
} from "antd";
import {
  DatabaseOutlined,
  LinkOutlined,
  AppstoreOutlined,
  ThunderboltOutlined,
  AimOutlined,
  ReloadOutlined,
  CameraOutlined,
  ApartmentOutlined,
  SearchOutlined,
  BranchesOutlined,
  EnvironmentOutlined,
} from "@ant-design/icons";
import dagre from "dagre";
import { fetchStructureGraph, fetchEntityGraph, fetchStats, findPath, getNeighbors, fetchGraphStats, type GraphData } from "../api/endpoints";
import { useDataset } from "../hooks/useDataset";
import { useNavigate } from "react-router-dom";

type LayoutMode = "dagre-tb" | "dagre-lr";

function layoutDagre(nodes: Node[], edges: Edge[], direction: "TB" | "LR" = "TB"): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, nodesep: 60, ranksep: 100 });

  for (const n of nodes) {
    g.setNode(n.id, { width: 180, height: 60 });
  }
  for (const e of edges) {
    g.setEdge(e.source, e.target);
  }
  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      ...n,
      position: { x: pos.x - 90, y: pos.y - 30 },
    };
  });
}

function graphToFlow(data: GraphData): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = (data.nodes || []).map((n) => ({
    id: n.id,
    type: "default",
    data: { label: n.label || n.id, ...n },
    position: { x: 0, y: 0 },
  }));
  const edges: Edge[] = (data.edges || []).map((e, i) => ({
    id: e.id || `e-${i}`,
    source: e.source,
    target: e.target,
    label: e.label,
    type: "smoothstep",
    animated: true,
  }));
  return { nodes, edges };
}

export default function GraphPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { dataset } = useDataset();
  const [graphTab, setGraphTab] = useState<"structure" | "entities">("structure");
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("dagre-tb");

  // Phase B: 路径查找
  const [pathSource, setPathSource] = useState("");
  const [pathTarget, setPathTarget] = useState("");
  const [pathResult, setPathResult] = useState<Awaited<ReturnType<typeof findPath>> | null>(null);
  const [pathLoading, setPathLoading] = useState(false);

  // Phase B: 图谱统计
  const { data: graphStats } = useQuery({
    queryKey: ["graph-stats", dataset],
    queryFn: () => fetchGraphStats(dataset),
    enabled: graphTab === "entities",
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });

  const { data: structureData, isLoading: structureLoading } = useQuery({
    queryKey: ["graph-structure"],
    queryFn: fetchStructureGraph,
    enabled: graphTab === "structure",
  });

  const { data: entityData, isLoading: entityLoading } = useQuery({
    queryKey: ["graph-entities", dataset],
    queryFn: () => fetchEntityGraph(dataset),
    enabled: graphTab === "entities",
  });

  const graphData = graphTab === "structure" ? structureData : entityData;
  const isLoading = graphTab === "structure" ? structureLoading : entityLoading;

  const initialised = useRef(false);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    if (!graphData) return;
    const { nodes: rawNodes, edges: rawEdges } = graphToFlow(graphData);
    const laidOut = layoutDagre(rawNodes, rawEdges, layoutMode === "dagre-tb" ? "TB" : "LR");
    setNodes(laidOut);
    setEdges(rawEdges);
    initialised.current = true;
  }, [graphData, layoutMode, setNodes, setEdges]);

  const relayout = useCallback(() => {
    const laidOut = layoutDagre(nodes, edges, layoutMode === "dagre-tb" ? "TB" : "LR");
    setNodes(laidOut);
  }, [nodes, edges, layoutMode, setNodes]);

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (graphTab === "structure") {
        navigate(`/types?name=${node.id}`);
      }
    },
    [graphTab, navigate],
  );

  const contextMenuItems = useMemo(
    () => [
      {
        key: "refresh",
        icon: <ReloadOutlined />,
        label: "刷新数据",
        onClick: () => {
          queryClient.invalidateQueries({ queryKey: ["graph-structure"] });
          queryClient.invalidateQueries({ queryKey: ["graph-entities"] });
          message.success("已刷新");
        },
      },
      {
        key: "fit",
        icon: <AimOutlined />,
        label: "适应画布",
        onClick: () => message.info("请使用右下角控制器的适应按钮"),
      },
      {
        key: "export",
        icon: <CameraOutlined />,
        label: "导出 PNG",
        onClick: () => message.info("导出功能即将支持"),
      },
    ],
    [queryClient],
  );

  const statCards = [
    { title: "对象实例", value: stats?.objectCount ?? 0, icon: <DatabaseOutlined />, color: "#1890ff" },
    { title: "链接关系", value: stats?.linkCount ?? 0, icon: <LinkOutlined />, color: "#52c41a" },
    { title: "类型定义", value: stats?.typeCount ?? 0, icon: <AppstoreOutlined />, color: "#722ed1" },
    { title: "今日动作", value: stats?.actionsToday ?? 0, icon: <ThunderboltOutlined />, color: "#fa8c16" },
  ];

  // Phase B: 路径查找处理
  const handleFindPath = useCallback(async () => {
    if (!pathSource || !pathTarget) {
      message.warning("请输入起点和终点节点 ID");
      return;
    }
    setPathLoading(true);
    try {
      const result = await findPath(pathSource, pathTarget, dataset);
      setPathResult(result);
      if (result.found) {
        message.success(`找到路径，长度: ${result.length}`);
      } else {
        message.info("未找到路径");
      }
    } catch {
      message.error("路径查找失败");
    } finally {
      setPathLoading(false);
    }
  }, [pathSource, pathTarget, dataset]);

  const handleExploreNeighbors = useCallback(async (nodeId: string) => {
    try {
      const result = await getNeighbors(nodeId, dataset, "both");
      message.info(`节点 ${nodeId} 有 ${result.count} 个邻居`);
    } catch {
      message.error("邻居查询失败");
    }
  }, [dataset]);

  const layoutLabels: Record<LayoutMode, string> = {
    "dagre-tb": "上下层次",
    "dagre-lr": "左右层次",
  };

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>概览</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
        {statCards.map((s) => (
          <Card key={s.title} size="small">
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 28, color: s.color }}>{s.icon}</span>
              <div>
                <div style={{ fontSize: 24, fontWeight: 700 }}>{statsLoading ? "—" : s.value}</div>
                <div style={{ color: "#999" }}>{s.title}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Phase B: 路径查找 & 图谱统计 */}
      {graphTab === "entities" && (
        <Card size="small" title={<><BranchesOutlined /> 路径查找 & 图谱分析</>} style={{ marginBottom: 16 }}>
          <Space direction="vertical" style={{ width: "100%" }}>
            <Space>
              <Input
                placeholder="起点节点 UUID"
                value={pathSource}
                onChange={(e) => setPathSource(e.target.value)}
                style={{ width: 300 }}
                prefix={<EnvironmentOutlined />}
              />
              <Input
                placeholder="终点节点 UUID"
                value={pathTarget}
                onChange={(e) => setPathTarget(e.target.value)}
                style={{ width: 300 }}
                prefix={<EnvironmentOutlined />}
              />
              <Button
                type="primary"
                icon={<SearchOutlined />}
                loading={pathLoading}
                onClick={handleFindPath}
              >
                查找最短路径
              </Button>
            </Space>
            {pathResult && (
              <Alert
                type={pathResult.found ? "success" : "info"}
                message={pathResult.found ? `找到路径 (长度: ${pathResult.length})` : "未找到路径"}
                description={
                  pathResult.found
                    ? `路径: ${pathResult.path.map((n) => n.label).join(" → ")}`
                    : "两节点之间不存在可达路径"
                }
                style={{ marginTop: 8 }}
              />
            )}
            {graphStats && (
              <Descriptions size="small" column={4} style={{ marginTop: 8 }}>
                <Descriptions.Item label="节点数">{graphStats.nodeCount}</Descriptions.Item>
                <Descriptions.Item label="边数">{graphStats.edgeCount}</Descriptions.Item>
                <Descriptions.Item label="密度">{graphStats.density}</Descriptions.Item>
                <Descriptions.Item label="平均度">{graphStats.averageDegree}</Descriptions.Item>
              </Descriptions>
            )}
          </Space>
        </Card>
      )}

      <Card
        title={
          <Tabs
            activeKey={graphTab}
            onChange={(k) => setGraphTab(k as "structure" | "entities")}
            style={{ marginBottom: -16 }}
            items={[
              { key: "structure", label: "结构图谱" },
              { key: "entities", label: "实体图谱" },
            ]}
          />
        }
        extra={
          <Space>
            <Segmented
              size="small"
              value={layoutMode}
              onChange={(v) => setLayoutMode(v as LayoutMode)}
              options={[
                { value: "dagre-tb", label: "上下" },
                { value: "dagre-lr", label: "左右" },
              ]}
            />
            <Button size="small" icon={<ReloadOutlined />} onClick={relayout}>
              重新布局
            </Button>
            <Dropdown menu={{ items: contextMenuItems }} trigger={["click"]}>
              <Button size="small">更多</Button>
            </Dropdown>
          </Space>
        }
        styles={{ body: { padding: 0 } }}
      >
        <div style={{ height: 520 }}>
          {isLoading ? (
            <Spin size="large" style={{ display: "block", margin: "200px auto" }} />
          ) : graphData && initialised.current ? (
            <Dropdown menu={{ items: contextMenuItems }} trigger={["contextMenu"]}>
              <div style={{ width: "100%", height: "100%" }}>
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  onNodeClick={onNodeClick}
                  fitView
                  attributionPosition="bottom-left"
                  minZoom={0.1}
                  maxZoom={2}
                >
                  <Background color="#f0f0f0" gap={20} />
                  <Controls showInteractive={false} />
                  <MiniMap
                    nodeStrokeWidth={3}
                    pannable
                    zoomable
                    style={{ border: "1px solid #e8e8e8" }}
                  />
                  <Panel position="top-right">
                    <Tag color="processing" style={{ margin: 0 }}>
                      {layoutLabels[layoutMode]}
                    </Tag>
                  </Panel>
                </ReactFlow>
              </div>
            </Dropdown>
          ) : (
            <div style={{ textAlign: "center", color: "#999", padding: "120px 0" }}>
              <ApartmentOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <p>暂无图谱数据，请先创建类型定义和实例</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
