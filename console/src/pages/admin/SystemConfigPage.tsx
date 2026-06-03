import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Button, Space, Modal, Form, Input, message } from "antd";
import { ReloadOutlined, EditOutlined } from "@ant-design/icons";
import { fetchSystemConfig, updateSystemConfig } from "../../api/endpoints";

export default function SystemConfigPage() {
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [editingKey, setEditingKey] = useState("");
  const [form] = Form.useForm();

  const { data: configs, isLoading } = useQuery({
    queryKey: ["system-config"],
    queryFn: fetchSystemConfig,
  });

  const updateMut = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => updateSystemConfig(key, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-config"] });
      message.success("配置已更新");
      setEditOpen(false);
    },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "更新失败"),
  });

  const columns = [
    { title: "配置键", dataIndex: "key", key: "key", width: 250 },
    { title: "值", dataIndex: "value", key: "value", ellipsis: true, render: (v: unknown) => typeof v === "object" ? JSON.stringify(v) : String(v) },
    { title: "描述", dataIndex: "description", key: "description", ellipsis: true },
    {
      title: "操作", key: "actions", width: 100,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Button
          size="small"
          icon={<EditOutlined />}
          onClick={() => {
            setEditingKey(record.key as string);
            form.setFieldsValue({ key: record.key, value: typeof record.value === "object" ? JSON.stringify(record.value) : String(record.value ?? "") });
            setEditOpen(true);
          }}
        >
          编辑
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h3>系统配置管理</h3>
        <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ["system-config"] })}>刷新</Button>
      </div>
      <Table
        columns={columns}
        dataSource={configs as Record<string, unknown>[]}
        rowKey="key"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
      />

      <Modal
        title={`编辑配置: ${editingKey}`}
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={() => {
          form.validateFields().then((v) => {
            let value: unknown = v.value;
            try { value = JSON.parse(v.value); } catch { /* keep as string */ }
            updateMut.mutate({ key: editingKey, value });
          });
        }}
        confirmLoading={updateMut.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="key" label="配置键">
            <Input disabled />
          </Form.Item>
          <Form.Item name="value" label="值" rules={[{ required: true }]}>
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
