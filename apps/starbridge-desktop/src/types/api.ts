export type RuntimeState =
  | "starting"
  | "connected"
  | "offline"
  | "recovering"
  | "failed";

export interface RuntimeStatus {
  state: RuntimeState;
  message: string;
  backendPid?: number;
  port?: number;
  recoveryAttempts: number;
  technicalDetails?: string;
}

export interface VersionInfo {
  desktop: string;
  backend?: string;
}

export type CodexConnectionState =
  | "not_found"
  | "connector_required"
  | "awaiting_pairing"
  | "paired"
  | "error";

export type CreativeApplicationState =
  | "not_installed"
  | "installed"
  | "running"
  | "bridge_ready"
  | "unavailable";

export type CreativeApplicationPairingState =
  | "not_available"
  | "open_required"
  | "ready_to_pair"
  | "paired"
  | "paired_limited"
  | "reconnect_required"
  | "unavailable";

export interface CodexConnection {
  state: CodexConnectionState;
  app_available: boolean;
  connector_configured: boolean;
  session_paired: boolean;
  pairing_code: string;
  message: string;
  next_steps: string[];
}

export interface CreativeApplicationConnection {
  id: string;
  name: string;
  mark: string;
  state: CreativeApplicationState;
  installed: boolean;
  running: boolean;
  bridge_available: boolean;
  managed: boolean;
  message: string;
  pairing_state: CreativeApplicationPairingState;
  paired: boolean;
  adapter_kind: "com" | "http" | "process";
  control_level: "verified_bridge" | "session_detection";
  capabilities: string[];
  next_steps: string[];
  last_connected_at?: string;
  version?: string;
}

export interface ConnectionOverview {
  schema_version: "starbridge.desktop-connections.v2";
  checked_at: string;
  drawing_enabled: boolean;
  codex: CodexConnection;
  applications: CreativeApplicationConnection[];
  safety: {
    loopback_only: true;
    credentials_read: false;
    external_apps_force_restarted: false;
  };
}

export interface CodexConnectorInstallResult {
  installed: boolean;
  connector: string;
  message: string;
  restart_required: boolean;
  next_steps: string[];
}

export interface CodexConnectionResetResult {
  reset: boolean;
  pairing_code: string;
}

export interface SoftwareUpdateStatus {
  configured: boolean;
  source: string;
  currentVersion: string;
  available: boolean;
  version?: string;
  notes?: string;
  publishedAt?: string;
  signatureRequired: boolean;
  automaticChecksSupported: boolean;
}

export type SoftwareUpdateProgress =
  | { event: "started"; data: { contentLength?: number } }
  | {
      event: "progress";
      data: {
        chunkLength: number;
        downloadedBytes: number;
        contentLength?: number;
      };
    }
  | { event: "verified" }
  | { event: "installing" };

export type LicenseState = "community" | "active" | "invalid";
export type LicenseEdition = "community" | "pro" | "enterprise";

export interface LicenseStatus {
  state: LicenseState;
  edition: LicenseEdition;
  message: string;
  licenseId?: string;
  issuedOn?: string;
  perpetual?: boolean;
  currentDeviceMatched?: boolean;
  deviceLimit: number;
  features: string[];
  commercialVerifierConfigured: boolean;
  reason?: string;
}

export interface LicenseRequestReceipt {
  requestId: string;
  fileName: string;
  location: string;
  folderOpened: boolean;
}

export type VectorMode = "artisan" | "smart" | "lightweight" | "exact";
export type VectorJobState = "queued" | "running" | "completed" | "failed";

export interface VectorSelection {
  selectionId: string;
  fileName: string;
  width: number;
  height: number;
  sourceHash: string;
  previewDataUrl: string;
}

export interface VectorMetrics {
  colors: number;
  subpaths: number;
  points: number;
  svgBytes: number;
  elapsedSeconds: number;
  pixelMatch?: boolean | null;
  anchorReductionRatio?: number | null;
}

export interface VectorJobResult {
  modeLabel: string;
  sourceHash: string;
  sourcePreviewDataUrl: string;
  resultPreviewDataUrl: string;
  metrics: VectorMetrics;
  warnings: string[];
  outputAvailable: boolean;
}

export interface VectorJobError {
  code: string;
  message: string;
  nextSteps: string[];
}

export interface VectorJob {
  jobId: string;
  status: VectorJobState;
  progress: number;
  stage: string;
  mode: VectorMode;
  createdAt: string;
  completedAt?: string;
  result?: VectorJobResult;
  error?: VectorJobError;
}

export interface VectorHistoryEvent {
  eventId: string;
  createdAt: string;
  mode: VectorMode;
  summary: string;
  sourceHash: string;
  metrics: VectorMetrics;
  outputAvailable: boolean;
}

export interface VectorHistory {
  eventCount: number;
  events: VectorHistoryEvent[];
}

export interface VectorizationStart {
  selectionId: string;
  mode: VectorMode;
  parameters: Record<string, number>;
  confirmRun: boolean;
  confirmWrite: boolean;
  confirmExport: boolean;
}

export interface ApiErrorShape {
  code?: string;
  message?: string;
  next_steps?: string[];
}

export interface ApiEnvelope<T> {
  ok: boolean;
  data?: T;
  error?: ApiErrorShape | string;
  [key: string]: unknown;
}

export interface TransportResponse<T> {
  status: number;
  body: T;
}

export interface TransportRequest {
  method: "GET" | "POST";
  path: string;
  body?: Record<string, unknown>;
}
