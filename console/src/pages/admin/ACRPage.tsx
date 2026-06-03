import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Button, Space, Modal, Form, Input, InputNumber, Select, Switch, message, Popconfirm, Tag } from "antd";
import { PlusOutlined, ReloadOutlined, PlayCircleOutlined } from "@ant-design/icons";
import { fetchAcrRules, createAcrRule, deleteAcrRule, fetchAcrGroups, createAcrGroup, fetchAcrBindings, createAcrBinding, evaluateAccess } from "../../api/endpoints";

export default function ACRPage() {
  const queryClient = useQueryClient();
  const [ruleOpen, setRuleOpen] = useState(false);
  const [groupOpen, setGroupOpen] = useState(false);
  const [bindingOpen, setBindingOpen] = useState(false);
  const [evalResult, setEvalResult] = useState<string | null>(null);
  const [evalForm] = Form.useForm();
  const [ruleForm] = Form.useForm();
  const [groupForm] = Form.useForm();
  const [bindingForm] = Form.useForm();

  const { data: rules, isLoading: rulesLoading } = useQuery({ queryKey: ["acr-rules"], queryFn: fetchAcrRules });
  const { data: groups, isLoading: groupsLoading } = useQuery({ queryKey: ["acr-groups"], queryFn: fetchAcrGroups });
  const { data: bindings } = useQuery({ queryKey: ["acr-bindings"], queryFn: () => fetchAcrBindings() });

  const createRuleMut = useMutation({
    mutationFn: createAcrRule,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["acr-rules"] }); message.success("规则已创建"); setRuleOpen(false); ruleForm.resetFields(); },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "创建失败"),
  });

  const deleteRuleMut = useMutation({
    mutationFn: deleteAcrRule,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["acr-rules"] }); message.success("规则已删除"); },
  });

  const createGroupMut = useMutation({
    mutationFn: createAcrGroup,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["acr-groups"] }); message.success("规则组已创建"); setGroupOpen(false); groupForm.resetFields(); },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "创建失败"),
  });

  const createBindingMut = useMutation({
    mutationFn: createAcrBinding,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["acr-bindings"] }); message.success("绑定已创建"); setBindingOpen(false); bindingForm.resetFields(); },
    onError: (e: unknown) => message.error((e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "创建失败"),
  });

  const handleEvaluate = async (v: Record<string, unknown>) => {
    try {
      const result = await evaluateAccess(v);
      setEvalResult(JSON.stringify(result, null, 2));
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "评估失败";
      message.error(msg);
    }
  };

  const ruleColumns = [
    { title: "名称", dataIndex: "rule_name", key: "rule_name", width: 180 },
    { title: "条件", dataIndex: "conditions", key: "conditions", ellipsis: true, render: (v: unknown) => JSON.stringify(v) },
    { title: "优先级", dataIndex: "priority", key: "priority", width: 80 },
    {
      title: "操作", key: "actions", width: 80,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Popconfirm title="确定删除？" onConfirm={() => deleteRuleMut.mutate(record.id as number)}>
          <Button size="small" danger>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  const groupColumns = [
    { title: "名称", dataIndex: "group_name", key: "group_name", width: 200 },
    { title: "规则", dataIndex: "rules", key: "rules", ellipsis: true, render: (v: unknown) => JSON.stringify(v) },
  ];

  const bindingColumns = [
    { title: "用户", dataIndex: "user_id", key: "user_id", width: 200 },
    { title: "规则组", dataIndex: "group_id", key: "group_id", width: 200 },
    { title: "目标类型", dataIndex: "target_type", key: "target_type", width: 150 },
    { title: "目标 ID", dataIndex: "target_id", key: "target_id", ellipsis: true },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h3>访问控制规则 (ACR)</h3>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => {
            queryClient.invalidateQueries({ queryKey: ["acr-rules"] });
            queryClient.invalidateQueries({ queryKey: ["acr-groups"] });
            queryClient.invalidateQueries({ queryKey: ["acr-bindings"] });
          }}>刷新</Button>
          <Button icon={<PlusOutlined />} onClick={() => setRuleOpen(true)}>添加规则</Button>
          <Button icon={<PlusOutlined />} onClick={() => setGroupOpen(true)}>添加规则组</Button>
          <Button icon={<PlusOutlined />} onClick={() => setBindingOpen(true)}>添加绑定</Button>
        </Space>
      </div>

      <h4 style={{ marginTop: 16 }}>ACR 规则</h4>
      <Table columns={ruleColumns} dataSource={rules as Record<string, unknown>[]} rowKey="id" loading={rulesLoading} pagination={false} size="small" style={{ marginBottom: 24 }} />

      <h4>规则组</h4>
      <Table columns={groupColumns} dataSource={groups as Record<string, unknown>[]} rowKey="id" loading={groupsLoading} pagination={false} size="small" style={{ marginBottom: 24 }} />

      <h4>绑定关系</h4>
      <Table columns={bindingColumns} dataSource={bindings as Record<string, unknown>[]} rowKey="id" pagination={false} size="small" style={{ marginBottom: 24 }} />

      <h4>权限评估测试</h4>
      <Form form={evalForm} layout="inline" onFinish={handleEvaluate} style={{ marginBottom: 16 }}>
        <Form.Item name="user_id" label="用户"><Input placeholder="用户ID" /></Form.Item>
        <Form.Item name="object_id" label="对象"><Input placeholder="对象ID" /></Form.Item>
        <Form.Item name="action" label="操作"><Input placeholder="read/write/delete" /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />}>评估</Button></Form.Item>
      </Form>
      {evalResult && <pre style={{ background: "#f5f5f5", padding: 16, borderRadius: 8, maxHeight: 200, overflow: "auto" }}>{evalResult}</pre>}

      <Modal title="添加规则" open={ruleOpen} onCancel={() => setRuleOpen(false)} onOk={() => ruleForm.submit()}>
        <Form form={ruleForm} layout="vertical" onFinish={(v) => createRuleMut.mutate(v)}>
          <Form.Item name="rule_name" label="规则名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="conditions" label="条件 (JSON)" rules={[{ required: true }]} help='如: {"field": "dataset_id", "operator": "eq", "value": "default"}'><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="permissions" label="权限 (JSON)" rules={[{ required: true }]} help='如: ["read", "write"]'><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={0}><InputNumber min={0} max={100} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="添加规则组" open={groupOpen} onCancel={() => setGroupOpen(false)} onOk={() => groupForm.submit()}>
        <Form form={groupForm} layout="vertical" onFinish={(v) => createGroupMut.mutate(v)}>
          <Form.Item name="group_name" label="组名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="rules" label="规则 ID 列表 (JSON)" help='如: [1, 2, 3]'><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="添加绑定" open={bindingOpen} onCancel={() => setBindingOpen(false)} onOk={() => bindingForm.submit()}>
        <Form form={bindingForm} layout="vertical" onFinish={(v) => createBindingMut.mutate(v)}>
          <Form.Item name="user_id" label="用户 ID" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="group_id" label="规则组 ID" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="target_type" label="目标类型"><Input /></Form.Item>
          <Form.Item name="target_id" label="目标 ID"><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
