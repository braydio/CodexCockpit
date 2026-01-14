// codex-cockpit-desktop/src/lib/workspaceApi.ts
import { apiBase } from "@/lib/api";

export type TreeNode =
  | {
      type: "dir";
      name: string;
      path: string; // "" for root
      children: TreeNode[];
    }
  | {
      type: "file";
      name: string;
      path: string;
    }
  | {
      type: "error";
      name: string;
      path: string;
      message: string;
    };

export type WorkspaceTreeResponse = {
  root: string; // server absolute
  tree: TreeNode;
};

export type WorkspaceFileResponse = {
  root: string;
  path: string; // normalized rel
  abs_path: string;
  size: number;
  truncated: boolean;
  text: string;
};

export async function fetchWorkspaceTree(opts: {
  root: string;
  maxDepth?: number;
  maxEntries?: number;
}): Promise<WorkspaceTreeResponse> {
  const u = new URL(`${apiBase()}/workspace/tree`);
  u.searchParams.set("root", opts.root || ".");
  u.searchParams.set("max_depth", String(opts.maxDepth ?? 5));
  u.searchParams.set("max_entries", String(opts.maxEntries ?? 5000));

  const res = await fetch(u.toString(), { method: "GET" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`workspace tree failed: ${res.status} ${res.statusText} ${text}`);
  }
  return (await res.json()) as WorkspaceTreeResponse;
}

export async function fetchWorkspaceFile(opts: {
  root: string;
  path: string;
  maxBytes?: number;
}): Promise<WorkspaceFileResponse> {
  const u = new URL(`${apiBase()}/workspace/file`);
  u.searchParams.set("root", opts.root || ".");
  u.searchParams.set("path", opts.path);
  u.searchParams.set("max_bytes", String(opts.maxBytes ?? 512000));

  const res = await fetch(u.toString(), { method: "GET" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`workspace file failed: ${res.status} ${res.statusText} ${text}`);
  }
  return (await res.json()) as WorkspaceFileResponse;
}
