import { createContext, useContext, useState, type ReactNode } from "react";

interface DatasetContextType {
  dataset: string;
  setDataset: (d: string) => void;
}

const DatasetContext = createContext<DatasetContextType>({ dataset: "default", setDataset: () => {} });

export function DatasetProvider({ children }: { children: ReactNode }) {
  const [dataset, setDataset] = useState("default");
  return (
    <DatasetContext.Provider value={{ dataset, setDataset }}>
      {children}
    </DatasetContext.Provider>
  );
}

export function useDataset() {
  return useContext(DatasetContext);
}
