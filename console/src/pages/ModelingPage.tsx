import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Steps,
  Card,
  Button,
  Tag,
  Result,
  Spin,
  Checkbox,
  List,
  message,
  Descriptions,
  Space,
  Alert,
} from "antd";
import {
  CheckCircleOutlined,
  LoadingOutlined,
  ExperimentOutlined,
  ImportOutlined,
} from "@ant-design/icons";
import api from "../api/client";

interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  tags: string[];
  stats: { objectTypes: number; linkTypes: number; actionTypes: number };
}

interface TemplateDetail extends TemplateInfo {
  objectTypes: Array<{ api_name: string; display_name: string; description: string }>;
  linkTypes: Array<{ api_name: string; display_name: string; description: string }>;
  actionTypes: Array<{ api_name: string; display_name: string; description: string }>;
}

export default function ModelingPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [checkedTypes, setCheckedTypes] = useState<Set<string>>(new Set());

  const { data: templates, isLoading: tplLoading } = useQuery({
    queryKey: ["templates"],
    queryFn: () => api.get<TemplateInfo[]>("/templates").then((r) => r.data),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["template-detail", selected],
    queryFn: () => api.get<TemplateDetail>(`/templates/${selected}`).then((r) => r.data),
    enabled: !!selected && step >= 2,
  });

  const applyMut = useMutation({
    mutationFn: (id: string) => api.post(`/templates/${id}/apply`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["types"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      message.success("模板导入成功！");
      setStep(3);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.error?.message || err.response?.data?.message || "导入失败";
      message.warning(msg);
    },
  });

  const goToStep2 = useCallback(() => {
    if (!selected) return;
    setStep(1);
  }, [selected]);

  const goToStep3 = useCallback(() => {
    if (!detail) return;
    const allIds = new Set<string>();
    (detail.objectTypes || []).forEach((t) => allIds.add(`object:${t.api_name}`));
    (detail.linkTypes || []).forEach((t) => allIds.add(`link:${t.api_name}`));
    (detail.actionTypes || []).forEach((t) => allIds.add(`action:${t.api_name}`));
    setCheckedTypes(allIds);
    setStep(2);
  }, [detail]);

  const toggleType = (key: string) => {
    const next = new Set(checkedTypes);
    if (next.has(key)) next.delete(key); else next.add(key);
    setCheckedTypes(next);
  };

  const selectedTemplate = (templates || []).find((t) => t.id === selected);

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>行业建模</h2>
      <Steps
        current={step}
        style={{ marginBottom: 32 }}
        items={[
          { title: "选择模板" },
          { title: "LLM 映射分析" },
          { title: "预览与调整" },
          { title: "执行导入" },
        ]}
      />

      {/* Step 0: 选择模板 */}
      {step === 0 && (
        <>
          {tplLoading ? (
            <Spin size="large" style={{ display: "block", margin: "60px auto" }} />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
              {(templates || []).map((t) => (
                <Card
                  key={t.id}
                  title={t.name}
                  hoverable
                  style={{ border: selected === t.id ? "2px solid #1890ff" : undefined }}
                  onClick={() => setSelected(t.id)}
                  actions={[
                    <Button
                      key="select"
                      type={selected === t.id ? "primary" : "default"}
                      onClick={(e) => { e.stopPropagation(); setSelected(t.id); }}
                      icon={selected === t.id ? <CheckCircleOutlined /> : undefined}
                    >
                      {selected === t.id ? "已选择" : "选择模板"}
                    </Button>,
                  ]}
                >
                  <p>{t.description}</p>
                  <div style={{ marginTop: 8 }}>
                    {(t.tags || []).map((tag) => <Tag key={tag}>{tag}</Tag>)}
                  </div>
                  <div style={{ marginTop: 12, display: "flex", gap: 16 }}>
                    <span>对象类型: <b>{t.stats.objectTypes}</b></span>
                    <span>关系类型: <b>{t.stats.linkTypes}</b></span>
                    <span>动作类型: <b>{t.stats.actionTypes}</b></span>
                  </div>
                </Card>
              ))}
            </div>
          )}
          <div style={{ marginTop: 24 }}>
            <Button type="primary" size="large" disabled={!selected} onClick={goToStep2}>
              下一步：LLM 映射分析
            </Button>
          </div>
        </>
      )}

      {/* Step 1: LLM 映射分析（占位） */}
      {step === 1 && (
        <>
          <Result
            icon={<ExperimentOutlined style={{ fontSize: 48, color: "#722ed1" }} />}
            title="LLM 映射分析"
            subTitle="此功能将在 Phase 2 中接入大语言模型（OpenAI / 通义千问），自动完成数据库 Schema 到本体定义的智能映射分析。"
          />
          {selectedTemplate && (
            <Card size="small" style={{ maxWidth: 480, margin: "0 auto 24px" }}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="已选模板">{selectedTemplate.name}</Descriptions.Item>
                <Descriptions.Item label="对象类型">{selectedTemplate.stats.objectTypes} 个</Descriptions.Item>
                <Descriptions.Item label="关系类型">{selectedTemplate.stats.linkTypes} 个</Descriptions.Item>
                <Descriptions.Item label="动作类型">{selectedTemplate.stats.actionTypes} 个</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
          <div style={{ textAlign: "center" }}>
            <Space>
              <Button onClick={() => setStep(0)}>返回模板选择</Button>
              <Button type="primary" onClick={goToStep3}>
                跳过分析，直接预览
              </Button>
            </Space>
          </div>
        </>
      )}

      {/* Step 2: 预览与调整 */}
      {step === 2 && (
        <>
          {detailLoading ? (
            <Spin size="large" style={{ display: "block", margin: "60px auto" }} />
          ) : detail ? (
            <div style={{ display: "grid", gap: 24 }}>
              {(detail.objectTypes || []).length > 0 && (
                <Card title={`对象类型 (${detail.objectTypes.length})`} size="small">
                  <List
                    size="small"
                    dataSource={detail.objectTypes}
                    renderItem={(item) => {
                      const key = `object:${item.api_name}`;
                      return (
                        <List.Item
                          actions={[
                            <Checkbox
                              key="check"
                              checked={checkedTypes.has(key)}
                              onChange={() => toggleType(key)}
                            />,
                          ]}
                        >
                          <List.Item.Meta
                            avatar={<Tag color="blue">OBJECT</Tag>}
                            title={item.display_name}
                            description={`${item.api_name} — ${item.description}`}
                          />
                        </List.Item>
                      );
                    }}
                  />
                </Card>
              )}
              {(detail.linkTypes || []).length > 0 && (
                <Card title={`关系类型 (${detail.linkTypes.length})`} size="small">
                  <List
                    size="small"
                    dataSource={detail.linkTypes}
                    renderItem={(item) => {
                      const key = `link:${item.api_name}`;
                      return (
                        <List.Item
                          actions={[
                            <Checkbox
                              key="check"
                              checked={checkedTypes.has(key)}
                              onChange={() => toggleType(key)}
                            />,
                          ]}
                        >
                          <List.Item.Meta
                            avatar={<Tag color="orange">LINK</Tag>}
                            title={item.display_name}
                            description={`${item.api_name} — ${item.description}`}
                          />
                        </List.Item>
                      );
                    }}
                  />
                </Card>
              )}
              {(detail.actionTypes || []).length > 0 && (
                <Card title={`动作类型 (${detail.actionTypes.length})`} size="small">
                  <List
                    size="small"
                    dataSource={detail.actionTypes}
                    renderItem={(item) => {
                      const key = `action:${item.api_name}`;
                      return (
                        <List.Item
                          actions={[
                            <Checkbox
                              key="check"
                              checked={checkedTypes.has(key)}
                              onChange={() => toggleType(key)}
                            />,
                          ]}
                        >
                          <List.Item.Meta
                            avatar={<Tag color="green">ACTION</Tag>}
                            title={item.display_name}
                            description={`${item.api_name} — ${item.description}`}
                          />
                        </List.Item>
                      );
                    }}
                  />
                </Card>
              )}
              <Alert
                type="info"
                message={`已选择 ${checkedTypes.size} 个类型定义，取消勾选的不会导入。`}
                showIcon
              />
              <Space>
                <Button onClick={() => setStep(1)}>返回上一步</Button>
                <Button
                  type="primary"
                  icon={<ImportOutlined />}
                  onClick={() => { if (selected) applyMut.mutate(selected); }}
                  loading={applyMut.isPending}
                >
                  执行导入
                </Button>
              </Space>
            </div>
          ) : (
            <Result status="warning" title="无法加载模板详情" extra={
              <Button onClick={() => setStep(0)}>返回模板选择</Button>
            } />
          )}
        </>
      )}

      {/* Step 3: 导入完成 */}
      {step === 3 && (
        <Result
          status="success"
          icon={<CheckCircleOutlined style={{ color: "#52c41a" }} />}
          title="模板导入完成"
          subTitle={`已成功导入 ${checkedTypes.size} 个类型定义。`}
          extra={[
            <Button key="types" type="primary" onClick={() => navigate("/types")}>
              查看类型定义
            </Button>,
            <Button key="again" onClick={() => { setStep(0); setSelected(null); setCheckedTypes(new Set()); }}>
              导入另一个模板
            </Button>,
          ]}
        />
      )}
    </div>
  );
}
