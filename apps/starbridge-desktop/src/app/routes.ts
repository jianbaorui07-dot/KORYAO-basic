export type PageId =
  | "home"
  | "vectorization"
  | "batch"
  | "integrations"
  | "tasks"
  | "license"
  | "diagnostics";

export interface NavigationItem {
  id: PageId;
  label: string;
}

export const NAVIGATION_ITEMS: NavigationItem[] = [
  { id: "home", label: "首页" },
  { id: "vectorization", label: "图片矢量化" },
  { id: "batch", label: "批量处理" },
  { id: "integrations", label: "软件联动" },
  { id: "tasks", label: "任务记录" },
  { id: "license", label: "版本与授权" },
  { id: "diagnostics", label: "设置与诊断" },
];

export const PAGE_TITLES = Object.fromEntries(
  NAVIGATION_ITEMS.map((item) => [item.id, item.label]),
) as Record<PageId, string>;
