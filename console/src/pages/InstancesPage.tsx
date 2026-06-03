import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Table,
  Input,
  Select,
  Button,
  Popconfirm,
  Tag,
  Tabs,
  message,
  Space,
  Modal,
  Descriptions,
  Tooltip,
} from "antd";
import {
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  LinkOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { useDataset } from "../hooks/useDataset";
import {
  fetchObjects,
  fetchTypes,
  searchObjects,
  createObject,
  deleteObject,
  fetchLinks,
  createLink,
  deleteLink,
  fetchActionHistory,
  type ObjectInstance,
  type GraphData,
} from "../api/endpoints";
import api from "../api/client";

interface LinkRecord {
  id: string;
  link_type: string;
  source_id: string;
  target_id: string;
  dataset_id: string;
  properties: Record<string, unknown>;
  confidence: number;
  created_at: string;
}

interface ActionRecord {
  id: string;
  action_type: string;
  status: string;
  executed_by: string;
  executed_at: string;
  error_message?: string;
}

export default function InstancesPage() {
  const [searchParams] = useSearchParams();
  const presetType = searchParams.get("type") || "";
  const { dataset } = useDataset();
  const [activeTab, setActiveTab] = useState("objects");
  const [typeFilter, setTypeFilter] = useState<string | undefined>(presetType || undefined);
  const [searchText, setSearchText] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailObj, setDetailObj] = useState<ObjectInstance | null>(null);
  const [newForm, setNewForm] = useState({ object_type: presetType || "", properties: "{}" });

  const [actionPage, setActionPage] = useState(1);
  const queryClient = useQueryClient();

  const { data: types } = useQuery({ queryKey: ["types", "OBJECT"], queryFn: () => fetchTypes("OBJECT") });
  const { data: linkTypes } = useQuery({ queryKey: ["types", "LINK"], queryFn: () => fetchTypes("LINK") });
  const { data: allTypes } = useQuery({ queryKey: ["types"], queryFn: () => fetchTypes() });

  const { data: objData, isLoading: objLoading } = useQuery({
    queryKey: ["objects", typeFilter, dataset, page],
    queryFn: () => fetchObjects({ type: typeFilter, dataset, page, size: 20 }),
    enabled: activeTab === "objects",
  });

  const { data: searchResults } = useQuery({
    queryKey: ["objects", "search", searchText],
    queryFn: () => searchObjects(searchText),
    enabled: searchText.length > 0 && activeTab === "objects",
  });

  const { data: linksData, isLoading: linksLoading } = useQuery({
    queryKey: ["links", dataset],
    queryFn: async () => {
      const res = await api.get<LinkRecord[]>("/links", { params: { dataset } });
      return res.data;
    },
    enabled: activeTab === "links",
  });

  const { data: actionsData, isLoading: actionsLoading } = useQuery({
    queryKey: ["actions-history", actionPage],
    queryFn: () => fetchActionHistory(actionPage, 20),
    enabled: activeTab === "actions",
  });

  const createMut = useMutation({
    mutationFn: (vals: Record<string, unknown>) => createObject(vals),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objects"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      setCreateOpen(false);
      setNewForm({ object_type: "", properties: "{}" });
      message.success("已创建");
    },
    onError: (err: any) => message.error(err.response?.data?.error?.message || "创建失败"),
  });

  const delMut = useMutation({
    mutationFn: (id: string) => deleteObject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objects"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      message.success("已删除");
    },
    onError: (err: any) => message.error(err.response?.data?.error?.message || "删除失败"),
  });

  const displayRows = searchText ? (searchResults || []) : (objData?.data || []);
  const total = searchText ? displayRows.length : (objData?.total || 0);

  const typeLabelMap: Record<string, string> = {};
  (allTypes || []).forEach((t) => { typeLabelMap[t.api_name] = t.display_name; });

  const objectColumns = [
    {
      title: "ID", dataIndex: "id", key: "id", width: 100,
      render: (v: string) => <Tooltip title={v}>{v.substring(0, 8)}...</Tooltip>,
    },
    {
      title: "名称", dataIndex: "display_name", key: "display_name", width: 160,
    },
    {
      title: "类型", dataIndex: "object_type", key: "object_type", width: 120,
      render: (v: string) => <Tag color="blue">{typeLabelMap[v] || v}</Tag>,
    },
    {
      title: "属性", dataIndex: "properties", key: "properties", width: 200,
      render: (props: Record<string, unknown>) => {
        if (!props || Object.keys(props).length === 0) return <span style={{ color: "#ccc" }}>—</span>;
        const entries = Object.entries(props).filter(([k]) => k !== "name").slice(0, 3);
        return (
          <Tooltip title={JSON.stringify(props, null, 2)}>
            <span style={{ fontSize: 12 }}>
              {entries.map(([k, v]) => (
                <Tag key={k} style={{ marginBottom: 2 }}>{k}: {typeof v === "object" ? JSON.stringify(v) : String(v)}</Tag>
              ))}
              {Object.keys(props).length > 4 && " …"}
            </span>
          </Tooltip>
        );
      },
    },
    {
      title: "创建时间", dataIndex: "created_at", key: "created_at", width: 140,
      render: (v: string) => v?.slice(0, 16).replace("T", " ") || "—",
    },
    {
      title: "操作", key: "actions", width: 100,
      render: (_: unknown, r: ObjectInstance) => (
        <Space size="small">
          <Button type="text" size="small" icon={<EyeOutlined />}
            onClick={() => { setDetailObj(r); setDetailOpen(true); }} />
          <Popconfirm title="确认删除？级联删除关联链接。" onConfirm={() => delMut.mutate(r.id)}>
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const linkColumns = [
    {
      title: "源对象", dataIndex: "source_id", key: "source_id", width: 120,
      render: (v: string) => <Tooltip title={v}>{v.substring(0, 8)}...</Tooltip>,
    },
    { title: "→", key: "arrow", width: 40, render: () => <LinkOutlined style={{ color: "#999" }} /> },
    {
      title: "目标对象", dataIndex: "target_id", key: "target_id", width: 120,
      render: (v: string) => <Tooltip title={v}>{v.substring(0, 8)}...</Tooltip>,
    },
    {
      title: "链接类型", dataIndex: "link_type", key: "link_type", width: 120,
      render: (v: string) => <Tag color="orange">{typeLabelMap[v] || v}</Tag>,
    },
    {
      title: "置信度", dataIndex: "confidence", key: "confidence", width: 80,
      render: (v: number) => <span>{v != null ? (v * 100).toFixed(0) + "%" : "—"}</span>,
    },
    {
      title: "操作", key: "actions", width: 60,
      render: (_: unknown, r: LinkRecord) => (
        <Popconfirm title="确认删除？" onConfirm={async () => {
          try {
            await deleteLink(r.id);
            queryClient.invalidateQueries({ queryKey: ["links"] });
            queryClient.invalidateQueries({ queryKey: ["stats"] });
            message.success("已删除");
          } catch (err: any) {
            message.error(err.response?.data?.error?.message || "删除失败");
          }
        }}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  const actionColumns = [
    { title: "动作", dataIndex: "action_type", key: "action_type", width: 150,
      render: (v: string) => <Tag color="green">{typeLabelMap[v] || v}</Tag> },
    { title: "状态", dataIndex: "status", key: "status", width: 80,
      render: (v: string) => <Tag color={v === "SUCCESS" ? "green" : v === "FAILED" ? "red" : "default"}>{v}</Tag> },
    { title: "执行者", dataIndex: "executed_by", key: "executed_by", width: 100 },
    { title: "执行时间", dataIndex: "executed_at", key: "executed_at", width: 160,
      render: (v: string) => v?.slice(0, 16).replace("T", " ") || "—" },
    { title: "错误", dataIndex: "error_message", key: "error_message",
      render: (v: string) => v ? <Tooltip title={v}><Tag color="red">有错误</Tag></Tooltip> : "—" },
  ];

  const tabs = [
    { key: "objects", label: `对象实例 (${total})` },
    { key: "links", label: `链接实例 (${(linksData || []).length})` },
    { key: "actions", label: `Action 历史 (${actionsData?.total ?? 0})` },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2>实例管理</h2>
        {activeTab === "objects" && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            新建对象
          </Button>
        )}
      </div>
      <Tabs activeKey={activeTab} onChange={(k) => { setActiveTab(k); setSearchText(""); setPage(1); }} items={tabs} />

      {activeTab === "objects" && (
        <>
          <Space style={{ marginBottom: 16 }}>
            <Select
              allowClear
              placeholder="按类型筛选"
              style={{ width: 180 }}
              value={typeFilter}
              onChange={(v) => { setTypeFilter(v); setPage(1); }}
              options={(types || []).map((t) => ({ value: t.api_name, label: t.display_name }))}
            />
            <Input
              prefix={<SearchOutlined />}
              placeholder="搜索对象（属性全文匹配）..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 280 }}
              allowClear
            />
          </Space>
          <Table
            columns={objectColumns}
            dataSource={displayRows}
            rowKey="id"
            loading={objLoading}
            size="middle"
            pagination={searchText ? false : { current: page, total, pageSize: 20, onChange: (p) => setPage(p), showSizeChanger: false }}
          />
        </>
      )}

      {activeTab === "links" && (
        <Table
          columns={linkColumns}
          dataSource={linksData || []}
          rowKey="id"
          loading={linksLoading}
          size="middle"
          pagination={{ pageSize: 20, showSizeChanger: false }}
        />
      )}

      {activeTab === "actions" && (
        <Table
          columns={actionColumns}
          dataSource={actionsData?.data || []}
          rowKey="id"
          loading={actionsLoading}
          size="middle"
          pagination={{
            current: actionPage,
            total: actionsData?.total || 0,
            pageSize: 20,
            onChange: (p) => setActionPage(p),
            showSizeChanger: false,
          }}
        />
      )}

      <Modal
        title="新建对象"
        open={createOpen}
        onOk={() => {
          try {
            const props = JSON.parse(newForm.properties);
            createMut.mutate({ object_type: newForm.object_type, dataset_id: dataset, properties: props });
          } catch {
            message.error("properties 不是合法 JSON");
          }
        }}
        onCancel={() => { setCreateOpen(false); setNewForm({ object_type: "", properties: "{}" }); }}
        confirmLoading={createMut.isPending}
        destroyOnHidden
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Select
            placeholder="选择对象类型"
            value={newForm.object_type || undefined}
            onChange={(v) => setNewForm({ ...newForm, object_type: v })}
            style={{ width: "100%" }}
            options={(types || []).map((t) => ({ value: t.api_name, label: t.display_name }))}
          />
          <Input.TextArea
            rows={8}
            value={newForm.properties}
            onChange={(e) => setNewForm({ ...newForm, properties: e.target.value })}
            placeholder='{"name": "示例名称", "region": "华东"}'
          />
        </div>
      </Modal>

      <Modal
        title={detailObj ? `对象详情: ${detailObj.display_name}` : ""}
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={<Button onClick={() => setDetailOpen(false)}>关闭</Button>}
        size="large"
        destroyOnHidden
      >
        {detailObj && (
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label="ID" span={2}>{detailObj.id}</Descriptions.Item>
            <Descriptions.Item label="对象类型"><Tag color="blue">{detailObj.object_type}</Tag></Descriptions.Item>
            <Descriptions.Item label="数据集">{detailObj.dataset_id}</Descriptions.Item>
            <Descriptions.Item label="显示名称" span={2}>{detailObj.display_name || "—"}</Descriptions.Item>
            <Descriptions.Item label="External ID">{detailObj.external_id || "—"}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{detailObj.created_at?.slice(0, 16).replace("T", " ") || "—"}</Descriptions.Item>
            <Descriptions.Item label="属性详情" span={2}>
              <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 4, maxHeight: 300, overflow: "auto", fontSize: 13 }}>
                {JSON.stringify(detailObj.properties, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}
