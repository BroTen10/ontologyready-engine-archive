import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Card, Form, Input, Button, Space, message, Divider, Table, Modal, Popconfirm, Tag } from "antd";
import { UserOutlined, LockOutlined, KeyOutlined, PlusOutlined, CopyOutlined } from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";
import { changePassword, fetchPats, createPat, deletePat } from "../api/endpoints";

export default function UserSettingsPage() {
  const { user, refresh } = useAuth();
  const [profileForm] = Form.useForm();
  const [pwdForm] = Form.useForm();
  const [patModalOpen, setPatModalOpen] = useState(false);
  const [patForm] = Form.useForm();

  const { data: pats, isLoading: patsLoading } = useQuery({
    queryKey: ["pats"],
    queryFn: fetchPats,
  });

  const pwdMut = useMutation({
    mutationFn: changePassword,
    onSuccess: () => { message.success("密码已修改，请重新登录"); pwdForm.resetFields(); },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "修改失败"),
  });

  const createPatMut = useMutation({
    mutationFn: createPat,
    onSuccess: (data) => {
      message.success("PAT 已创建，请复制保存");
      setPatModalOpen(false);
      patForm.resetFields();
    },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "创建失败"),
  });

  const deletePatMut = useMutation({
    mutationFn: deletePat,
    onSuccess: () => message.success("PAT 已删除"),
  });

  const patColumns = [
    { title: "名称", dataIndex: "name", key: "name" },
    { title: "范围", dataIndex: "scopes", key: "scopes", render: (v: unknown) => JSON.stringify(v) },
    {
      title: "状态", dataIndex: "is_active", key: "is_active",
      render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "启用" : "禁用"}</Tag>,
    },
    { title: "过期", dataIndex: "expires_at", key: "expires_at", render: (v: string) => v || "永不过期" },
    {
      title: "操作", key: "actions",
      render: (_: unknown, record: Record<string, unknown>) => (
        <Popconfirm title="确定删除？" onConfirm={() => deletePatMut.mutate(record.id as string)}>
          <Button size="small" danger>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 640 }}>
      <h2 style={{ marginBottom: 24 }}>个人设置</h2>

      <Card title={<><UserOutlined /> 个人信息</>} style={{ marginBottom: 16 }}>
        <Form form={profileForm} layout="vertical" initialValues={user || {}}>
          <Form.Item label="用户名"><Input value={user?.username} disabled /></Form.Item>
          <Form.Item label="邮箱"><Input value={user?.email} disabled /></Form.Item>
          <Form.Item label="姓名"><Input value={user?.full_name} disabled /></Form.Item>
          <Form.Item label="角色">
            <Tag color={user?.is_superuser ? "red" : "blue"}>
              {user?.is_superuser ? "超级管理员" : "普通用户"}
            </Tag>
          </Form.Item>
        </Form>
      </Card>

      <Card title={<><LockOutlined /> 修改密码</>} style={{ marginBottom: 16 }}>
        <Form form={pwdForm} layout="vertical" onFinish={(v) => pwdMut.mutate(v)}>
          <Form.Item name="old_password" label="当前密码" rules={[{ required: true, message: "请输入当前密码" }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[
            { required: true, message: "请输入新密码" },
            { min: 6, message: "密码至少 6 位" },
          ]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="confirm_password" label="确认新密码" dependencies={["new_password"]} rules={[
            { required: true, message: "请确认新密码" },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue("new_password") === value) return Promise.resolve();
                return Promise.reject(new Error("两次输入的密码不一致"));
              },
            }),
          ]}>
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={pwdMut.isPending}>修改密码</Button>
        </Form>
      </Card>

      <Card title={<><KeyOutlined /> 个人访问令牌 (PAT)</>}>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { patForm.resetFields(); setPatModalOpen(true); }}>
            创建令牌
          </Button>
        </Space>
        <Table
          columns={patColumns}
          dataSource={pats as Record<string, unknown>[]}
          rowKey="id"
          loading={patsLoading}
          pagination={false}
          size="small"
        />
      </Card>

      <Modal title="创建访问令牌" open={patModalOpen} onCancel={() => setPatModalOpen(false)} onOk={() => patForm.submit()} confirmLoading={createPatMut.isPending}>
        <Form form={patForm} layout="vertical" onFinish={(v) => createPatMut.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="scopes" label="范围 (JSON)" help='如: ["read"]'><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
