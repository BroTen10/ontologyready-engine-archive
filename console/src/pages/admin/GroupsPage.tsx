import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm, Tag } from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { fetchGroups, createGroup, updateGroup, deleteGroup, fetchGroupMembers, addGroupMember, removeGroupMember, fetchUsers } from "../../api/endpoints";

export default function GroupsPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<Record<string, unknown> | null>(null);
  const [memberModalOpen, setMemberModalOpen] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: groups, isLoading } = useQuery({ queryKey: ["admin-groups"], queryFn: fetchGroups });
  const { data: users } = useQuery({ queryKey: ["admin-users"], queryFn: fetchUsers });
  const { data: members, refetch: refetchMembers } = useQuery({
    queryKey: ["group-members", selectedGroupId],
    queryFn: () => fetchGroupMembers(selectedGroupId!),
    enabled: !!selectedGroupId,
  });

  const saveMut = useMutation({
    mutationFn: async (v: Record<string, unknown>) => {
      if (editingGroup) return updateGroup(editingGroup.id as string, v);
      return createGroup(v);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-groups"] });
      message.success(editingGroup ? "用户组已更新" : "用户组已创建");
      setModalOpen(false); setEditingGroup(null); form.resetFields();
    },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "操作失败"),
  });

  const deleteMut = useMutation({
    mutationFn: deleteGroup,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin-groups"] }); message.success("用户组已删除"); },
  });

  const addMemberMut = useMutation({
    mutationFn: (userId: string) => addGroupMember(selectedGroupId!, userId),
    onSuccess: () => { refetchMembers(); message.success("成员已添加"); },
  });

  const removeMemberMut = useMutation({
    mutationFn: (userId: string) => removeGroupMember(selectedGroupId!, userId),
    onSuccess: () => { refetchMembers(); message.success("成员已移除"); },
  });

  const columns = [
    { title: "名称", dataIndex: "name", key: "name", width: 200 },
    { title: "描述", dataIndex: "description", key: "description", ellipsis: true },
    {
      title: "操作", key: "actions", width: 240,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size="small">
          <Button size="small" onClick={() => { setSelectedGroupId(record.id as string); setMemberModalOpen(true); }}>成员</Button>
          <Button size="small" onClick={() => { setEditingGroup(record); form.setFieldsValue(record); setModalOpen(true); }}>编辑</Button>
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
        <h3>用户组管理</h3>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ["admin-groups"] })}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingGroup(null); form.resetFields(); setModalOpen(true); }}>添加用户组</Button>
        </Space>
      </div>
      <Table columns={columns} dataSource={groups as Record<string, unknown>[]} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} />

      <Modal title={editingGroup ? "编辑用户组" : "添加用户组"} open={modalOpen} onCancel={() => { setModalOpen(false); setEditingGroup(null); }} onOk={() => form.submit()} confirmLoading={saveMut.isPending}>
        <Form form={form} layout="vertical" onFinish={(v) => saveMut.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="管理组成员" open={memberModalOpen} onCancel={() => setMemberModalOpen(false)} footer={null} width={500}>
        <div style={{ marginBottom: 16 }}>
          <Tag color="blue">当前成员</Tag>
          <Space wrap style={{ marginTop: 8 }}>
            {(members as Array<{ id: string; username: string }>)?.map((m) => (
              <Tag key={m.id} closable onClose={() => removeMemberMut.mutate(m.id)}>{m.username}</Tag>
            )) || <span style={{ color: "#999" }}>无</span>}
          </Space>
        </div>
        <Select
          style={{ width: "100%" }}
          placeholder="选择要添加的用户"
          onChange={(userId) => addMemberMut.mutate(userId)}
          options={(users as Array<{ id: string; username: string }>)?.map((u) => ({ value: u.id, label: u.username })) || []}
        />
      </Modal>
    </div>
  );
}
