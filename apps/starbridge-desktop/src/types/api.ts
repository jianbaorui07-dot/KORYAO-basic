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
