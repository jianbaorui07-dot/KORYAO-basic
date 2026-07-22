import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState/EmptyState";
import type { CreNexusClient } from "../services/client";
import type { Project, WorkflowSummary } from "../types/api";

type DrawingMode = "artisan" | "smart" | "lightweight";

interface WorkflowsPageProps {
  client: CreNexusClient;
  runtimeReady: boolean;
  initialProjectId?: string;
  onOpenProjects: () => void;
  onOpenJob: (jobId: string, projectId: string) => void;
}

const MODE_COPY: Record<DrawingMode, [string, string]> = {
  artisan: ["工匠曲线", "适合 Logo 和扁平几何；优先使用贝塞尔曲线和更少锚点。"],
  smart: ["智能矢量", "默认推荐；适合插画与纹样，在细节、稳定性和锚点数量之间平衡。"],
  lightweight: ["轻量矢量", "生成更精简的结构，适合快速交付和后续编辑。"],
};

export function WorkflowsPage({ client, runtimeReady, initialProjectId, onOpenProjects, onOpenJob }: WorkflowsPageProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [projectId, setProjectId] = useState(initialProjectId ?? "");
  const [assetId, setAssetId] = useState("");
  const [drawingMode, setDrawingMode] = useState<DrawingMode>("smart");
  const [exactMaxDimension, setExactMaxDimension] = useState(1024);
  const [exactMaxSvgSizeMb, setExactMaxSvgSizeMb] = useState(128);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!runtimeReady) return;
    try {
      const [nextProjects, nextWorkflows] = await Promise.all([
        client.getProjects(),
        client.getWorkflows(),
      ]);
      const vectorProjects = nextProjects.filter((project) => project.workflowId === "vector-delivery-v1");
      setProjects(vectorProjects);
      setWorkflows(nextWorkflows);
      setProjectId((current) => current || initialProjectId || vectorProjects[0]?.projectId || "");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "工作流暂时无法读取。");
    }
  }, [client, initialProjectId, runtimeReady]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.projectId === projectId),
    [projectId, projects],
  );
  const selectedWorkflow = workflows.find((workflow) => workflow.workflowId === "vector-delivery-v1");

  useEffect(() => {
    setAssetId((current) =>
      selectedProject?.sourceAssets.some((asset) => asset.assetId === current)
        ? current
        : selectedProject?.sourceAssets[0]?.assetId ?? "",
    );
  }, [selectedProject]);

  const createJob = async () => {
    if (!selectedProject || !assetId) return;
    setBusy(true);
    setError("");
    try {
      const job = await client.createCreativeJob({
        projectId: selectedProject.projectId,
        workflowId: "vector-delivery-v1",
        sourceAssetId: assetId,
        drawingMode,
        parameters: { exact: { maxDimension: exactMaxDimension, maxSvgSizeMb: exactMaxSvgSizeMb } },
      });
      onOpenJob(job.jobId, job.projectId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "任务计划没有建立成功。");
    } finally {
      setBusy(false);
    }
  };

  if (!runtimeReady) {
    return <div className="standard-page"><header className="page-intro"><div><span className="page-kicker">创意工作流</span><h2>本地服务正在启动</h2><p>项目与素材会在安全 sidecar 就绪后自动载入，请稍候。</p></div></header><EmptyState title="正在连接本地创意引擎" description="无需重复选择或刷新；服务就绪后此页会自动显示已有项目。" /></div>;
  }

  if (projects.length === 0 && runtimeReady) {
    return <div className="standard-page"><header className="page-intro"><div><span className="page-kicker">创意工作流</span><h2>从一个项目开始</h2><p>工作流需要项目来保存素材、任务、真实产物和证据。</p></div></header><EmptyState title="还没有可用项目" description="先创建项目并导入一张明确选择的图片。" action={<button type="button" className="primary" onClick={onOpenProjects}>创建项目</button>} /></div>;
  }

  return (
    <div className="standard-page">
      <header className="page-intro"><div><span className="page-kicker">vector-delivery-v1</span><h2>先建立精确基线，再绘制可编辑矢量</h2><p>固定顺序为：源素材验证 → 像素级精确重建 → 基线验收 → 绘制型矢量 → 质量比较 → 人工确认 → 交付。不会回退到 Illustrator Image Trace。</p></div><span className="state-label planned">{selectedWorkflow?.capabilityStatus === "experimental" ? "实验性" : "状态待确认"}</span></header>
      {error ? <div className="error-state" role="alert"><strong>操作未完成</strong><p>{error}</p></div> : null}
      <div className="workflow-builder-grid">
        <section className="record-panel">
          <div className="section-heading"><div><span>输入</span><h3>项目与源素材</h3></div></div>
          <div className="form-grid">
            <label>项目<select value={projectId} onChange={(event) => setProjectId(event.target.value)}>{projects.map((project) => <option key={project.projectId} value={project.projectId}>{project.projectName}</option>)}</select></label>
            <label>源素材<select value={assetId} onChange={(event) => setAssetId(event.target.value)}><option value="">请选择已导入素材</option>{selectedProject?.sourceAssets.map((asset) => <option key={asset.assetId} value={asset.assetId}>{asset.basename}</option>)}</select></label>
          </div>
          {selectedProject && selectedProject.sourceAssets.length === 0 ? <p className="truth-note">这个项目还没有源素材。请回到项目页明确选择并导入图片。</p> : null}
        </section>
        <section className="record-panel">
          <div className="section-heading"><div><span>绘制方式</span><h3>选择第二阶段的矢量策略</h3></div><span className="state-label neutral">默认：智能矢量</span></div>
          <div className="mode-grid">
            {(Object.keys(MODE_COPY) as DrawingMode[]).map((mode) => <button type="button" key={mode} className={`mode-card ${drawingMode === mode ? "is-selected" : ""}`} onClick={() => setDrawingMode(mode)}><strong>{MODE_COPY[mode][0]}</strong><span>{MODE_COPY[mode][1]}</span></button>)}
          </div>
        </section>
        <section className="record-panel">
          <div className="section-heading"><div><span>精确基线</span><h3>控制大图的安全尺寸</h3></div><span className="state-label neutral">推荐：1024</span></div>
          <div className="form-grid">
            <label>精确基线最长边<select aria-label="精确基线最长边" value={exactMaxDimension} onChange={(event) => setExactMaxDimension(Number(event.target.value))}><option value={1024}>1024 像素（推荐）</option><option value={512}>512 像素（复杂大图）</option><option value={1600}>1600 像素（更高细节）</option><option value={2048}>2048 像素（可能较慢）</option><option value={0}>原始尺寸（可能超出安全上限）</option></select></label>
            <label>SVG 安全上限<select aria-label="SVG 安全上限" value={exactMaxSvgSizeMb} onChange={(event) => setExactMaxSvgSizeMb(Number(event.target.value))}><option value={64}>64 MB（兼容优先）</option><option value={128}>128 MB（推荐）</option><option value={256}>256 MB（大型文件）</option></select></label>
          </div>
          <p className="truth-note">源图片不会被缩小或覆盖。选择非原始尺寸时，精确 SVG 会对本地缩放工作副本做逐像素验证；后续绘制型矢量仍按所选绘制策略独立生成。</p>
        </section>
        <section className="record-panel workflow-truth-panel">
          <div className="section-heading"><div><span>安全边界</span><h3>写入会分段确认</h3></div></div>
          <ol className="workflow-step-list"><li>导入时只复制明确选择的文件。</li><li>精确重建写入前单独确认。</li><li>绘制型矢量写入前再次确认。</li><li>交付前由你审核实际生成的产物。</li></ol>
          <p className="truth-note">任务计划与确认令牌绑定到同一个项目、工作流、步骤和计划哈希；令牌一次使用并会过期。</p>
          <div className="button-row"><button type="button" className="secondary" onClick={onOpenProjects}>管理项目</button><button type="button" className="primary" disabled={!runtimeReady || busy || !assetId} onClick={() => void createJob()}>建立任务计划</button></div>
        </section>
      </div>
    </div>
  );
}
