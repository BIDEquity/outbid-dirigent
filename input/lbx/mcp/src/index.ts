import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { ClickUpClient } from "./clickup-api.js";
import { formatTask, formatComments, formatTaskList } from "./formatters.js";

const server = new McpServer({
  name: "clickup",
  version: "1.0.0",
});

const client = new ClickUpClient();
const TEAM_ID = "36654621";

server.registerTool("get_task", {
  description: "Get full details of a ClickUp task by its custom ID (e.g. 'MP-42'). Returns description, status, assignees, custom fields, and subtasks.",
  inputSchema: {
    custom_id: z.string().describe("The custom task ID (e.g. 'MP-42')"),
  },
  annotations: { readOnlyHint: true },
}, async ({ custom_id }) => {
  const data = await client.getTask(custom_id, TEAM_ID);
  return { content: [{ type: "text", text: formatTask(data) }] };
});

server.registerTool("get_task_comments", {
  description: "Get all comments on a ClickUp task by its custom ID.",
  inputSchema: {
    custom_id: z.string().describe("The custom task ID (e.g. 'MP-42')"),
  },
  annotations: { readOnlyHint: true },
}, async ({ custom_id }) => {
  const data = await client.getTaskComments(custom_id, TEAM_ID);
  return { content: [{ type: "text", text: formatComments(data) }] };
});

server.registerTool("get_tasks", {
  description: "Get all tasks from a ClickUp list with optional date filtering. Auto-paginates. Returns task list with time tracking data.",
  inputSchema: {
    list_id: z.string().describe("The ClickUp list ID"),
    date_created_gt: z.string().optional().describe("Only tasks created after this ISO date (e.g. '2026-01-01')"),
    date_created_lt: z.string().optional().describe("Only tasks created before this ISO date (e.g. '2026-12-31')"),
    include_closed: z.boolean().optional().describe("Include closed tasks (default: true)"),
  },
  annotations: { readOnlyHint: true },
}, async ({ list_id, date_created_gt, date_created_lt, include_closed }) => {
  const tasks = await client.getTasksByList(list_id, {
    date_created_gt,
    date_created_lt,
    include_closed: include_closed ?? true,
  });
  return {
    content: [
      { type: "text", text: formatTaskList(tasks) },
      { type: "text", text: "\n\n---\nRAW_JSON_START\n" + JSON.stringify(tasks) + "\nRAW_JSON_END" },
    ],
  };
});

server.registerTool("update_task_description", {
  description: "Update the description of a ClickUp task by its custom ID. Sets the full markdown description.",
  inputSchema: {
    custom_id: z.string().describe("The custom task ID (e.g. 'MP-42')"),
    markdown_description: z.string().describe("The full markdown description to set on the task"),
  },
}, async ({ custom_id, markdown_description }) => {
  await client.updateTaskDescription(custom_id, TEAM_ID, markdown_description);
  return { content: [{ type: "text", text: `Description updated on ${custom_id}.` }] };
});

server.registerTool("add_task_comment", {
  description: "Add a comment with markdown content to a ClickUp task. Supports inline images: use ![alt](/local/path.png) for local files (auto-uploaded) or ![alt](https://url) with inline_attachments for already-uploaded files.",
  inputSchema: {
    custom_id: z.string().describe("The custom task ID (e.g. 'MP-42')"),
    comment_text: z.string().describe("The comment body (markdown). Use ![alt](/path/to/file.png) to embed local images inline — they are uploaded automatically."),
  },
}, async ({ custom_id, comment_text }) => {
  // Auto-upload any local file paths referenced as ![alt](/path/to/file)
  const localImageRe = /!\[([^\]]*)\]\(([^)]+)\)/g;
  const attachments: import("./markdown.js").ClickUpAttachment[] = [];
  let resolvedText = comment_text;

  const localPaths: Array<{ match: string; alt: string; path: string }> = [];
  for (const m of comment_text.matchAll(localImageRe)) {
    const ref = m[2];
    if (ref.startsWith("/") || ref.startsWith("./") || ref.startsWith("~/")) {
      localPaths.push({ match: m[0], alt: m[1], path: ref });
    }
  }

  for (const { match, alt, path } of localPaths) {
    const attachment = await client.uploadAttachment(custom_id, TEAM_ID, path);
    attachments.push(attachment);
    resolvedText = resolvedText.replace(match, `![${alt}](${attachment.url})`);
  }

  await client.addTaskComment(custom_id, TEAM_ID, resolvedText, attachments);
  return { content: [{ type: "text", text: `Comment added to ${custom_id}.` }] };
});


async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ClickUp MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
