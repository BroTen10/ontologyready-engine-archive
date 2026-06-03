import { Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import GraphPage from "./pages/GraphPage";
import TypesPage from "./pages/TypesPage";
import InstancesPage from "./pages/InstancesPage";
import ModelingPage from "./pages/ModelingPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/graph" replace />} />
        <Route path="graph" element={<GraphPage />} />
        <Route path="types" element={<TypesPage />} />
        <Route path="instances" element={<InstancesPage />} />
        <Route path="modeling" element={<ModelingPage />} />
      </Route>
    </Routes>
  );
}
