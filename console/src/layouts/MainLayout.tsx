import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Select, Dropdown, Space, Button } from "antd";
import {
  ApartmentOutlined,
  AppstoreOutlined,
  DatabaseOutlined,
  BuildOutlined,
  UserOutlined,
  ThunderboltOutlined,
  CodeOutlined,
  RobotOutlined,
  SearchOutlined,
  SettingOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { useDataset } from "../hooks/useDataset";
import { useAuth } from "../hooks/useAuth";

const { Sider, Header, Content, Footer } = Layout;

const menuItems = [
  { key: "/graph", icon: <ApartmentOutlined />, label: "本体图谱" },
  { key: "/types", icon: <AppstoreOutlined />, label: "类型定义" },
  { key: "/instances", icon: <DatabaseOutlined />, label: "实例管理" },
  { key: "/search", icon: <SearchOutlined />, label: "高级搜索" },
  { key: "/automodel", icon: <ThunderboltOutlined />, label: "自动建模" },
  { key: "/modeling", icon: <BuildOutlined />, label: "行业建模" },
  { key: "/skills", icon: <CodeOutlined />, label: "Skills 技能" },
  { key: "/llm-config", icon: <RobotOutlined />, label: "LLM 配置" },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { dataset, setDataset, datasets } = useDataset();
  const { user, logout } = useAuth();

  const selectedKey = "/" + (location.pathname.split("/")[1] || "graph");

  const userMenuItems = [
    { key: "settings", icon: <SettingOutlined />, label: "个人设置", onClick: () => navigate("/settings") },
  ];

  if (user?.is_superuser) {
    userMenuItems.push({
      key: "admin",
      icon: <SafetyCertificateOutlined />,
      label: "管理面板",
      onClick: () => navigate("/admin"),
    });
  }

  userMenuItems.push(
    { type: "divider" as const },
    { key: "logout", icon: <LogoutOutlined />, label: "退出登录", onClick: () => logout().then(() => navigate("/login")) },
  );

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={200} theme="dark">
        <div
          style={{
            height: 48,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontWeight: 700,
            fontSize: 16,
            borderBottom: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          OntologyReady
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: "#fff",
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 16,
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          <Select
            value={dataset}
            onChange={setDataset}
            style={{ width: 180 }}
            options={(datasets || [{ value: "default", label: "默认数据集" }]).map((d: { value: string; label: string }) => ({
              value: d.value,
              label: d.label,
            }))}
          />
          <Dropdown menu={{ items: userMenuItems }}>
            <Space style={{ cursor: "pointer" }}>
              <UserOutlined />
              {user?.username || user?.full_name || "用户"}
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: "#fff", borderRadius: 8, minHeight: 520 }}>
          <Outlet />
        </Content>
        <Footer style={{ textAlign: "center", color: "#999" }}>
          OntologyReady ©2026 — 企业级本体管理平台
        </Footer>
      </Layout>
    </Layout>
  );
}
