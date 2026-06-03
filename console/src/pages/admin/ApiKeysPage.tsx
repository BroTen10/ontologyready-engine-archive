import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Button, Space, Modal, Form, Input, DatePicker, Switch, message, Popconfirm, Tag } from "antd";
import { PlusOutlined, ReloadOutlined, CopyOutlined } from "@ant-design/icons";
import { fetchApiKeys, createApiKey, updateApiKey, deleteApiKey, fetchPats, createPat, deletePat } from "../../api/endpoints";
export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [patModalOpen, setPatModalOpen] = useState(false);
  const [editingKey, setEditingKey] = useState<Record<string, unknown> | null>(null);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [patForm] = Form.useForm();

  const { data: apiKeys, isLoading } = useQuery({ queryKey: ["api-keys"], queryFn: fetchApiKeys });
  const { data: pats, isLoading: patsLoading } = useQuery({ queryKey: ["pats"], queryFn: fetchPats });

  const createKeyMut = useMutation({
    mutationFn: createApiKey,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setNewKey((data as { key?: string }).key || "密钥已创建，请妥善保存");
      message.success("API Key 已创建");
      setModalOpen(false); form.resetFields();
    },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "创建失败"),
  });

  const updateKeyMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) => updateApiKey(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["api-keys"] }); message.success("API Key 已更新"); setModalOpen(false); },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "更新失败"),
  });

  const deleteKeyMut = useMutation({
    mutationFn: deleteApiKey,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["api-keys"] }); message.success("API Key 已删除"); },
  });

  const createPatMut = useMutation({
    mutationFn: createPat,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["pats"] });
      message.success(`PAT 已创建: ${(data as { token?: string }).token || ""}`);
      setPatModalOpen(false); patForm.resetFields();
    },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "创建失败"),
  });

  const deletePatMut = useMutation({
    mutationFn: deletePat,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["pats"] }); message.success("PAT 已删除"); },
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => message.success("已复制到剪贴板"));
  };

  const keyColumns = [
    { title: "名称", dataIndex: "name", key: "name", width: 160 },
    { title: "密钥前缀", dataIndex: "key_prefix", key: "key_prefix", width: 200, render: (v: string) => v ? `${v}...` : "—" },
    {
      title: "状态", dataIndex: "is_active", key: "is_active", width: 100,
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "启用" : "禁用"}</Tag>,
    },
    { title: "过期", dataIndex: "expires_at", key: "expires_at", width: 180, render: (v: string) => v || "永不过期" },
    {
      title: "操作", key: "actions", width: 200,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size="small">
          <Button size="small" onClick={() => { setEditingKey(record); form.setFieldsValue(record); setModalOpen(true); }}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => deleteKeyMut.mutate(record.id as string)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const patColumns = [
    { title: "名称", dataIndex: "name", key: "name", width: 160 },
    { title: "范围", dataIndex: "scopes", key: "scopes", ellipsis: true, render: (v: unknown) => JSON.stringify(v) },
    {
      title: "状态", dataIndex: "is_active", key: "is_active", width: 100,
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "启用" : "禁用"}</Tag>,
    },
    { title: "过期", dataIndex: "expires_at", key: "expires_at", width: 180, render: (v: string) => v || "永不过期" },
    {
      title: "操作", key: "actions", width: 100,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Popconfirm title="确定删除？" onConfirm={() => deletePatMut.mutate(record.id as string)}>
          <Button size="small" danger>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      {newKey && (
        <Modal title="新创建的 API Key" open={!!newKey} onCancel={() => setNewKey(null)} footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={() => copyToClipboard(newKey)}>复制</Button>,
          <Button key="close" type="primary" onClick={() => setNewKey(null)}>关闭</Button>,
        ]}>
          <div style={{ background: "#fff7e6", border: "1px solid #ffd591", padding: 16, borderRadius: 8, wordBreak: "break-all", fontFamily: "monospace" }}>
            {newKey}
          </div>
          <p style={{ color: "#fa8c16", marginTop: 8 }}>请立即复制并妥善保存此密钥，关闭后将无法再次查看。</p>
        </Modal>
      )}

      <h3 style={{ marginBottom: 16 }}>API Key 管理</h3>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ["api-keys"] })}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingKey(null); form.resetFields(); setModalOpen(true); }}>创建 API Key</Button>
        </Space>
      </div>
      <Table columns={keyColumns} dataSource={apiKeys as Record<string, unknown>[]} rowKey="id" loading={isLoading} pagination={false} size="small" />

      <h3 style={{ marginTop: 32, marginBottom: 16 }}>个人访问令牌 (PAT)</h3>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { patForm.resetFields(); setPatModalOpen(true); }}>创建 PAT</Button>
      </div>
      <Table columns={patColumns} dataSource={pats as Record<string, unknown>[]} rowKey="id" loading={patsLoading} pagination={false} size="small" />

      <Modal title={editingKey ? "编辑 API Key" : "创建 API Key"} open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} confirmLoading={createKeyMut.isPending || updateKeyMut.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => {
          if (editingKey) {
            updateKeyMut.mutate({ id: editingKey.id as string, data: v });
          } else {
            createKeyMut.mutate(v);
          }
        }}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          {!editingKey && <Form.Item name="permissions" label="权限 (JSON)" help='如: ["read", "write"]'><Input.TextArea rows={3} /></Form.Item>}
          <Form.Item name="is_active" label="启用" valuePropName="checked" initialValue={true}><Switch /></Form.Item>
        </Form>
      </Modal>

      <Modal title="创建个人访问令牌" open={patModalOpen} onCancel={() => setPatModalOpen(false)} onOk={() => patForm.submit()} confirmLoading={createPatMut.isPending}>
        <Form form={patForm} layout="vertical" onFinish={(v) => createPatMut.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="scopes" label="范围 (JSON)" help='如: ["read"]'><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
