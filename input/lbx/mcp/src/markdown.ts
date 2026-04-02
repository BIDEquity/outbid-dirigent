export type CommentItem =
  | { text: string; attributes?: Record<string, unknown> }
  | { type: "image"; text: string; image: Record<string, unknown>; attributes: Record<string, unknown> };

export interface ClickUpAttachment {
  id: string;
  version: string;
  date: number;
  name: string;
  title: string;
  extension: string;
  source: number;
  thumbnail_small: string;
  thumbnail_medium: string;
  thumbnail_large: string;
  width: number;
  height: number;
  url: string;
  url_w_query: string;
  url_w_host: string;
}

function buildAttachmentImageOp(attachment: ClickUpAttachment): CommentItem {
  const ext = attachment.extension; // e.g. "png"
  const mimeType = `image/${ext}`;

  const dataAttachment = {
    id: attachment.id,
    version: attachment.version,
    date: attachment.date,
    name: attachment.name,
    title: attachment.title,
    extension: ext,
    source: attachment.source,
    thumbnail_small: attachment.thumbnail_small,
    thumbnail_medium: attachment.thumbnail_medium,
    thumbnail_large: attachment.thumbnail_large,
    width: attachment.width,
    height: attachment.height,
    url: attachment.url,
    url_w_query: attachment.url_w_query,
    url_w_host: attachment.url_w_host,
  };

  return {
    type: "image",
    text: attachment.name,
    image: {
      id: attachment.id,
      name: attachment.name,
      title: attachment.title,
      type: ext,
      extension: mimeType,
      thumbnail_large: attachment.thumbnail_large,
      thumbnail_medium: attachment.thumbnail_medium,
      thumbnail_small: attachment.thumbnail_small,
      url: attachment.url,
      uploaded: true,
    },
    attributes: {
      width: "300",
      "data-id": attachment.id,
      "data-attachment": JSON.stringify(dataAttachment),
      "data-natural-width": String(attachment.width),
      "data-natural-height": String(attachment.height),
    },
  };
}

/**
 * Parse inline markdown (bold, italic, code, links, strikethrough, images)
 * into ClickUp comment items (Quill Delta format).
 */
function parseInline(
  text: string,
  items: CommentItem[],
  attachmentsByUrl?: Map<string, ClickUpAttachment>,
): void {
  // Image must come before link; bold before italic so ** is matched before *
  const re =
    /!\[.*?\]\((.+?)\)|\*\*(.+?)\*\*|__(.+?)__|~~(.+?)~~|\*(.+?)\*|_(.+?)_|`(.+?)`|\[(.+?)\]\((.+?)\)/g;
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = re.exec(text)) !== null) {
    if (m.index > last) items.push({ text: text.slice(last, m.index) });

    if (m[1]) {
      // inline image: ![alt](url)
      const url = m[1];
      const attachment = attachmentsByUrl?.get(url);
      if (attachment) {
        items.push(buildAttachmentImageOp(attachment));
      } else {
        // fallback: plain image op (may not render in ClickUp UI)
        items.push({ type: "image", text: url, image: { url, uploaded: false }, attributes: { width: "300" } });
      }
    } else if (m[2] ?? m[3]) {
      items.push({ text: m[2] ?? m[3], attributes: { bold: true } });
    } else if (m[4]) {
      items.push({ text: m[4], attributes: { strike: true } });
    } else if (m[5] ?? m[6]) {
      items.push({ text: m[5] ?? m[6], attributes: { italic: true } });
    } else if (m[7]) {
      items.push({ text: m[7], attributes: { code: true } });
    } else if (m[8] && m[9]) {
      items.push({ text: m[8], attributes: { link: m[9] } });
    }

    last = m.index + m[0].length;
  }

  if (last < text.length) items.push({ text: text.slice(last) });
}

/**
 * Convert a markdown string into ClickUp's comment rich-text format
 * (array of Quill Delta items). Pass attachment metadata so that
 * ![alt](url) references are converted to proper inline image ops.
 */
export function markdownToComment(
  md: string,
  attachments?: ClickUpAttachment[],
): CommentItem[] {
  const attachmentsByUrl = attachments?.length
    ? new Map(attachments.map((a) => [a.url, a]))
    : undefined;

  const items: CommentItem[] = [];
  const lines = md.split("\n");
  let inCode = false;

  for (const line of lines) {
    // fenced code block toggle
    if (line.startsWith("```")) {
      inCode = !inCode;
      continue;
    }

    if (inCode) {
      items.push({ text: line });
      items.push({ text: "\n", attributes: { "code-block": true } });
      continue;
    }

    // header
    const hdr = line.match(/^(#{1,6})\s+(.*)/);
    if (hdr) {
      parseInline(hdr[2], items, attachmentsByUrl);
      items.push({ text: "\n", attributes: { header: hdr[1].length } });
      continue;
    }

    // unordered list
    const ul = line.match(/^[-*]\s+(.*)/);
    if (ul) {
      parseInline(ul[1], items, attachmentsByUrl);
      items.push({ text: "\n", attributes: { list: "bullet" } });
      continue;
    }

    // ordered list
    const ol = line.match(/^\d+\.\s+(.*)/);
    if (ol) {
      parseInline(ol[1], items, attachmentsByUrl);
      items.push({ text: "\n", attributes: { list: "ordered" } });
      continue;
    }

    // blockquote
    const bq = line.match(/^>\s?(.*)/);
    if (bq) {
      parseInline(bq[1], items, attachmentsByUrl);
      items.push({ text: "\n", attributes: { blockquote: true } });
      continue;
    }

    // regular line
    parseInline(line, items, attachmentsByUrl);
    items.push({ text: "\n" });
  }

  return items;
}
