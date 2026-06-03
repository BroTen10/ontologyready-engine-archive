import { Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import AdminLayout from "./layouts/AdminLayout";
import AuthGuard from "./components/AuthGuard";
import GraphPage from "./pages/GraphPage";
import TypesPage from "./pages/TypesPage";
import InstancesPage from "./pages/InstancesPage";
import ModelingPage from "./pages/ModelingPage";
import LoginPage from "./pages/LoginPage";
import AutoModelPage from "./pages/AutoModelPage";
import SkillsPage from "./pages/SkillsPage";
import LLMConfigPage from "./pages/LLMConfigPage";
import AdvancedSearchPage from "./pages/AdvancedSearchPage";
import UserSettingsPage from "./pages/UserSettingsPage";
import UsersPage from "./pages/admin/UsersPage";
import RolesPage from "./pages/admin/RolesPage";
import GroupsPage from "./pages/admin/GroupsPage";
import ACRPage from "./pages/admin/ACRPage";
import SystemConfigPage from "./pages/admin/SystemConfigPage";
import ApiKeysPage from "./pages/admin/ApiKeysPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <AuthGuard>
            <MainLayout />
          </AuthGuard>
        }
      >
        <Route index element={<Navigate to="/graph" replace />} />
        <Route path="graph" element={<GraphPage />} />
        <Route path="types" element={<TypesPage />} />
        <Route path="instances" element={<InstancesPage />} />
        <Route path="modeling" element={<ModelingPage />} />
        <Route path="automodel" element={<AutoModelPage />} />
        <Route path="skills" element={<SkillsPage />} />
        <Route path="llm-config" element={<LLMConfigPage />} />
        <Route path="search" element={<AdvancedSearchPage />} />
        <Route path="settings" element={<UserSettingsPage />} />

        <Route path="admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/users" replace />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="roles" element={<RolesPage />} />
          <Route path="groups" element={<GroupsPage />} />
          <Route path="acr" element={<ACRPage />} />
          <Route path="apikeys" element={<ApiKeysPage />} />
          <Route path="config" element={<SystemConfigPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/graph" replace />} />
    </Routes>
  );
}
