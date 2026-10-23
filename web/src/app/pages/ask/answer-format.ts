/**
 * Turns the model's answer into blocks the template renders without innerHTML: paragraphs and
 * lists made of text, `code`, **bold**, *italics* and [n] citations ([1, 2] and [1][2] both work).
 * Underscores are left alone: they are part of names like __post_init__.
 */

export type Inline =
  | { kind: 'text'; value: string }
  | { kind: 'code'; value: string }
  | { kind: 'strong'; value: string }
  | { kind: 'em'; value: string }
  | { kind: 'cite'; n: number };

export type Block = { kind: 'p'; inlines: Inline[] } | { kind: 'ul' | 'ol'; items: Inline[][] };

const INLINE = /`([^`]+)`|\*\*([^*]+)\*\*|\*([^*\s](?:[^*]*[^*\s])?)\*|\[(\d+(?:\s*,\s*\d+)*)\]/g;
const BULLET = /^\s*[-*•]\s+/;
const NUMBERED = /^\s*\d+[.)]\s+/;

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  let last = 0;
  for (const match of text.matchAll(INLINE)) {
    const index = match.index ?? 0;
    if (index > last) out.push({ kind: 'text', value: text.slice(last, index) });
    const [, code, strong, em, cites] = match;
    if (code !== undefined) out.push({ kind: 'code', value: code });
    else if (strong !== undefined) out.push({ kind: 'strong', value: strong });
    else if (em !== undefined) out.push({ kind: 'em', value: em });
    else for (const n of cites.split(',')) out.push({ kind: 'cite', n: Number(n.trim()) });
    last = index + match[0].length;
  }
  if (last < text.length) out.push({ kind: 'text', value: text.slice(last) });
  return out;
}

export function parseAnswer(answer: string): Block[] {
  const blocks: Block[] = [];
  // Consecutive plain lines join into one paragraph; consecutive list lines into one list.
  let paragraph: string[] = [];
  let list: Extract<Block, { kind: 'ul' | 'ol' }> | null = null;

  const close = () => {
    if (paragraph.length) blocks.push({ kind: 'p', inlines: parseInline(paragraph.join(' ')) });
    if (list) blocks.push(list);
    paragraph = [];
    list = null;
  };

  for (const line of answer.trim().split('\n')) {
    if (!line.trim()) {
      close(); // a blank line ends the block
      continue;
    }
    const kind = BULLET.test(line) ? 'ul' : NUMBERED.test(line) ? 'ol' : null;
    if (!kind) {
      if (list) close();
      paragraph.push(line.trim());
      continue;
    }
    const current: Extract<Block, { kind: 'ul' | 'ol' }> | null = list;
    if (paragraph.length || current?.kind !== kind) close();
    const target: Extract<Block, { kind: 'ul' | 'ol' }> = list ?? { kind, items: [] };
    target.items.push(parseInline(line.replace(kind === 'ul' ? BULLET : NUMBERED, '')));
    list = target;
  }
  close();
  return blocks;
}
