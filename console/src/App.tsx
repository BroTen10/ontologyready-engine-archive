import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter } from "react-router-dom";
import { ConfigProvider, App as AntApp } from "antd";
import zhCN from "antd/locale/zh_CN";
import { AuthProvider } from "./hooks/useAuth";
import { DatasetProvider } from "./hooks/useDataset";
import AppRouter from "./AppRouter";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <AntApp>
          <HashRouter>
            <AuthProvider>
              <DatasetProvider>
                <AppRouter />
              </DatasetProvider>
            </AuthProvider>
          </HashRouter>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
