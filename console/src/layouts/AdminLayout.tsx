import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  UserOutlined, TeamOutlined, UsergroupAddOutlined,
  SafetyCertificateOutlined, SettingOutlined, KeyOutlined,
} from "@ant-design/icons";

const { Sider, Content } = Layout;

const menuItems = [
  { key: "/admin/users", icon: <UserOutlined />, label: "用户管理" },
  { key: "/admin/roles", icon: <TeamOutlined />, label: "角色管理" },
  { key: "/admin/groups", icon: <UsergroupAddOutlined />, label: "用户组管理" },
  { key: "/admin/acr", icon: <SafetyCertificateOutlined />, label: "访问控制" },
  { key: "/admin/apikeys", icon: <KeyOutlined />, label: "API 密钥" },
  { key: "/admin/config", icon: <SettingOutlined />, label: "系统配置" },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = "/admin/" + (location.pathname.split("/")[2] || "users");

  return (
    <Layout style={{ background: "#fff" }}>
      <Sider width={200} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Content style={{ padding: "0 24px", minHeight: 500 }}>
        <Outlet />
      </Content>
    </Layout>
  );
}
