export type CodexEventType =
  | "system"
  | "plan"
  | "tool"
  | "diff"
  | "thought"
  | "status"
  | "final"
  | "cancelled"
  | "error";

export type CodexEvent = {
  type: CodexEventType;
  content: string;
  meta?: Record<string, unknown>;
  ts?: number;
};

export type ModelInfo = {
  name: string;
  type?: string;
  runtime?: string;
  endpoint?: string | null;
  context?: number;
  tools?: boolean;
};
