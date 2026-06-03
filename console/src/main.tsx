import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { DatasetProvider } from "./hooks/useDataset";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <DatasetProvider>
      <App />
    </DatasetProvider>
  </StrictMode>,
);
