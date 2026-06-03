import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Button, Space, Modal, Form, Input, Switch, message, Popconfirm, Tag, Select } from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { fetchUsers, createUser, updateUser, deleteUser, fetchRoles, assignRole, removeRole, fetchUserRoles } from "../../api/endpoints";

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<Record<string, unknown> | null>(null);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: users, isLoading } = useQuery({ queryKey: ["admin-users"], queryFn: fetchUsers });
  const { data: roles } = useQuery({ queryKey: ["admin-roles"], queryFn: fetchRoles });
  const { data: userRoles, refetch: refetchUserRoles } = useQuery({
    queryKey: ["user-roles", selectedUserId],
    queryFn: () => fetchUserRoles(selectedUserId!),
    enabled: !!selectedUserId,
  });

  const saveMut = useMutation({
    mutationFn: async (v: Record<string, unknown>) => {
      if (editingUser) return updateUser(editingUser.id as string, v);
      return createUser(v);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      message.success(editingUser ? "用户已更新" : "用户已创建");
      setModalOpen(false);
      setEditingUser(null);
      form.resetFields();
    },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "操作失败"),
  });

  const deleteMut = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin-users"] }); message.success("用户已删除"); },
  });

  const assignRoleMut = useMutation({
    mutationFn: ({ roleId }: { roleId: string }) => assignRole(selectedUserId!, roleId),
    onSuccess: () => { refetchUserRoles(); message.success("角色已分配"); },
  });

  const removeRoleMut = useMutation({
    mutationFn: (roleId: string) => removeRole(selectedUserId!, roleId),
    onSuccess: () => { refetchUserRoles(); message.success("角色已移除"); },
  });

  const columns = [
    { title: "用户名", dataIndex: "username", key: "username", width: 150 },
    { title: "邮箱", dataIndex: "email", key: "email", width: 200 },
    { title: "姓名", dataIndex: "full_name", key: "full_name", width: 150 },
    {
      title: "管理员", dataIndex: "is_superuser", key: "is_superuser", width: 100,
      render: (v: boolean) => v ? <Tag color="red">是</Tag> : <Tag>否</Tag>,
    },
    {
      title: "状态", dataIndex: "is_active", key: "is_active", width: 100,
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "正常" : "禁用"}</Tag>,
    },
    {
      title: "操作", key: "actions", width: 280,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size="small">
          <Button size="small" onClick={() => { setSelectedUserId(record.id as string); setRoleModalOpen(true); }}>角色</Button>
          <Button size="small" onClick={() => { setEditingUser(record); form.setFieldsValue(record); setModalOpen(true); }}>编辑</Button>
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
        <h3>用户管理</h3>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ["admin-users"] })}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingUser(null); form.resetFields(); setModalOpen(true); }}>添加用户</Button>
        </Space>
      </div>
      <Table columns={columns} dataSource={users as Record<string, unknown>[]} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} />

      <Modal title={editingUser ? "编辑用户" : "添加用户"} open={modalOpen} onCancel={() => { setModalOpen(false); setEditingUser(null); }} onOk={() => form.submit()} confirmLoading={saveMut.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => saveMut.mutate(v)}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="full_name" label="姓名"><Input /></Form.Item>
          <Form.Item name="password" label={editingUser ? "新密码 (留空不修改)" : "密码"} rules={editingUser ? [] : [{ required: true }]}><Input.Password /></Form.Item>
          <Form.Item name="is_superuser" label="管理员" valuePropName="checked"><Switch /></Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked" initialValue={true}><Switch /></Form.Item>
        </Form>
      </Modal>

      <Modal title="管理用户角色" open={roleModalOpen} onCancel={() => setRoleModalOpen(false)} footer={null} width={500}>
        <div style={{ marginBottom: 16 }}>
          <Tag color="blue">当前角色</Tag>
          <Space wrap style={{ marginTop: 8 }}>
            {(userRoles as Array<{ id: string; name: string }>)?.map((r) => (
              <Tag key={r.id} closable onClose={() => removeRoleMut.mutate(r.id)}>{r.name}</Tag>
            )) || <span style={{ color: "#999" }}>无</span>}
          </Space>
        </div>
        <Select
          style={{ width: "100%" }}
          placeholder="选择要分配的角色"
          onChange={(roleId) => assignRoleMut.mutate({ roleId })}
          options={(roles as Array<{ id: string; name: string }>)?.map((r) => ({ value: r.id, label: r.name })) || []}
        />
      </Modal>
    </div>
  );
}
