import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { CreNexusClient } from "../services/client";
import type { ConnectionOverview, Project } from "../types/api";
import { CodexConversationPage } from "./CodexConversationPage";

const CONNECTIONS: ConnectionOverview = {
  schema_version: "starbridge.desktop-connections.v2",
  checked_at: "2026-07-22T00:00:00Z",
  drawing_enabled: true,
  codex: {
    state: "paired",
    app_available: true,
    connector_configured: true,
    session_paired: true,
    pairing_code: "ABCD2345",
    message: "已关联",
    next_steps: [],
  },
  applications: [],
  safety: {
    loopback_only: true,
    credentials_read: false,
    external_apps_force_restarted: false,
  },
};

const PROJECT: Project = {
  schemaVersion: 1,
  projectId: "project-test",
  projectName: "客户项目",
  workflowId: "vector-delivery-v1",
  description: "",
  sourceAssets: [],
  currentJob: null,
  jobHistory: [],
  artifacts: [],
  qualityReports: [],
  evidence: [],
  createdAt: "2026-07-22T00:00:00Z",
  updatedAt: "2026-07-22T00:00:00Z",
};

describe("Codex conversation handoff", () => {
  it("opens a confirmed Codex task with selected project context", async () => {
    const openCodexTask = vi.fn().mockResolvedValue(undefined);
    const client = {
      getProjects: vi.fn().mockResolvedValue([PROJECT]),
      openCodexTask,
    } as unknown as CreNexusClient;

    render(<CodexConversationPage client={client} connections={CONNECTIONS} runtimeReady onOpenConnections={vi.fn()} />);
    await screen.findByRole("option", { name: "客户项目" });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "project-test" } });
    fireEvent.change(screen.getByLabelText("给 Codex 的要求"), { target: { value: "生成真实 AI 文件" } });
    fireEvent.click(screen.getByRole("button", { name: "在 Codex 中发送并继续" }));

    await waitFor(() => expect(openCodexTask).toHaveBeenCalledTimes(1));
    expect(openCodexTask.mock.calls[0][0]).toContain("project-test");
    expect(openCodexTask.mock.calls[0][0]).toContain("生成真实 AI 文件");
    expect(openCodexTask).toHaveBeenCalledWith(expect.any(String), true);
    expect(await screen.findByText("生成真实 AI 文件")).toBeInTheDocument();
    expect(screen.getByText(/不伪造模型回复/)).toBeInTheDocument();
  });

  it("routes an unpaired customer to the connection center", () => {
    const onOpenConnections = vi.fn();
    render(<CodexConversationPage client={{ getProjects: vi.fn() } as unknown as CreNexusClient} connections={{ ...CONNECTIONS, drawing_enabled: false, codex: { ...CONNECTIONS.codex, state: "awaiting_pairing", session_paired: false } }} runtimeReady={false} onOpenConnections={onOpenConnections} />);
    fireEvent.click(screen.getByRole("button", { name: "前往连接中心" }));
    expect(onOpenConnections).toHaveBeenCalledTimes(1);
  });
});
