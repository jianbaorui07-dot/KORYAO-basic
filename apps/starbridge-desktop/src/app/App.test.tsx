import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { StarBridgeClient } from "../services/client";
import { UserFacingError } from "../services/client";
import type { ConnectionOverview, RuntimeStatus } from "../types/api";
import { App } from "./App";

const PAIRED_CONNECTIONS: ConnectionOverview = {
  schema_version: "starbridge.desktop-connections.v2",
  checked_at: "2026-07-18T08:00:00Z",
  drawing_enabled: true,
  codex: {
    state: "paired",
    app_available: true,
    connector_configured: true,
    session_paired: true,
    pairing_code: "ABCD2345",
    message: "Codex 已关联当前桌面会话，制图入口已开放。",
    next_steps: [],
  },
  applications: [],
  safety: {
    loopback_only: true,
    credentials_read: false,
    external_apps_force_restarted: false,
  },
};

function makeClient(status: RuntimeStatus | Promise<RuntimeStatus>): StarBridgeClient {
  return {
    getRuntimeStatus: vi.fn().mockImplementation(() => Promise.resolve(status)),
    getHealth: vi.fn().mockResolvedValue({ ok: true }),
    getBootstrap: vi.fn().mockResolvedValue({ ok: true }),
    restartBackend: vi.fn().mockResolvedValue({
      state: "connected",
      message: "本地服务已恢复。",
      recoveryAttempts: 1,
    }),
    openLogsDirectory: vi.fn().mockResolvedValue("<LOCAL_APP_DATA>/StarBridge/logs"),
    getConnections: vi.fn().mockResolvedValue(PAIRED_CONNECTIONS),
    installCodexConnector: vi.fn().mockResolvedValue({
      installed: true,
      connector: "starbridge-desktop",
      message: "连接器已安装。",
      restart_required: true,
      next_steps: [],
    }),
    resetCodexConnection: vi.fn().mockResolvedValue({ reset: true, pairing_code: "WXYZ6789" }),
    openCodexPairing: vi.fn().mockResolvedValue(undefined),
    openGitHubProject: vi.fn().mockResolvedValue(undefined),
    pairCreativeApplication: vi.fn(),
    reconnectCreativeApplication: vi.fn(),
    disconnectCreativeApplication: vi.fn(),
    getVersion: vi.fn().mockResolvedValue({ desktop: "0.1.0" }),
    getUpdateStatus: vi.fn().mockResolvedValue({
      configured: false,
      source: "GitHub Releases",
      currentVersion: "0.1.0",
      available: false,
      signatureRequired: true,
      automaticChecksSupported: false,
    }),
    checkForUpdate: vi.fn().mockResolvedValue({
      configured: false,
      source: "GitHub Releases",
      currentVersion: "0.1.0",
      available: false,
      signatureRequired: true,
      automaticChecksSupported: false,
    }),
    installUpdate: vi.fn().mockResolvedValue(undefined),
    getLicenseStatus: vi.fn().mockResolvedValue({
      state: "community",
      edition: "community",
      message: "Community 免费版正在本机运行，不需要授权文件。",
      deviceLimit: 0,
      features: [],
      commercialVerifierConfigured: false,
    }),
    createLicenseRequest: vi.fn().mockResolvedValue({
      requestId: "request-test",
      fileName: "StarBridge-license-request-request-test.json",
      location: "<LOCAL_APP_DATA>/StarBridge/license/requests",
      folderOpened: true,
    }),
    importLicenseFile: vi.fn().mockResolvedValue({
      state: "active",
      edition: "pro",
      message: "离线授权签名和当前设备绑定均已验证。",
      licenseId: "SB-PRO-TEST",
      deviceLimit: 1,
      features: ["batch.processing"],
      commercialVerifierConfigured: true,
    }),
    chooseVectorInput: vi.fn().mockResolvedValue(null),
    startVectorization: vi.fn(),
    getVectorizationJob: vi.fn(),
    getVectorizationHistory: vi.fn().mockResolvedValue({ eventCount: 0, events: [] }),
    openVectorOutput: vi.fn().mockResolvedValue(undefined),
  };
}

describe("desktop runtime status", () => {
  it("shows the product home while the runtime starts", () => {
    const pending = new Promise<RuntimeStatus>(() => undefined);
    render(<App client={makeClient(pending)} />);

    expect(screen.getByText("StarBridge 已准备好")).toBeInTheDocument();
    expect(screen.getByText("正在启动")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "连接 Codex 后开始制图" })).toBeDisabled();
  });

  it("shows a connected state in ordinary language", async () => {
    render(
      <App
        client={makeClient({
          state: "connected",
          message: "安全本地服务已经就绪。",
          recoveryAttempts: 0,
          port: 49152,
        })}
      />,
    );

    expect(await screen.findByText("运行正常 · 仅本机")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "开始图片矢量化" })).toBeEnabled();
    expect(screen.queryByText(/49152/)).not.toBeInTheDocument();
  });

  it("opens the fixed GitHub project from the top bar", async () => {
    const client = makeClient({
      state: "connected",
      message: "安全本地服务已经就绪。",
      recoveryAttempts: 0,
    });
    render(<App client={client} />);

    fireEvent.click(await screen.findByRole("button", { name: "GitHub 项目" }));
    expect(client.openGitHubProject).toHaveBeenCalledOnce();
  });

  it("locks drawing until the current Codex session is paired", async () => {
    const client = makeClient({
      state: "connected",
      message: "安全本地服务已经就绪。",
      recoveryAttempts: 0,
    });
    client.getConnections = vi.fn().mockResolvedValue({
      ...PAIRED_CONNECTIONS,
      drawing_enabled: false,
      codex: {
        ...PAIRED_CONNECTIONS.codex,
        state: "awaiting_pairing",
        session_paired: false,
        message: "连接器已配置，正在等待 Codex 确认当前桌面会话。",
      },
    });
    render(<App client={client} />);

    const connect = await screen.findByRole("button", { name: "连接 Codex 后开始制图" });
    fireEvent.click(connect);
    expect(await screen.findByText("先关联 Codex，再连接本机创意软件")).toBeInTheDocument();
    expect(screen.getByText("ABCD2345")).toBeInTheDocument();
  });

  it("installs the managed connector before opening a new Codex pairing task", async () => {
    const client = makeClient({
      state: "connected",
      message: "安全本地服务已经就绪。",
      recoveryAttempts: 0,
    });
    client.getConnections = vi.fn().mockResolvedValue({
      ...PAIRED_CONNECTIONS,
      drawing_enabled: false,
      codex: {
        ...PAIRED_CONNECTIONS.codex,
        state: "connector_required",
        connector_configured: false,
        session_paired: false,
        message: "已找到 Codex；需要安装 StarBridge 本地连接器。",
      },
    });
    render(<App client={client} />);

    fireEvent.click(await screen.findByRole("button", { name: "连接 Codex 后开始制图" }));
    fireEvent.click(await screen.findByRole("button", { name: "安装连接器并打开 Codex" }));

    await waitFor(() => expect(client.installCodexConnector).toHaveBeenCalledWith(true));
    expect(client.openCodexPairing).toHaveBeenCalledWith("ABCD2345");
  });

  it("pairs a running creative application without claiming a process-only bridge can edit", async () => {
    const client = makeClient({
      state: "connected",
      message: "安全本地服务已经就绪。",
      recoveryAttempts: 0,
    });
    const blender = {
      id: "blender",
      name: "Blender",
      mark: "Bl",
      state: "running" as const,
      installed: true,
      running: true,
      bridge_available: false,
      managed: false,
      message: "软件正在运行，等待与当前 StarBridge 会话配对。",
      pairing_state: "ready_to_pair" as const,
      paired: false,
      adapter_kind: "process" as const,
      control_level: "session_detection" as const,
      capabilities: ["进程会话检测", "本机任务路由"],
      next_steps: [],
    };
    client.getConnections = vi.fn().mockResolvedValue({
      ...PAIRED_CONNECTIONS,
      applications: [blender],
    });
    client.pairCreativeApplication = vi.fn().mockResolvedValue({
      ...blender,
      paired: true,
      pairing_state: "paired_limited",
      message: "当前软件会话已配对；目前仅支持检测和任务路由。",
    });
    render(<App client={client} />);

    fireEvent.click(await screen.findByRole("button", { name: "连接中心" }));
    fireEvent.click(await screen.findByRole("button", { name: "开始配对" }));

    await waitFor(() => expect(client.pairCreativeApplication).toHaveBeenCalledWith("blender"));
    expect(await screen.findByText(/当前仅提供存在性检测和任务路由/)).toBeInTheDocument();
  });

  it("shows offline recovery guidance and technical details", async () => {
    render(
      <App
        client={makeClient({
          state: "offline",
          message: "没有检测到本地服务，请尝试重新启动。",
          recoveryAttempts: 1,
          technicalDetails: "backend process not found",
        })}
      />,
    );

    expect(await screen.findByText("本地服务离线")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "打开设置与诊断" }));
    expect(screen.getByRole("button", { name: "重新启动本地服务" })).toBeInTheDocument();
    expect(screen.getByText("技术详情")).toBeInTheDocument();
    expect(screen.getByText("backend process not found")).toBeInTheDocument();
  });

  it("turns a 401 or 403 style error into a user-facing failure", async () => {
    const client = makeClient({
      state: "connected",
      message: "connected",
      recoveryAttempts: 0,
    });
    client.getRuntimeStatus = vi.fn().mockRejectedValue(
      new UserFacingError(
        "authentication_failed",
        "桌面会话已失效，请重新启动本地服务。",
        "HTTP 403; authentication_failed",
        [],
        403,
      ),
    );
    render(<App client={client} />);

    expect(await screen.findByText("需要处理")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "打开设置与诊断" }));
    expect(screen.getByText("桌面会话已失效，请重新启动本地服务。")).toBeInTheDocument();
    expect(screen.getByText("HTTP 403; authentication_failed")).toBeInTheDocument();
  });

  it("offers a manual restart and reports recovery", async () => {
    const client = makeClient({
      state: "failed",
      message: "启动失败。",
      recoveryAttempts: 1,
    });
    render(<App client={client} />);
    await screen.findByText("需要处理");
    fireEvent.click(screen.getByRole("button", { name: "打开设置与诊断" }));

    fireEvent.click(screen.getByRole("button", { name: "重新启动本地服务" }));

    await waitFor(() => expect(client.restartBackend).toHaveBeenCalledOnce());
    expect(await screen.findByText("运行正常 · 仅本机")).toBeInTheDocument();
  });

  it("shows a signed GitHub update and requires explicit install confirmation", async () => {
    const client = makeClient({ state: "connected", message: "connected", recoveryAttempts: 0 });
    const update = {
      configured: true,
      source: "GitHub Releases",
      currentVersion: "0.1.0",
      available: true,
      version: "0.2.0",
      notes: "稳定性改进",
      signatureRequired: true,
      automaticChecksSupported: true,
    };
    client.getUpdateStatus = vi.fn().mockResolvedValue(update);
    client.checkForUpdate = vi.fn().mockResolvedValue(update);
    render(<App client={client} />);

    expect(await screen.findByRole("button", { name: "可更新至 v0.2.0" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "可更新至 v0.2.0" }));
    const install = screen.getByRole("button", { name: "更新到 v0.2.0" });
    expect(install).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", { name: /我已保存正在进行的工作/ }));
    expect(install).toBeEnabled();
    fireEvent.click(install);
    await waitFor(() => expect(client.installUpdate).toHaveBeenCalledWith(
      "0.2.0",
      true,
      expect.any(Function),
    ));
  });

  it("states that a development build cannot claim public updates", async () => {
    render(<App client={makeClient({ state: "connected", message: "connected", recoveryAttempts: 0 })} />);
    fireEvent.click(await screen.findByRole("button", { name: "打开设置与诊断" }));
    expect(screen.getByText("发布通道未启用")).toBeInTheDocument();
    expect(screen.getByText(/没有正式更新验签公钥/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "立即检查更新" })).not.toBeInTheDocument();
  });

  it("shows the offline Community license flow without claiming Pro is active", async () => {
    const client = makeClient({
      state: "connected",
      message: "connected",
      recoveryAttempts: 0,
    });
    render(<App client={client} />);

    fireEvent.click(await screen.findByRole("button", { name: "版本与授权" }));
    expect(screen.getByText("你可以直接使用免费功能，无需登录、无需联网，也不需要授权文件。"))
      .toBeInTheDocument();
    expect(screen.queryByText("授权有效")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "导出设备申请" }));
    await waitFor(() => expect(client.createLicenseRequest).toHaveBeenCalledOnce());
    expect(await screen.findByText(/文件夹已打开/)).toBeInTheDocument();
  });

  it("explains how to recover from an invalid license while keeping Community available", async () => {
    const client = makeClient({ state: "connected", message: "connected", recoveryAttempts: 0 });
    client.getLicenseStatus = vi.fn().mockResolvedValue({
      state: "invalid",
      edition: "community",
      message: "授权签名未通过验证。",
      deviceLimit: 0,
      features: [],
      commercialVerifierConfigured: true,
      reason: "signature_invalid",
    });
    render(<App client={client} />);

    fireEvent.click(await screen.findByRole("button", { name: "版本与授权" }));
    expect(screen.getByText("授权文件未生效")).toBeInTheDocument();
    expect(screen.getByText(/授权签名未通过验证/)).toBeInTheDocument();
    expect(screen.getByText(/Community 免费功能仍可继续使用/)).toBeInTheDocument();
  });

  it("runs the Community vectorization flow through selection, confirmation and result", async () => {
    const client = makeClient({
      state: "connected",
      message: "运行正常。",
      recoveryAttempts: 0,
    });
    client.chooseVectorInput = vi.fn().mockResolvedValue({
      selectionId: "selection-test",
      fileName: "example.png",
      width: 320,
      height: 240,
      sourceHash: "abc123",
      previewDataUrl: "data:image/png;base64,AA==",
    });
    client.startVectorization = vi.fn().mockResolvedValue({
      jobId: "vector-test",
      status: "queued",
      progress: 6,
      stage: "已确认，正在准备",
      mode: "smart",
      createdAt: "2026-07-17T08:00:00Z",
    });
    client.getVectorizationJob = vi.fn().mockResolvedValue({
      jobId: "vector-test",
      status: "completed",
      progress: 100,
      stage: "处理完成",
      mode: "smart",
      createdAt: "2026-07-17T08:00:00Z",
      completedAt: "2026-07-17T08:00:01Z",
      result: {
        modeLabel: "智能矢量",
        sourceHash: "abc123",
        sourcePreviewDataUrl: "data:image/png;base64,AA==",
        resultPreviewDataUrl: "data:image/png;base64,AA==",
        metrics: { colors: 8, subpaths: 12, points: 36, svgBytes: 2048, elapsedSeconds: 1.2 },
        warnings: [],
        outputAvailable: true,
      },
    });

    render(<App client={client} />);
    fireEvent.click(await screen.findByRole("button", { name: "开始图片矢量化" }));
    fireEvent.click(screen.getByRole("button", { name: "选择图片" }));
    expect(await screen.findByText("example.png")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "开始本机矢量化" }));

    await waitFor(() => expect(client.startVectorization).toHaveBeenCalledWith(
      expect.objectContaining({
        selectionId: "selection-test",
        confirmRun: true,
        confirmWrite: true,
        confirmExport: true,
      }),
    ));
    expect(await screen.findByText("任务记录已保存，输出位于 StarBridge 本机应用数据目录。", {}, { timeout: 2000 })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "打开输出文件夹" }));
    await waitFor(() => expect(client.openVectorOutput).toHaveBeenCalledWith("vector-test"));
  });
});
