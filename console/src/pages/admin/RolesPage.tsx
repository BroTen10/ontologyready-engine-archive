import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Button, Space, Modal, Form, Input, message, Popconfirm } from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { fetchRoles, createRole, updateRole, deleteRole } from "../../api/endpoints";

export default function RolesPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Record<string, unknown> | null>(null);
  const [form] = Form.useForm();

  const { data: roles, isLoading } = useQuery({ queryKey: ["admin-roles"], queryFn: fetchRoles });

  const saveMut = useMutation({
    mutationFn: async (v: Record<string, unknown>) => {
      if (editingRole) return updateRole(editingRole.id as string, v);
      return createRole(v);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-roles"] });
      message.success(editingRole ? "角色已更新" : "角色已创建");
      setModalOpen(false); setEditingRole(null); form.resetFields();
    },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "操作失败"),
  });

  const deleteMut = useMutation({
    mutationFn: deleteRole,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin-roles"] }); message.success("角色已删除"); },
  });

  const columns = [
    { title: "名称", dataIndex: "name", key: "name", width: 200 },
    { title: "描述", dataIndex: "description", key: "description", ellipsis: true },
    { title: "权限", dataIndex: "permissions", key: "permissions", ellipsis: true, render: (v: unknown) => JSON.stringify(v) },
    {
      title: "操作", key: "actions", width: 160,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size="small">
          <Button size="small" onClick={() => { setEditingRole(record); form.setFieldsValue(record); setModalOpen(true); }}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => deleteMut.mutate(record.id as string)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h3>角色管理</h3>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ["admin-roles"] })}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingRole(null); form.resetFields(); setModalOpen(true); }}>添加角色</Button>
        </Space>
      </div>
      <Table columns={columns} dataSource={roles as Record<string, unknown>[]} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} />

      <Modal title={editingRole ? "编辑角色" : "添加角色"} open={modalOpen} onCancel={() => { setModalOpen(false); setEditingRole(null); }} onOk={() => form.submit()} confirmLoading={saveMut.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => saveMut.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="permissions" label="权限 (JSON)" help='如: ["read", "write", "admin"]'>
            <Input.TextArea rows={4} placeholder='["read", "write"]' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
