import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  Spin,
  message,
  Popconfirm,
  Tabs,
  Table,
  Switch,
  Drawer,
  Descriptions,
  Space,
  Tooltip,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ThunderboltOutlined,
  LinkOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { fetchTypes, createType, deleteType, updateType, type TypeDef } from "../api/endpoints";

const TYPE_ICONS: Record<string, React.ReactNode> = {
  OBJECT: <DatabaseOutlined />,
  LINK: <LinkOutlined />,
  ACTION: <ThunderboltOutlined />,
};

const TYPE_COLORS: Record<string, string> = { OBJECT: "#1890ff", LINK: "#faad14", ACTION: "#52c41a" };

const PROPERTY_TYPES = ["STRING", "NUMBER", "BOOLEAN", "DATE", "DATETIME", "JSON", "ARRAY", "REFERENCE"];

interface PropDef {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

interface ConfigEditor {
  [key: string]: unknown;
  properties?: PropDef[];
  icon?: string;
  color?: string;
  sourceType?: string;
  targetType?: string;
  parameters?: Array<{ name: string; type: string; required: boolean; description: string }>;
}

function parseConfig(config: Record<string, unknown>): ConfigEditor {
  if (typeof config === "object" && config !== null) return { ...config };
  return {};
}

function parseProperties(config: Record<string, unknown>): PropDef[] {
  const c = parseConfig(config);
  const props = c.properties;
  if (Array.isArray(props)) return props as PropDef[];
  return [];
}

export default function TypesPage() {
  const [searchParams] = useSearchParams();
  const presetName = searchParams.get("name") || "";
  const [activeTab, setActiveTab] = useState<string>("OBJECT");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TypeDef | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const [properties, setProperties] = useState<PropDef[]>([]);
  const [jsonEditMode, setJsonEditMode] = useState(false);
  const [jsonText, setJsonText] = useState("");

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerType, setDrawerType] = useState<TypeDef | null>(null);

  const [jsonViewOpen, setJsonViewOpen] = useState(false);
  const [jsonViewConfig, setJsonViewConfig] = useState("");

  const { data: types, isLoading } = useQuery({
    queryKey: ["types", activeTab],
    queryFn: () => fetchTypes(activeTab),
  });

  useEffect(() => {
    if (presetName) {
      const tab = types?.find((t) => t.api_name === presetName);
      if (tab) setActiveTab(tab.type);
    }
  }, [presetName, types]);

  const createMut = useMutation({
    mutationFn: (vals: Record<string, unknown>) => createType(vals),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["types"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      setModalOpen(false);
      form.resetFields();
      setProperties([]);
      message.success("类型已创建");
    },
    onError: (err: any) => message.error(err.response?.data?.error?.message || "创建失败"),
  });

  const delMut = useMutation({
    mutationFn: (name: string) => deleteType(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["types"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      message.success("已删除");
    },
    onError: (err: any) => message.error(err.response?.data?.error?.message || "删除失败"),
  });

  const openCreate = (tab: string) => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ type: tab, maturity: "DRAFT" });
    setProperties([]);
    setJsonEditMode(false);
    setJsonText("");
    setModalOpen(true);
  };

  const openEdit = (t: TypeDef) => {
    setEditing(t);
    form.setFieldsValue(t);
    const props = parseProperties(t.config);
    setProperties(props);
    setJsonEditMode(false);
    setJsonText("");
    setModalOpen(true);
  };

  const showDetail = (t: TypeDef) => {
    setDrawerType(t);
    setDrawerOpen(true);
  };

  const showJsonConfig = (t: TypeDef) => {
    setJsonViewConfig(JSON.stringify(t.config, null, 2));
    setJsonViewOpen(true);
  };

  const handleSubmit = () => {
    if (jsonEditMode) {
      let parsed: ConfigEditor;
      try {
        parsed = JSON.parse(jsonText);
      } catch {
        message.error("JSON 格式无效");
        return;
      }
      form.validateFields().then((vals) => {
        const payload = { ...vals, config: parsed, properties: parsed.properties || [] };
        if (editing) {
          updateType(editing.api_name, payload).then(() => {
            queryClient.invalidateQueries({ queryKey: ["types"] });
            setModalOpen(false);
            message.success("已更新");
          }).catch((err: any) => message.error(err.response?.data?.error?.message || "更新失败"));
        } else {
          createMut.mutate(payload);
        }
      }).catch(() => {});
      return;
    }
    form.validateFields().then((vals) => {
      const existingConfig = editing ? parseConfig(editing.config) : {};
      const mergedConfig: ConfigEditor = {
        ...existingConfig,
        ...vals.config,
        properties,
      };
      const payload = { ...vals, config: mergedConfig, properties };
      if (editing) {
        updateType(editing.api_name, payload).then(() => {
          queryClient.invalidateQueries({ queryKey: ["types"] });
          setModalOpen(false);
          message.success("已更新");
        }).catch((err: any) => message.error(err.response?.data?.error?.message || "更新失败"));
      } else {
        createMut.mutate(payload);
      }
    }).catch(() => {});
  };

  const addProperty = () => {
    setProperties([...properties, { name: "", type: "STRING", required: false, description: "" }]);
  };

  const updateProperty = (idx: number, field: keyof PropDef, value: unknown) => {
    const next = [...properties];
    next[idx] = { ...next[idx], [field]: value };
    setProperties(next);
  };

  const removeProperty = (idx: number) => {
    setProperties(properties.filter((_, i) => i !== idx));
  };

  const tabs = [
    { key: "OBJECT", label: `对象类型 (${(types ?? []).filter((t) => t.type === "OBJECT").length})` },
    { key: "LINK", label: `链接类型 (${(types ?? []).filter((t) => t.type === "LINK").length})` },
    { key: "ACTION", label: `动作类型 (${(types ?? []).filter((t) => t.type === "ACTION").length})` },
  ];

  const propertyColumns = [
    { title: "属性名", dataIndex: "name", key: "name", width: 110,
      render: (_: unknown, __: PropDef, idx: number) => (
        <Input size="small" value={properties[idx]?.name ?? ""} placeholder="name"
          onChange={(e) => updateProperty(idx, "name", e.target.value)} />
      ),
    },
    { title: "类型", dataIndex: "type", key: "type", width: 120,
      render: (_: unknown, __: PropDef, idx: number) => (
        <Select size="small" value={properties[idx]?.type ?? "STRING"} style={{ width: 100 }}
          onChange={(v) => updateProperty(idx, "type", v)}>
          {PROPERTY_TYPES.map((pt) => (<Select.Option key={pt} value={pt}>{pt}</Select.Option>))}
        </Select>
      ),
    },
    { title: "必填", dataIndex: "required", key: "required", width: 56,
      render: (_: unknown, __: PropDef, idx: number) => (
        <Switch size="small" checked={properties[idx]?.required ?? false}
          onChange={(v) => updateProperty(idx, "required", v)} />
      ),
    },
    { title: "描述", dataIndex: "description", key: "description",
      render: (_: unknown, __: PropDef, idx: number) => (
        <Input size="small" value={properties[idx]?.description ?? ""} placeholder="属性说明"
          onChange={(e) => updateProperty(idx, "description", e.target.value)} />
      ),
    },
    { title: "", key: "action", width: 40,
      render: (_: unknown, __: PropDef, idx: number) => (
        <Button type="text" size="small" danger icon={<DeleteOutlined />}
          onClick={() => removeProperty(idx)} />
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2>类型定义</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => openCreate(activeTab)}>
          新建类型
        </Button>
      </div>
      <Tabs activeKey={activeTab} onChange={(k) => setActiveTab(k)} items={tabs} />
      {isLoading ? (
        <Spin size="large" style={{ display: "block", margin: "60px auto" }} />
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
          {(types || []).map((t) => {
            const cfg = parseConfig(t.config);
            const iconColor = cfg.color || TYPE_COLORS[t.type] || "#666";
            const propsCount = parseProperties(t.config).length;
            return (
              <Card
                key={t.api_name}
                size="small"
                hoverable
                style={{ borderTop: `3px solid ${iconColor}` }}
                onClick={() => showDetail(t)}
                title={
                  <Space>
                    <span style={{ color: iconColor, fontSize: 18 }}>{TYPE_ICONS[t.type]}</span>
                    <span style={{ fontWeight: 600 }}>{t.display_name}</span>
                  </Space>
                }
                extra={
                  <Tag color={t.maturity === "ACTIVE" ? "green" : t.maturity === "DEPRECATED" ? "red" : "default"}>
                    {t.maturity}
                  </Tag>
                }
                actions={[
                  <Tooltip key="view" title="查看详情"><EyeOutlined onClick={(e) => { e.stopPropagation(); showDetail(t); }} /></Tooltip>,
                  <Tooltip key="edit" title="编辑"><EditOutlined onClick={(e) => { e.stopPropagation(); openEdit(t); }} /></Tooltip>,
                  <Popconfirm key="del" title="确认删除此类型？" onConfirm={(e) => { e?.stopPropagation(); delMut.mutate(t.api_name); }}>
                    <DeleteOutlined onClick={(e) => e.stopPropagation()} />
                  </Popconfirm>,
                ]}
              >
                <p style={{ color: "#999", fontSize: 12, marginBottom: 4 }}>{t.api_name}</p>
                <p style={{ marginBottom: 8, minHeight: 40 }}>{t.description || "—"}</p>
                <div style={{ display: "flex", gap: 16, fontSize: 12, color: "#999" }}>
                  <span>属性: {propsCount}</span>
                  <span>创建: {t.created_at?.slice(0, 10) || "—"}</span>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <Modal
        title={editing ? `编辑类型: ${editing.api_name}` : "新建类型"}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={createMut.isPending}
        size="large"
        destroyOnHidden
        footer={[
          <Button key="json" onClick={() => {
            if (jsonEditMode) {
              setJsonEditMode(false);
            } else {
              const currentConfig = editing ? parseConfig(editing.config) : {};
              const merged: ConfigEditor = { ...currentConfig, properties };
              setJsonText(JSON.stringify(merged, null, 2));
              setJsonEditMode(true);
            }
          }}>
            {jsonEditMode ? "表单模式" : "JSON 编辑"}
          </Button>,
          <Button key="cancel" onClick={() => setModalOpen(false)}>取消</Button>,
          <Button key="submit" type="primary" loading={createMut.isPending} onClick={handleSubmit}>保存</Button>,
        ]}
      >
        {jsonEditMode ? (
          <Input.TextArea
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            rows={20}
            style={{ fontFamily: "monospace", fontSize: 13 }}
            placeholder='{"properties": [...], "color": "#1890ff", ...}'
          />
        ) : (
          <Form form={form} layout="vertical">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 24px" }}>
              <Form.Item name="api_name" label="API Name" rules={[{ required: true, message: "必填" }]}>
                <Input disabled={!!editing} placeholder="英文标识，如 Customer" />
              </Form.Item>
              <Form.Item name="type" label="类型" rules={[{ required: true }]}>
                <Select disabled={!!editing}>
                  <Select.Option value="OBJECT">对象类型</Select.Option>
                  <Select.Option value="LINK">链接类型</Select.Option>
                  <Select.Option value="ACTION">动作类型</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="display_name" label="显示名称" rules={[{ required: true, message: "必填" }]}>
                <Input placeholder="中文名称" />
              </Form.Item>
              <Form.Item name="maturity" label="成熟度">
                <Select>
                  <Select.Option value="DRAFT">Draft</Select.Option>
                  <Select.Option value="ACTIVE">Active</Select.Option>
                  <Select.Option value="DEPRECATED">Deprecated</Select.Option>
                </Select>
              </Form.Item>
            </div>
            <Form.Item name="description" label="描述" rules={[{ required: true, message: "必填" }]}>
              <Input.TextArea rows={2} placeholder="面向 LLM 和 AI Agent 的自然语言描述" />
            </Form.Item>

            <div style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span style={{ fontWeight: 500 }}>属性定义</span>
                <Button size="small" type="dashed" icon={<PlusOutlined />} onClick={addProperty}>添加属性</Button>
              </div>
              {properties.length === 0 ? (
                <div style={{ color: "#999", padding: 16, textAlign: "center", border: "1px dashed #d9d9d9", borderRadius: 6 }}>
                  暂无属性，点击「添加属性」或使用 JSON 编辑模式
                </div>
              ) : (
                <Table
                  size="small"
                  rowKey={(_, idx) => `${idx}`}
                  dataSource={properties}
                  columns={propertyColumns}
                  pagination={false}
                  style={{ marginBottom: 8 }}
                />
              )}
            </div>
          </Form>
        )}
      </Modal>

      <Drawer
        title={drawerType ? `${drawerType.display_name} 详情` : ""}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        size="large"
        extra={
          <Space>
            <Button icon={<EditOutlined />} onClick={() => { setDrawerOpen(false); if (drawerType) openEdit(drawerType); }}>
              编辑
            </Button>
            <Button onClick={() => { if (drawerType) showJsonConfig(drawerType); }}>
              查看 JSON 配置
            </Button>
          </Space>
        }
      >
        {drawerType && (
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="API Name">{drawerType.api_name}</Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag color={TYPE_COLORS[drawerType.type]}>{drawerType.type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="显示名称">{drawerType.display_name}</Descriptions.Item>
            <Descriptions.Item label="描述">{drawerType.description}</Descriptions.Item>
            <Descriptions.Item label="成熟度">
              <Tag color={drawerType.maturity === "ACTIVE" ? "green" : drawerType.maturity === "DEPRECATED" ? "red" : "default"}>
                {drawerType.maturity}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">{drawerType.created_at || "—"}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{drawerType.updated_at || "—"}</Descriptions.Item>
            <Descriptions.Item label="属性数量">{parseProperties(drawerType.config).length}</Descriptions.Item>
            {parseProperties(drawerType.config).length > 0 && (
              <Descriptions.Item label="属性列表">
                <Table
                  size="small"
                  rowKey="name"
                  dataSource={parseProperties(drawerType.config)}
                  columns={[
                    { title: "名称", dataIndex: "name", key: "name" },
                    { title: "类型", dataIndex: "type", key: "type", render: (v: string) => <Tag>{v}</Tag> },
                    { title: "必填", dataIndex: "required", key: "required", width: 56,
                      render: (v: boolean) => v ? <Tag color="red">是</Tag> : <span>否</span> },
                    { title: "说明", dataIndex: "description", key: "description" },
                  ]}
                  pagination={false}
                />
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Drawer>

      <Modal
        title="JSON 配置"
        open={jsonViewOpen}
        onCancel={() => setJsonViewOpen(false)}
        footer={null}
        size="large"
      >
        <pre style={{ background: "#f5f5f5", padding: 16, borderRadius: 6, maxHeight: 400, overflow: "auto", fontSize: 13 }}>
          {jsonViewConfig}
        </pre>
      </Modal>
    </div>
  );
}
