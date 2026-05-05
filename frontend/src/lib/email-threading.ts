import createDOMPurify from "dompurify";

export interface ThreadEmailData {
  id: number;
  subject: string | null;
  sender: string;
  reply_to?: string | null;
  body: string;
  date?: string | null;
  thread_id?: string | null;
  message_id?: string | null;
  in_reply_to?: string | null;
  references?: string | null;
}

export interface ReplyPayload {
  to: string;
  subject: string;
  body: string;
  in_reply_to?: string;
  references?: string;
}

const HTML_ENTITY_MAP: Record<string, string> = {
  amp: "&",
  gt: ">",
  lt: "<",
  nbsp: " ",
  quot: '"',
  apos: "'",
};

const TEXT_ONLY_HTML_SANITIZER_CONFIG = {
  ALLOWED_ATTR: [],
  ALLOWED_TAGS: [],
  KEEP_CONTENT: true,
};

const ENCODED_NULL_BYTE_PATTERN = /%00/gi;
const NON_TEXT_HTML_SELECTORS = "script,style,template,iframe,object,embed";
const NON_TEXT_HTML_TAGS = new Set(["script", "style", "template", "iframe", "object", "embed"]);
let browserSanitizer: ReturnType<typeof createDOMPurify> | null = null;

function getBrowserSanitizer(): ReturnType<typeof createDOMPurify> | null {
  if (typeof window === "undefined") return null;

  browserSanitizer ??= createDOMPurify(window);
  return browserSanitizer;
}

function extractHtmlTextContent(value: string): string {
  const parsedDocument = new window.DOMParser().parseFromString(value, "text/html");

  parsedDocument
    .querySelectorAll(NON_TEXT_HTML_SELECTORS)
    .forEach((node) => node.remove());

  return parsedDocument.body.textContent ?? "";
}

function encodeMarkupDelimiters(value: string): string {
  return value.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function isHtmlNameCharacter(value: string): boolean {
  const codePoint = value.codePointAt(0);
  if (codePoint === undefined) return false;

  return (
    (codePoint >= 48 && codePoint <= 57) ||
    (codePoint >= 65 && codePoint <= 90) ||
    (codePoint >= 97 && codePoint <= 122) ||
    value === ":" ||
    value === "-"
  );
}

function readHtmlTagName(rawTag: string): string {
  let index = rawTag.startsWith("/") ? 1 : 0;

  while (rawTag[index] === " " || rawTag[index] === "\t" || rawTag[index] === "\n") {
    index += 1;
  }

  const startIndex = index;
  while (index < rawTag.length && isHtmlNameCharacter(rawTag[index])) {
    index += 1;
  }

  return rawTag.slice(startIndex, index).toLowerCase();
}

function stripHtmlMarkupForServerFallback(value: string): string {
  let result = "";
  let index = 0;
  let blockedTag: string | null = null;

  while (index < value.length) {
    const character = value[index];

    if (character !== "<") {
      if (!blockedTag) result += character;
      index += 1;
      continue;
    }

    if (value.startsWith("<!--", index)) {
      const commentEndIndex = value.indexOf("-->", index + 4);
      index = commentEndIndex === -1 ? value.length : commentEndIndex + 3;
      continue;
    }

    const tagEndIndex = value.indexOf(">", index + 1);
    if (tagEndIndex === -1) break;

    const rawTag = value.slice(index + 1, tagEndIndex).trim();
    const tagName = readHtmlTagName(rawTag);
    const isClosingTag = rawTag.startsWith("/");

    if (blockedTag) {
      if (isClosingTag && tagName === blockedTag) blockedTag = null;
      index = tagEndIndex + 1;
      continue;
    }

    if (!isClosingTag && NON_TEXT_HTML_TAGS.has(tagName)) {
      blockedTag = tagName;
    }

    index = tagEndIndex + 1;
  }

  return result;
}

function normalizeSanitizedEmailText(value: string): string {
  return decodeHtmlEntities(value, { decodeMarkupDelimiters: false })
    .replace(/\r\n/g, "\n")
    .replace(/[\t ]+\n/g, "\n")
    .replace(/[\t ]{2,}/g, " ")
    .trim();
}

function decodeHtmlEntities(
  value: string,
  options: { decodeMarkupDelimiters?: boolean } = {},
): string {
  const decodeMarkupDelimiters = options.decodeMarkupDelimiters ?? true;

  return value.replace(/&(#x[\da-f]+|#\d+|[a-z]+);/gi, (entity, rawName: string) => {
    const name = rawName.toLowerCase();

    if (name.startsWith("#x")) {
      const codePoint = Number.parseInt(name.slice(2), 16);
      if (!decodeMarkupDelimiters && (codePoint === 60 || codePoint === 62)) return entity;
      return Number.isInteger(codePoint) && codePoint >= 0 && codePoint <= 0x10ffff
        ? String.fromCodePoint(codePoint)
        : entity;
    }

    if (name.startsWith("#")) {
      const codePoint = Number.parseInt(name.slice(1), 10);
      if (!decodeMarkupDelimiters && (codePoint === 60 || codePoint === 62)) return entity;
      return Number.isInteger(codePoint) && codePoint >= 0 && codePoint <= 0x10ffff
        ? String.fromCodePoint(codePoint)
        : entity;
    }

    if (!decodeMarkupDelimiters && (name === "lt" || name === "gt")) return entity;

    return HTML_ENTITY_MAP[name] ?? entity;
  });
}

export function sanitizeEmailText(value?: string | null): string {
  if (!value) return "";

  const decodedText = decodeHtmlEntities(value)
    .replace(ENCODED_NULL_BYTE_PATTERN, "")
    .replace(/\u0000/g, "");
  const sanitizer = getBrowserSanitizer();
  if (!sanitizer) {
    return normalizeSanitizedEmailText(
      encodeMarkupDelimiters(stripHtmlMarkupForServerFallback(decodedText)),
    );
  }

  const textOnlyContent = encodeMarkupDelimiters(extractHtmlTextContent(decodedText));
  const withoutTags = sanitizer.sanitize(textOnlyContent, TEXT_ONLY_HTML_SANITIZER_CONFIG);

  return normalizeSanitizedEmailText(withoutTags);
}

function extractMailbox(value: string): string {
  const angleMatch = value.match(/<([^>]+)>/);
  return (angleMatch?.[1] ?? value).trim();
}

function buildReferences(email: ThreadEmailData): string | undefined {
  const references = email.references?.trim();
  const messageId = email.message_id?.trim();

  if (!references) return messageId || undefined;
  if (!messageId) return references;

  const normalizedMessageId = messageId.replace(/^<|>$/g, "");
  const referenceTokens =
    references.match(/<[^>]+>/g)?.map((token) => token.replace(/^<|>$/g, "")) ??
    references.split(/\s+/).map((token) => token.replace(/^<|>$/g, ""));

  if (referenceTokens.includes(normalizedMessageId)) return references;

  return `${references} ${messageId}`;
}

export function formatEmailDate(value?: string | null): string {
  if (!value) return "Unknown date";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown date";

  return date.toLocaleString();
}

export function buildThreadUrl(apiUrl: string, threadId: string): string {
  return `${apiUrl}/api/emails/thread/${encodeURIComponent(threadId)}`;
}

export function getConversationMessages<T extends ThreadEmailData>(
  selectedEmail: T,
  threadEmails: T[],
): T[] {
  const hasSelectedEmail = threadEmails.some(
    (threadEmail) =>
      threadEmail.id === selectedEmail.id ||
      (!!selectedEmail.message_id && threadEmail.message_id === selectedEmail.message_id),
  );

  return hasSelectedEmail ? threadEmails : [selectedEmail];
}

export function buildReplyPayload(
  email: ThreadEmailData,
  draft: string,
): ReplyPayload {
  const to = email.reply_to?.trim()
    ? extractMailbox(email.reply_to)
    : extractMailbox(email.sender);
  const subject = email.subject?.startsWith("Re:")
    ? email.subject
    : `Re: ${email.subject || ""}`;
  const references = buildReferences(email);

  return {
    to,
    subject,
    body: draft,
    in_reply_to: email.message_id || undefined,
    references,
  };
}
