import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { fetchDatasets } from "../api/endpoints";

interface DatasetOption {
  value: string;
  label: string;
}

interface DatasetContextType {
  dataset: string;
  setDataset: (d: string) => void;
  datasets: DatasetOption[];
}

const DatasetContext = createContext<DatasetContextType>({
  dataset: "default",
  setDataset: () => {},
  datasets: [{ value: "default", label: "默认数据集" }],
});

export function DatasetProvider({ children }: { children: ReactNode }) {
  const [dataset, setDataset] = useState("default");
  const [datasets, setDatasets] = useState<DatasetOption[]>([
    { value: "default", label: "默认数据集" },
  ]);

  useEffect(() => {
    fetchDatasets()
      .then((data) => {
        const list = data as Array<{ id: string; name: string }>;
        if (list && list.length > 0) {
          setDatasets(
            list.map((d) => ({ value: d.id, label: d.name })),
          );
        }
      })
      .catch(() => {
        // 保持默认数据集
      });
  }, []);

  return (
    <DatasetContext.Provider value={{ dataset, setDataset, datasets }}>
      {children}
    </DatasetContext.Provider>
  );
}

export function useDataset() {
  return useContext(DatasetContext);
}
