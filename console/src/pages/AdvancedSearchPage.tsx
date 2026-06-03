import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, Form, Input, Select, Button, Space, Table, Tag, DatePicker, Row, Col } from "antd";
import { SearchOutlined, ReloadOutlined, FilterOutlined } from "@ant-design/icons";
import { fetchTypes, searchObjects, fetchObjects, type ObjectInstance } from "../api/endpoints";
import { useDataset } from "../hooks/useDataset";

export default function AdvancedSearchPage() {
  const { dataset } = useDataset();
  const [searchResults, setSearchResults] = useState<ObjectInstance[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const { data: types } = useQuery({
    queryKey: ["types-list"],
    queryFn: () => fetchTypes(),
  });

  const handleSearch = useCallback(async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      const q = values.q as string;
      if (q) {
        const results = await searchObjects(q);
        setSearchResults(results);
      } else {
        const params: Record<string, unknown> = { dataset, page: 1, size: 50 };
        if (values.type) params.type = values.type;
        const result = await fetchObjects(params);
        setSearchResults(result.data);
      }
    } catch {
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  }, [dataset]);

  const columns = [
    { title: "ID", dataIndex: "id", key: "id", width: 280, ellipsis: true },
    { title: "显示名称", dataIndex: "display_name", key: "display_name", width: 200 },
    {
      title: "类型", dataIndex: "object_type", key: "object_type", width: 150,
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    { title: "外部 ID", dataIndex: "external_id", key: "external_id", width: 180, ellipsis: true },
    {
      title: "属性预览", dataIndex: "properties", key: "properties", ellipsis: true,
      render: (v: Record<string, unknown>) => {
        if (!v) return "—";
        const keys = Object.keys(v).slice(0, 3);
        return keys.map((k) => `${k}: ${v[k]}`).join(" | ") || "—";
      },
    },
    { title: "创建时间", dataIndex: "created_at", key: "created_at", width: 180 },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>高级搜索</h2>

      <Card style={{ marginBottom: 24 }}>
        <Form form={form} onFinish={handleSearch} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="q" label="全文搜索">
                <Input prefix={<SearchOutlined />} placeholder="输入关键词搜索对象属性..." />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="type" label="类型筛选">
                <Select
                  allowClear
                  placeholder="选择对象类型"
                  options={(types as Array<{ api_name: string; display_name: string }>)?.map((t) => ({
                    value: t.api_name,
                    label: t.display_name || t.api_name,
                  })) || []}
                />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item name="dateRange" label="创建时间">
                <DatePicker.RangePicker style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col span={6} style={{ display: "flex", alignItems: "flex-end", paddingBottom: 24 }}>
              <Space>
                <Button type="primary" htmlType="submit" icon={<FilterOutlined />} loading={loading}>
                  搜索
                </Button>
                <Button icon={<ReloadOutlined />} onClick={() => { form.resetFields(); setSearchResults(null); }}>
                  重置
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>
      </Card>

      {searchResults !== null && (
        <Card title={`搜索结果 (${searchResults.length})`}>
          <Table
            columns={columns}
            dataSource={searchResults}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
            size="small"
          />
        </Card>
      )}
    </div>
  );
}
