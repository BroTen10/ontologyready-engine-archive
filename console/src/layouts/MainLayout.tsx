import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Select, Dropdown, Space } from "antd";
import {
  ApartmentOutlined,
  AppstoreOutlined,
  DatabaseOutlined,
  BuildOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useDataset } from "../hooks/useDataset";

const { Sider, Header, Content, Footer } = Layout;

const menuItems = [
  { key: "/graph", icon: <ApartmentOutlined />, label: "本体图谱" },
  { key: "/types", icon: <AppstoreOutlined />, label: "类型定义" },
  { key: "/instances", icon: <DatabaseOutlined />, label: "实例管理" },
  { key: "/modeling", icon: <BuildOutlined />, label: "行业建模" },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { dataset, setDataset } = useDataset();

  const selectedKey = "/" + (location.pathname.split("/")[1] || "graph");

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
            style={{ width: 160 }}
            options={[
              { value: "default", label: "默认数据集" },
            ]}
          />
          <Dropdown
            menu={{
              items: [{ key: "admin", label: "管理员" }],
            }}
          >
            <Space style={{ cursor: "pointer" }}>
              <UserOutlined />
              admin
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: "#fff", borderRadius: 8 }}>
          <Outlet />
        </Content>
        <Footer style={{ textAlign: "center", color: "#999" }}>
          OntologyReady ©2026 — 企业级本体管理平台
        </Footer>
      </Layout>
    </Layout>
  );
}
