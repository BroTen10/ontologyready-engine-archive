import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card, Table, Button, Space, Modal, Form, Input, Select, message, Tag, Popconfirm, Descriptions,
} from "antd";
import { PlusOutlined, ReloadOutlined, PlayCircleOutlined, EyeOutlined } from "@ant-design/icons";
import {
  fetchLlmConfigs, createLlmConfig, updateLlmConfig, deleteLlmConfig, testLlmConnection,
} from "../api/endpoints";

const PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "tongyi", label: "通义千问" },
  { value: "deepseek", label: "DeepSeek" },
];

export default function LLMConfigPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<Record<string, unknown> | null>(null);
  const [form] = Form.useForm();
  const [testResult, setTestResult] = useState<string | null>(null);

  const { data: configs, isLoading } = useQuery({
    queryKey: ["llm-configs"],
    queryFn: fetchLlmConfigs,
  });

  const saveMut = useMutation({
    mutationFn: async (v: Record<string, unknown>) => {
      if (editingId) {
        return updateLlmConfig(editingId, v);
      }
      return createLlmConfig(v);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm-configs"] });
      message.success(editingId ? "配置已更新" : "配置已创建");
      setModalOpen(false);
      setEditingId(null);
      form.resetFields();
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "操作失败";
      message.error(msg);
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteLlmConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm-configs"] });
      message.success("配置已删除");
    },
  });

  const testMut = useMutation({
    mutationFn: testLlmConnection,
    onSuccess: (data) => {
      setTestResult(`连接成功: ${JSON.stringify(data)}`);
      message.success("连接测试成功");
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "连接失败";
      setTestResult(`连接失败: ${msg}`);
      message.error(msg);
    },
  });

  const openEdit = (record: Record<string, unknown>) => {
    setEditingId(record.id as string);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const columns = [
    { title: "名称", dataIndex: "name", key: "name", width: 160 },
    {
      title: "厂商", dataIndex: "provider", key: "provider", width: 120,
      render: (p: string) => {
        const provider = PROVIDERS.find((pr) => pr.value === p);
        return <Tag color="blue">{provider?.label || p}</Tag>;
      },
    },
    { title: "模型", dataIndex: "model", key: "model", width: 160 },
    { title: "端点", dataIndex: "endpoint", key: "endpoint", ellipsis: true },
    {
      title: "状态", dataIndex: "status", key: "status", width: 100,
      render: (s: string) => <Tag color={s === "active" ? "green" : "default"}>{s === "active" ? "启用" : "停用"}</Tag>,
    },
    {
      title: "操作", key: "actions", width: 320,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => { setSelectedConfig(record); setDetailOpen(true); }} />
          <Button size="small" icon={<PlayCircleOutlined />}
            onClick={() => testMut.mutate(record.id as string)}
            loading={testMut.isPending}
          >
            测试连接
          </Button>
          <Button size="small" onClick={() => openEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => deleteMut.mutate(record.id as string)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>LLM 配置管理</h2>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ["llm-configs"] })}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingId(null); form.resetFields(); setModalOpen(true); }}>
            添加配置
          </Button>
        </Space>
      </div>

      {testResult && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <pre style={{ margin: 0 }}>{testResult}</pre>
        </Card>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={configs as Record<string, unknown>[]}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editingId ? "编辑 LLM 配置" : "添加 LLM 配置"}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); setEditingId(null); }}
        onOk={() => form.submit()}
        confirmLoading={saveMut.isPending}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={(v) => saveMut.mutate(v)}>
          <Form.Item name="name" label="配置名称" rules={[{ required: true }]}>
            <Input placeholder="如: 生产环境 OpenAI" />
          </Form.Item>
          <Form.Item name="provider" label="厂商" rules={[{ required: true }]}>
            <Select options={PROVIDERS} />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: !editingId }]}>
            <Input.Password placeholder={editingId ? "留空则不修改" : "输入 API Key"} />
          </Form.Item>
          <Form.Item name="endpoint" label="API 端点">
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item name="model" label="默认模型" rules={[{ required: true }]}>
            <Input placeholder="gpt-4o" />
          </Form.Item>
          <Form.Item name="settings" label="额外设置 (JSON)">
            <Input.TextArea rows={4} placeholder='{"temperature": 0.7, "max_tokens": 4096}' />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="配置详情"
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={640}
      >
        {selectedConfig && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="名称">{selectedConfig.name as string}</Descriptions.Item>
            <Descriptions.Item label="厂商">
              <Tag color="blue">{PROVIDERS.find((p) => p.value === selectedConfig.provider)?.label || (selectedConfig.provider as string)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="模型">{selectedConfig.model as string}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={(selectedConfig.status as string) === "active" ? "green" : "default"}>
                {selectedConfig.status as string}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="端点" span={2}>{selectedConfig.endpoint as string}</Descriptions.Item>
            <Descriptions.Item label="设置" span={2}>
              <pre style={{ maxHeight: 150, overflow: "auto", background: "#f5f5f5", padding: 8, borderRadius: 4 }}>
                {JSON.stringify(selectedConfig.settings, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}
