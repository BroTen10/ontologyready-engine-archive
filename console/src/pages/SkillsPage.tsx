import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card, Table, Button, Space, Tag, Switch, Modal, Form, Input, Select, message,
  Popconfirm, Descriptions, Upload, Tooltip,
} from "antd";
import {
  PlusOutlined, ExportOutlined, ImportOutlined, CopyOutlined,
  ThunderboltOutlined, ReloadOutlined, EyeOutlined,
} from "@ant-design/icons";
import {
  fetchSkills, toggleSkill, cloneSkill, fetchSkillPresets,
  generateSkills, createSkill, deleteSkill, exportSkill, importSkill,
  type UserProfile,
} from "../api/endpoints";
import { useDataset } from "../hooks/useDataset";

export default function SkillsPage() {
  const queryClient = useQueryClient();
  const { dataset } = useDataset();
  const [createOpen, setCreateOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState<Record<string, unknown> | null>(null);
  const [createForm] = Form.useForm();

  const { data: skills, isLoading } = useQuery({
    queryKey: ["skills"],
    queryFn: fetchSkills,
  });

  const { data: presets } = useQuery({
    queryKey: ["skill-presets"],
    queryFn: fetchSkillPresets,
  });

  const toggleMut = useMutation({
    mutationFn: toggleSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      message.success("技能状态已更新");
    },
  });

  const cloneMut = useMutation({
    mutationFn: cloneSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      message.success("技能已克隆");
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      message.success("技能已删除");
    },
  });

  const createMut = useMutation({
    mutationFn: createSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      message.success("技能已创建");
      setCreateOpen(false);
      createForm.resetFields();
    },
  });

  const generateMut = useMutation({
    mutationFn: generateSkills,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      message.success("技能已从本体生成");
    },
  });

  const handleExport = async (skillId: string) => {
    try {
      const data = await exportSkill(skillId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `skill-${skillId}.json`;
      a.click();
      URL.revokeObjectURL(url);
      message.success("导出成功");
    } catch {
      message.error("导出失败");
    }
  };

  const handleImport = async (file: File) => {
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      await importSkill(data);
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      message.success("导入成功");
    } catch {
      message.error("导入失败，请检查文件格式");
    }
    return false;
  };

  const columns = [
    { title: "名称", dataIndex: "name", key: "name", width: 200 },
    { title: "描述", dataIndex: "description", key: "description", ellipsis: true },
    {
      title: "状态", dataIndex: "status", key: "status", width: 100,
      render: (s: string) => <Tag color={s === "active" ? "green" : "default"}>{s === "active" ? "启用" : "停用"}</Tag>,
    },
    {
      title: "操作", key: "actions", width: 360,
      render: (_: unknown, record: Record<string, unknown>) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button size="small" icon={<EyeOutlined />} onClick={() => { setSelectedSkill(record); setDetailOpen(true); }} />
          </Tooltip>
          <Switch
            size="small"
            checked={record.status === "active"}
            onChange={() => toggleMut.mutate(record.id as string)}
            loading={toggleMut.isPending}
          />
          <Tooltip title="克隆">
            <Button size="small" icon={<CopyOutlined />} onClick={() => cloneMut.mutate(record.id as string)} />
          </Tooltip>
          <Tooltip title="导出">
            <Button size="small" icon={<ExportOutlined />} onClick={() => handleExport(record.id as string)} />
          </Tooltip>
          <Popconfirm title="确定删除此技能？" onConfirm={() => deleteMut.mutate(record.id as string)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>Skills 技能管理</h2>
        <Space>
          <Upload accept=".json" showUploadList={false} beforeUpload={handleImport}>
            <Button icon={<ImportOutlined />}>导入技能</Button>
          </Upload>
          <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ["skills"] })}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={() => generateMut.mutate(dataset)}
            loading={generateMut.isPending}
          >
            从本体生成
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            创建技能
          </Button>
        </Space>
      </div>

      {presets && (presets as unknown[]).length > 0 && (
        <Card title="预设技能模板" size="small" style={{ marginBottom: 16 }}>
          <Space wrap>
            {(presets as Array<{ id: string; name: string; description: string }>).map((p) => (
              <Tag
                key={p.id}
                color="blue"
                style={{ cursor: "pointer", padding: "4px 12px" }}
                onClick={() => {
                  createForm.setFieldsValue({ name: p.name, description: p.description });
                  setCreateOpen(true);
                }}
              >
                {p.name}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={skills as Record<string, unknown>[]}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title="创建技能"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()}
        confirmLoading={createMut.isPending}
      >
        <Form form={createForm} layout="vertical" onFinish={(v) => createMut.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="skill_config" label="技能配置 (JSON)">
            <Input.TextArea rows={5} placeholder='{"type": "rule", "conditions": [], "actions": []}' />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="技能详情"
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={640}
      >
        {selectedSkill && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="名称">{selectedSkill.name as string}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={(selectedSkill.status as string) === "active" ? "green" : "default"}>
                {selectedSkill.status as string}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{selectedSkill.description as string}</Descriptions.Item>
            <Descriptions.Item label="配置" span={2}>
              <pre style={{ maxHeight: 200, overflow: "auto", background: "#f5f5f5", padding: 8, borderRadius: 4 }}>
                {JSON.stringify(selectedSkill.skill_config, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}
