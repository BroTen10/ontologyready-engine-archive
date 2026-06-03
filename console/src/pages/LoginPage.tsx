import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Form, Input, Button, Card, Typography, Alert, Space } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: string })?.from || "/graph";

  if (isAuthenticated) {
    navigate(from, { replace: true });
    return null;
  }

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true);
    setError(null);
    try {
      await login(values.username, values.password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ||
        "登录失败，请检查用户名和密码";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      <Card style={{ width: 400, boxShadow: "0 8px 32px rgba(0,0,0,0.15)" }}>
        <Space direction="vertical" size="large" style={{ width: "100%", textAlign: "center" }}>
          <div>
            <Typography.Title level={3} style={{ marginBottom: 4 }}>
              OntologyReady
            </Typography.Title>
            <Typography.Text type="secondary">企业级本体管理平台</Typography.Text>
          </div>
        </Space>

        {error && (
          <Alert message={error} type="error" showIcon style={{ marginTop: 24 }} />
        )}

        <Form
          name="login"
          onFinish={handleSubmit}
          layout="vertical"
          style={{ marginTop: 24 }}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" autoFocus />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
