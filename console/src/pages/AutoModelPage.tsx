import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Steps, Card, Form, Input, Select, Button, Space, message, Spin, Alert,
  Table, Tag, Checkbox, Descriptions, Result,
} from "antd";
import {
  DatabaseOutlined, TableOutlined, ThunderboltOutlined,
  CheckCircleOutlined, PlayCircleOutlined,
} from "@ant-design/icons";
import { testDbConnection, fetchDatabases, fetchSchemas, fetchTables, describeTable, quickAnalyze, syncModel, } from "../api/endpoints";

type DbConnection = { db_type: string; host: string; port: number; user: string; password: string; database: string };

export default function AutoModelPage() {
  const [step, setStep] = useState(0);
  const [connection, setConnection] = useState<DbConnection | null>(null);
  const [connected, setConnected] = useState(false);
  const [databases, setDatabases] = useState<string[]>([]);
  const [selectedDb, setSelectedDb] = useState("");
  const [schemas, setSchemas] = useState<string[]>([]);
  const [selectedSchema, setSelectedSchema] = useState("");
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [tableInfo, setTableInfo] = useState<Record<string, unknown>>({});
  const [analysisResult, setAnalysisResult] = useState<Record<string, unknown> | null>(null);
  const [syncDone, setSyncDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const testConnMutation = useMutation({
    mutationFn: testDbConnection,
    onSuccess: () => {
      setConnected(true);
      message.success("数据库连接成功");
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "连接失败";
      message.error(msg);
    },
  });

  const handleTestConnection = async (values: DbConnection) => {
    setConnection(values);
    testConnMutation.mutate(values);
  };

  const handleNext = async () => {
    setLoading(true);
    try {
      if (step === 0 && connected) {
        const dbs = await fetchDatabases();
        setDatabases(dbs as string[]);
      } else if (step === 1 && selectedDb) {
        const schemasList = await fetchSchemas();
        setSchemas(schemasList as string[]);
      } else if (step === 2 && selectedSchema) {
        const tableList = await fetchTables(selectedSchema);
        setTables(tableList as string[]);
      } else if (step === 3 && selectedTables.length > 0) {
        const info: Record<string, unknown> = {};
        for (const t of selectedTables) {
          info[t] = await describeTable(selectedSchema, t);
        }
        setTableInfo(info);
        const result = await quickAnalyze({
          db_type: connection?.db_type,
          tables: selectedTables.map((t) => ({ schema: selectedSchema, table: t })),
        });
        setAnalysisResult(result);
      }
      setStep((s) => s + 1);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "操作失败";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    if (!analysisResult) return;
    setLoading(true);
    try {
      await syncModel({ analysis_result: analysisResult });
      setSyncDone(true);
      setStep((s) => s + 1);
      message.success("本体模型已同步到知识图谱");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message || "同步失败";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { title: "连接数据库", icon: <DatabaseOutlined /> },
    { title: "选择数据库", icon: <DatabaseOutlined /> },
    { title: "选择 Schema", icon: <TableOutlined /> },
    { title: "选择表", icon: <TableOutlined /> },
    { title: "预览分析", icon: <ThunderboltOutlined /> },
    { title: "完成", icon: <CheckCircleOutlined /> },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>自动建模向导</h2>
      <Steps current={step} items={steps} style={{ marginBottom: 32 }} />

      <Card>
        {step === 0 && (
          <div>
            <h3>连接外部数据库</h3>
            <Form<DbConnection>
              layout="vertical"
              onFinish={handleTestConnection}
              style={{ maxWidth: 500, marginTop: 16 }}
            >
              <Form.Item name="db_type" label="数据库类型" rules={[{ required: true }]}>
                <Select options={[
                  { value: "postgresql", label: "PostgreSQL" },
                  { value: "mysql", label: "MySQL" },
                ]} />
              </Form.Item>
              <Form.Item name="host" label="主机" rules={[{ required: true }]}>
                <Input placeholder="localhost" />
              </Form.Item>
              <Form.Item name="port" label="端口" rules={[{ required: true }]}>
                <Input type="number" placeholder="5432" />
              </Form.Item>
              <Form.Item name="user" label="用户名" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Form.Item name="password" label="密码" rules={[{ required: true }]}>
                <Input.Password />
              </Form.Item>
              <Form.Item name="database" label="数据库名" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={testConnMutation.isPending} icon={<PlayCircleOutlined />}>
                  测试连接
                </Button>
                {connected && (
                  <Button type="primary" onClick={handleNext} loading={loading}>
                    下一步
                  </Button>
                )}
              </Space>
            </Form>
          </div>
        )}

        {step === 1 && (
          <div>
            <h3>选择目标数据库</h3>
            <Spin spinning={loading}>
              <div style={{ marginTop: 16 }}>
                {databases.map((db) => (
                  <Card
                    key={db}
                    size="small"
                    style={{
                      marginBottom: 8,
                      cursor: "pointer",
                      borderColor: selectedDb === db ? "#1890ff" : undefined,
                    }}
                    onClick={() => setSelectedDb(db)}
                  >
                    <DatabaseOutlined style={{ marginRight: 8 }} />
                    {db}
                    {selectedDb === db && <Tag color="blue" style={{ float: "right" }}>已选择</Tag>}
                  </Card>
                ))}
              </div>
              <Space style={{ marginTop: 16 }}>
                <Button onClick={() => setStep(0)}>上一步</Button>
                <Button type="primary" disabled={!selectedDb} onClick={handleNext} loading={loading}>
                  下一步
                </Button>
              </Space>
            </Spin>
          </div>
        )}

        {step === 2 && (
          <div>
            <h3>选择 Schema</h3>
            <Spin spinning={loading}>
              <div style={{ marginTop: 16 }}>
                {schemas.map((s) => (
                  <Card
                    key={s}
                    size="small"
                    style={{
                      marginBottom: 8,
                      cursor: "pointer",
                      borderColor: selectedSchema === s ? "#1890ff" : undefined,
                    }}
                    onClick={() => setSelectedSchema(s)}
                  >
                    <TableOutlined style={{ marginRight: 8 }} />
                    {s}
                    {selectedSchema === s && <Tag color="blue" style={{ float: "right" }}>已选择</Tag>}
                  </Card>
                ))}
              </div>
              <Space style={{ marginTop: 16 }}>
                <Button onClick={() => setStep(1)}>上一步</Button>
                <Button type="primary" disabled={!selectedSchema} onClick={handleNext} loading={loading}>
                  下一步
                </Button>
              </Space>
            </Spin>
          </div>
        )}

        {step === 3 && (
          <div>
            <h3>选择要分析的表</h3>
            <Spin spinning={loading}>
              <div style={{ marginTop: 16 }}>
                <Checkbox.Group value={selectedTables} onChange={(v) => setSelectedTables(v as string[])} style={{ width: "100%" }}>
                  {tables.map((t) => (
                    <Card key={t} size="small" style={{ marginBottom: 8 }}>
                      <Checkbox value={t}>
                        <TableOutlined style={{ marginLeft: 8, marginRight: 8 }} />
                        {t}
                      </Checkbox>
                    </Card>
                  ))}
                </Checkbox.Group>
              </div>
              <Space style={{ marginTop: 16 }}>
                <Button onClick={() => setStep(2)}>上一步</Button>
                <Button type="primary" disabled={selectedTables.length === 0} onClick={handleNext} loading={loading}>
                  分析选中的表
                </Button>
              </Space>
            </Spin>
          </div>
        )}

        {step === 4 && !syncDone && (
          <div>
            <h3>AI 分析预览</h3>
            <Spin spinning={loading}>
              {analysisResult ? (
                <div style={{ marginTop: 16 }}>
                  <Alert
                    type="info"
                    message="以下是根据数据库表结构自动生成的本体模型预览"
                    style={{ marginBottom: 16 }}
                  />
                  <Descriptions bordered column={2} size="small">
                    <Descriptions.Item label="识别到的对象类型">
                      {(analysisResult as Record<string, unknown>)?.objectTypes
                        ? (analysisResult as Record<string, unknown>).objectTypes as number
                        : 0}
                    </Descriptions.Item>
                    <Descriptions.Item label="识别到的关系类型">
                      {(analysisResult as Record<string, unknown>)?.linkTypes
                        ? (analysisResult as Record<string, unknown>).linkTypes as number
                        : 0}
                    </Descriptions.Item>
                  </Descriptions>
                  <pre style={{
                    marginTop: 16, padding: 16, background: "#f5f5f5", borderRadius: 8,
                    maxHeight: 300, overflow: "auto",
                  }}>
                    {JSON.stringify(analysisResult, null, 2)}
                  </pre>
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: 40 }}>
                  <Spin />
                  <p style={{ marginTop: 16, color: "#999" }}>正在分析...</p>
                </div>
              )}
              <Space style={{ marginTop: 16 }}>
                <Button onClick={() => setStep(3)}>上一步</Button>
                <Button type="primary" onClick={handleSync} loading={loading} icon={<ThunderboltOutlined />}>
                  应用并同步到知识图谱
                </Button>
              </Space>
            </Spin>
          </div>
        )}

        {step === 5 && syncDone && (
          <Result
            status="success"
            title="自动建模完成"
            subTitle="本体模型已成功同步到知识图谱，您现在可以在图谱页面查看新生成的本体结构。"
            extra={[
              <Button type="primary" key="graph" onClick={() => window.location.hash = "#/graph"}>
                查看图谱
              </Button>,
              <Button key="types" onClick={() => window.location.hash = "#/types"}>
                查看类型定义
              </Button>,
            ]}
          />
        )}
      </Card>
    </div>
  );
}
