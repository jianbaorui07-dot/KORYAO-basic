import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BatchPage } from "../pages/BatchPage";
import { DiagnosticsPage } from "../pages/DiagnosticsPage";
import { HomePage } from "../pages/HomePage";
import { IntegrationsPage } from "../pages/IntegrationsPage";
import { LicensePage } from "../pages/LicensePage";
import { TasksPage } from "../pages/TasksPage";
import { VectorizationPage } from "../pages/VectorizationPage";
import { StarBridgeApiClient, UserFacingError, type StarBridgeClient } from "../services/client";
import type { LicenseStatus, RuntimeStatus, VectorHistoryEvent, VersionInfo } from "../types/api";
import { AppShell } from "./AppShell";
import type { PageId } from "./routes";

const INITIAL_STATUS: RuntimeStatus = {
  state: "starting",
  message: "正在准备本机创意工作台。",
  recoveryAttempts: 0,
};

const INITIAL_LICENSE: LicenseStatus = {
  state: "community",
  edition: "community",
  message: "Community 免费版正在本机运行，不需要授权文件。",
  deviceLimit: 0,
  features: [],
  commercialVerifierConfigured: false,
};

interface AppProps {
  client?: StarBridgeClient;
}

function statusFromError(error: unknown): RuntimeStatus {
  if (error instanceof UserFacingError) {
    return {
      state: error.code === "backend_offline" ? "offline" : "failed",
      message: error.message,
      recoveryAttempts: 0,
      technicalDetails: error.technicalDetails,
    };
  }
  return {
    state: "failed",
    message: "本地服务状态暂时无法确认。请在设置与诊断中重新启动。",
    recoveryAttempts: 0,
    technicalDetails: error instanceof Error ? error.message : String(error),
  };
}

export function App({ client: providedClient }: AppProps) {
  const client = useMemo(() => providedClient ?? new StarBridgeApiClient(), [providedClient]);
  const [page, setPage] = useState<PageId>("home");
  const [status, setStatus] = useState<RuntimeStatus>(INITIAL_STATUS);
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [license, setLicense] = useState<LicenseStatus>(INITIAL_LICENSE);
  const [tasks, setTasks] = useState<VectorHistoryEvent[]>([]);
  const mounted = useRef(true);

  const refreshStatus = useCallback(async () => {
    try {
      const next = await client.getRuntimeStatus();
      if (mounted.current) setStatus(next);
    } catch (error) {
      if (mounted.current) setStatus(statusFromError(error));
    }
  }, [client]);

  const refreshTasks = useCallback(async () => {
    try {
      const history = await client.getVectorizationHistory();
      if (mounted.current) setTasks(history.events);
    } catch {
      // History is secondary; an offline state is already visible in the shell.
    }
  }, [client]);

  useEffect(() => {
    mounted.current = true;
    void refreshStatus();
    void client.getVersion().then((next) => mounted.current && setVersion(next)).catch(() => undefined);
    void client.getLicenseStatus().then((next) => mounted.current && setLicense(next)).catch(() => undefined);
    return () => { mounted.current = false; };
  }, [client, refreshStatus]);

  useEffect(() => {
    if (status.state === "starting" || status.state === "recovering") {
      const timer = window.setTimeout(() => void refreshStatus(), 600);
      return () => window.clearTimeout(timer);
    }
    if (status.state === "connected") void refreshTasks();
    return undefined;
  }, [refreshStatus, refreshTasks, status.state]);

  const restart = useCallback(async () => {
    setStatus((current) => ({ ...current, state: "recovering", message: "正在重新启动本地服务。" }));
    try {
      setStatus(await client.restartBackend());
    } catch (error) {
      setStatus(statusFromError(error));
    }
  }, [client]);

  const renderPage = () => {
    switch (page) {
      case "home":
        return <HomePage status={status} recentTasks={tasks} onNavigate={setPage} />;
      case "vectorization":
        return <VectorizationPage client={client} runtimeReady={status.state === "connected"} onTaskSaved={() => void refreshTasks()} />;
      case "batch":
        return <BatchPage />;
      case "integrations":
        return <IntegrationsPage />;
      case "tasks":
        return <TasksPage tasks={tasks} onStart={() => setPage("vectorization")} />;
      case "license":
        return <LicensePage client={client} license={license} version={version} onLicenseChanged={setLicense} />;
      case "diagnostics":
        return <DiagnosticsPage status={status} version={version} onRestart={restart} onOpenLogs={() => client.openLogsDirectory()} />;
    }
  };

  return (
    <AppShell currentPage={page} onNavigate={setPage} status={status} license={license} version={version}>
      {renderPage()}
    </AppShell>
  );
}
