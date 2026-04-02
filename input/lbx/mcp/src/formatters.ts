interface TaskData {
  id: string;
  custom_id?: string;
  name: string;
  description?: string;
  text_content?: string;
  status?: { status: string };
  priority?: { priority: string } | null;
  assignees?: Array<{ username: string; email?: string }>;
  tags?: Array<{ name: string }>;
  due_date?: string | null;
  start_date?: string | null;
  date_created?: string;
  date_updated?: string;
  list?: { name: string; id: string };
  custom_fields?: Array<{ name: string; value?: unknown }>;
  subtasks?: TaskData[];
  url?: string;
}

type CommentOp =
  | { text: string; attributes?: Record<string, unknown> }
  | { image: string };

interface CommentData {
  comments: Array<{
    comment_text: string;
    comment: CommentOp[];
    user: { username: string };
    date: string;
  }>;
}

function ts(ms: string | null | undefined): string {
  if (!ms) return "—";
  return new Date(Number(ms)).toISOString().slice(0, 10);
}

export function formatTask(raw: unknown): string {
  const t = raw as TaskData;
  const lines: string[] = [
    `# ${t.name}`,
    `**ID:** ${t.custom_id || t.id}  `,
    `**Status:** ${t.status?.status ?? "unknown"}  `,
    `**Priority:** ${t.priority?.priority ?? "none"}  `,
    `**Assignees:** ${t.assignees?.map((a) => a.username).join(", ") || "unassigned"}  `,
    `**Tags:** ${t.tags?.map((tag) => tag.name).join(", ") || "none"}  `,
    `**List:** ${t.list?.name ?? "—"} (${t.list?.id ?? ""})  `,
    `**Created:** ${ts(t.date_created)} | **Updated:** ${ts(t.date_updated)}  `,
    `**Due:** ${ts(t.due_date)} | **Start:** ${ts(t.start_date)}  `,
  ];

  if (t.url) lines.push(`**URL:** ${t.url}  `);

  if (t.text_content) {
    lines.push("", "## Description", t.text_content);
  } else if (t.description) {
    lines.push("", "## Description", t.description);
  }

  if (t.custom_fields?.length) {
    lines.push("", "## Custom Fields");
    for (const cf of t.custom_fields) {
      const val = cf.value !== undefined && cf.value !== null ? String(cf.value) : "—";
      lines.push(`- **${cf.name}:** ${val}`);
    }
  }

  if (t.subtasks?.length) {
    lines.push("", "## Subtasks");
    for (const st of t.subtasks) {
      lines.push(`- [${st.status?.status ?? "?"}] ${st.name} (${st.custom_id || st.id})`);
    }
  }

  return lines.join("\n");
}

interface TaskListItem {
  id: string;
  custom_id?: string;
  name: string;
  status?: { status: string };
  tags?: Array<{ name: string }>;
  date_created?: string;
  date_updated?: string;
  date_closed?: string | null;
  time_spent?: number;
  url?: string;
  text_content?: string;
}

export function formatTaskList(tasks: unknown[]): string {
  const items = tasks as TaskListItem[];
  const lines: string[] = [
    `**${items.length} tasks returned**\n`,
  ];

  for (const t of items) {
    const id = t.custom_id || t.id;
    const status = t.status?.status ?? "?";
    const hours = t.time_spent ? (t.time_spent / 3600000).toFixed(1) : "0";
    const tags = t.tags?.map((tag) => tag.name).join(", ") || "";
    lines.push(`- **${id}** [${status}] ${t.name} (${hours}h)${tags ? ` [${tags}]` : ""}`);
  }

  return lines.join("\n");
}

function renderCommentOps(ops: CommentOp[]): string {
  return ops
    .map((op) => {
      if ("image" in op) return `![image](${op.image})`;
      return op.text ?? "";
    })
    .join("");
}

export function formatComments(raw: unknown): string {
  const data = raw as CommentData;
  if (!data.comments?.length) return "_No comments._";

  return data.comments
    .map((c) => {
      const date = ts(c.date);
      const body = Array.isArray(c.comment) && c.comment.length
        ? renderCommentOps(c.comment)
        : c.comment_text;
      return `**${c.user.username}** (${date}):\n${body}`;
    })
    .join("\n\n---\n\n");
}
