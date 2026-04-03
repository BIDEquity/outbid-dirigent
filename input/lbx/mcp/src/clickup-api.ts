import { readFile } from "fs/promises";
import { basename } from "path";
import { markdownToComment, ClickUpAttachment } from "./markdown.js";

const BASE_URL = "https://api.clickup.com/api/v2";

export class ClickUpClient {
  private token: string;

  constructor() {
    const token = process.env.CLICKUP_API_TOKEN;
    if (!token) {
      throw new Error("CLICKUP_API_TOKEN environment variable is required");
    }
    this.token = token;
  }

  private async request(
    path: string,
    params?: Record<string, string>,
    options?: { method?: string; body?: unknown },
  ): Promise<unknown> {
    const url = new URL(`${BASE_URL}${path}`);

    if (params) {
      for (const [key, value] of Object.entries(params)) {
        url.searchParams.set(key, value);
      }
    }

    const headers: Record<string, string> = { Authorization: this.token };
    const init: RequestInit = { headers };

    if (options?.method) init.method = options.method;
    if (options?.body !== undefined) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(options.body);
    }

    const res = await fetch(url.toString(), init);

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`ClickUp API ${res.status}: ${body}`);
    }

    return res.json();
  }

  async getTask(customId: string, teamId: string): Promise<unknown> {
    return this.request(`/task/${customId}`, {
      custom_task_ids: "true",
      team_id: teamId,
      include_subtasks: "true",
      include_markdown_description: "true",
    });
  }

  async updateTaskDescription(
    customId: string,
    teamId: string,
    markdownDescription: string,
  ): Promise<unknown> {
    return this.request(
      `/task/${customId}`,
      { custom_task_ids: "true", team_id: teamId },
      { method: "PUT", body: { markdown_description: markdownDescription } },
    );
  }

  async getTaskComments(customId: string, teamId: string): Promise<unknown> {
    return this.request(`/task/${customId}/comment`, {
      custom_task_ids: "true",
      team_id: teamId,
    });
  }

  async addTaskComment(
    customId: string,
    teamId: string,
    commentText: string,
    inlineAttachments?: ClickUpAttachment[],
  ): Promise<unknown> {
    return this.request(
      `/task/${customId}/comment`,
      { custom_task_ids: "true", team_id: teamId },
      { method: "POST", body: { comment: markdownToComment(commentText, inlineAttachments) } },
    );
  }

  async uploadAttachment(
    customId: string,
    teamId: string,
    filePath: string,
  ): Promise<ClickUpAttachment> {
    const fileBuffer = await readFile(filePath);
    const filename = basename(filePath);
    const formData = new FormData();
    formData.append(
      "attachment",
      new Blob([fileBuffer]),
      filename,
    );

    const url = new URL(`${BASE_URL}/task/${customId}/attachment`);
    url.searchParams.set("custom_task_ids", "true");
    url.searchParams.set("team_id", teamId);

    const res = await fetch(url.toString(), {
      method: "POST",
      headers: { Authorization: this.token },
      body: formData,
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`ClickUp API ${res.status}: ${body}`);
    }

    return res.json() as Promise<ClickUpAttachment>;
  }

  async getTasksByList(
    listId: string,
    params?: {
      date_created_gt?: string;
      date_created_lt?: string;
      include_closed?: boolean;
    },
  ): Promise<unknown[]> {
    const allTasks: unknown[] = [];
    let page = 0;

    while (true) {
      const queryParams: Record<string, string> = {
        page: String(page),
        subtasks: "true",
        include_closed: String(params?.include_closed ?? true),
      };

      if (params?.date_created_gt) {
        queryParams.date_created_gt = String(
          new Date(params.date_created_gt).getTime(),
        );
      }
      if (params?.date_created_lt) {
        queryParams.date_created_lt = String(
          new Date(params.date_created_lt).getTime(),
        );
      }

      const result = (await this.request(
        `/list/${listId}/task`,
        queryParams,
      )) as { tasks: unknown[] };

      if (!result.tasks || result.tasks.length === 0) break;

      allTasks.push(...result.tasks);
      if (result.tasks.length < 100) break;
      page++;
    }

    return allTasks;
  }
}
