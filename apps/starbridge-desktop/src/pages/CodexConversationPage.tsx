import { useEffect, useMemo, useState } from "react";

import type { CreNexusClient } from "../services/client";
import type { ConnectionOverview, Project } from "../types/api";

interface CodexConversationPageProps {
  client: CreNexusClient;
  connections: ConnectionOverview | null;
  runtimeReady: boolean;
  onOpenConnections: () => void;
}

type ConversationEntry = {
  id: number;
  role: "user" | "bridge";
  text: string;
};

const WORK_MODES = {
  customer: {
    label: "用户视角",
    prompt: "请站在普通客户视角完成一次端到端任务：只使用软件里可见的入口，记录每一步是否清楚、是否能恢复、产物是否真实。遇到失败时先给出客户能理解的提示。",
  },
  maker: {
    label: "制作者视角",
    prompt: "请站在产品制作者视角检查当前失败：定位到代码、桥接、权限或环境层，修复后运行相关测试，并把结果交回用户视角重新验收。不要通过删除测试或伪造产物制造成功。",
  },
  loop: {
    label: "左右迭代",
    prompt: "执行用户视角 → 制作者视角 → 用户视角的闭环：先复现真实客户路径，再修复根因，最后用同一路径重新验收。每完成一个可回滚阶段，列出测试证据和仍未验证项。",
  },
} as const;

export function CodexConversationPage({
  client,
  connections,
  runtimeReady,
  onOpenConnections,
}: CodexConversationPageProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [entries, setEntries] = useState<ConversationEntry[]>([]);

  const paired = connections?.codex.session_paired === true;
  const selectedProject = useMemo(
    () => projects.find((project) => project.projectId === projectId),
    [projectId, projects],
  );

  useEffect(() => {
    if (!runtimeReady) return;
    void client.getProjects().then(setProjects).catch(() => setProjects([]));
  }, [client, runtimeReady]);

  const openConversation = async () => {
    const customerRequest = prompt.trim();
    if (!customerRequest || !paired) return;
    setBusy(true);
    setError("");
    const projectContext = selectedProject
      ? `当前 CreNexus 项目标识：${selectedProject.projectId}。请只通过已配对的 CreNexus MCP 查询该项目，不要猜测本机路径。\n`
      : "";
    const codexPrompt = `${projectContext}客户要求：${customerRequest}\n\n执行规则：先说明将如何验证，再通过 CreNexus MCP 完成任务。任何写入、导出、覆盖或外部软件操作都必须保留明确确认；不要读取或输出 Codex 登录凭据。真实失败要如实返回，并给出下一步。`;
    try {
      await client.openCodexTask(codexPrompt, true);
      const now = Date.now();
      setEntries((current) => [
        ...current,
        { id: now, role: "user", text: customerRequest },
        {
          id: now + 1,
          role: "bridge",
          text: "已把这条指令交接到新的 Codex 对话。真实回复、工具调用和审批会在 Codex 中继续；CreNexus 不读取你的登录凭据，也不伪造模型回复。",
        },
      ]);
      setPrompt("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Codex 对话没有打开，请从连接中心重新关联。" );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="standard-page codex-workspace">
      <header className="page-intro">
        <div>
          <span className="page-kicker">CODEX CONVERSATION</span>
          <h2>与 Codex 对话，再由 CreNexus 安全执行</h2>
          <p>这里负责组织项目上下文与客户要求，Codex 负责理解、规划和调用 CreNexus MCP；本地写入与外部软件操作仍保留独立确认。</p>
        </div>
        <span className={paired ? "local-badge" : "connection-required-badge"}>{paired ? "Codex 已关联" : "等待关联"}</span>
      </header>

      {!paired ? (
        <section className="drawing-connection-gate">
          <div><span>对话尚未开放</span><h3>先关联当前 Codex 会话</h3><p>关联只验证本次本地会话，不读取账号、Token 或历史对话。</p></div>
          <button type="button" className="primary" onClick={onOpenConnections}>前往连接中心</button>
        </section>
      ) : null}
      {error ? <div className="error-state" role="alert"><strong>没有完成交接</strong><p>{error}</p></div> : null}

      <div className="codex-workspace-grid">
        <section className="record-panel codex-chat-panel" aria-label="Codex 对话交接记录">
          <div className="section-heading"><div><span>当前会话</span><h3>对话交接</h3></div><span className="state-label neutral">仅本次打开期间</span></div>
          <div className="codex-chat-stream" aria-live="polite">
            <article className="codex-message codex-message-bridge"><strong>CreNexus 安全桥接</strong><p>告诉 Codex 你想完成什么。它会在独立的真实 Codex 对话里回复，并通过已配对的 MCP 调用本软件。</p></article>
            {entries.map((entry) => <article key={entry.id} className={`codex-message codex-message-${entry.role}`}><strong>{entry.role === "user" ? "你" : "CreNexus 安全桥接"}</strong><p>{entry.text}</p></article>)}
          </div>
          <div className="codex-composer">
            <label>项目上下文（可选）<select value={projectId} onChange={(event) => setProjectId(event.target.value)}><option value="">不附带项目编号</option>{projects.map((project) => <option key={project.projectId} value={project.projectId}>{project.projectName}</option>)}</select></label>
            <label>给 Codex 的要求<textarea aria-label="给 Codex 的要求" value={prompt} maxLength={2400} rows={6} placeholder="例如：把当前项目的鲤鱼图片生成可编辑矢量，并导出为 AI 文件。先用用户视角验收，失败后从制作者视角修正。" onChange={(event) => setPrompt(event.target.value)} /></label>
            <div className="button-row"><button type="button" className="primary" disabled={!paired || busy || !prompt.trim()} onClick={() => void openConversation()}>{busy ? "正在打开…" : "在 Codex 中发送并继续"}</button><span>{prompt.length}/2400</span></div>
          </div>
        </section>

        <aside className="record-panel codex-mode-panel">
          <div className="section-heading"><div><span>迭代方法</span><h3>用户 ↔ 制作者</h3></div></div>
          {(Object.keys(WORK_MODES) as Array<keyof typeof WORK_MODES>).map((mode) => <button type="button" key={mode} onClick={() => setPrompt(WORK_MODES[mode].prompt)}><strong>{WORK_MODES[mode].label}</strong><span>{WORK_MODES[mode].prompt}</span></button>)}
          <p className="truth-note">Codex app-server 目前属于实验接口，因此客户版本使用稳定的 Codex 深链与 CreNexus MCP 交接；界面不会把本地占位文字伪装成 Codex 回答。</p>
        </aside>
      </div>
    </div>
  );
}
