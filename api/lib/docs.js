import fs from 'node:fs/promises';
import path from 'node:path';

export function slugify(value) {
  return String(value)
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export async function loadReferenceDoc() {
  const docPath = path.join(process.cwd(), '..', 'docs', 'v2', 'api-reference.md');
  const markdown = await fs.readFile(docPath, 'utf8');
  const lines = markdown.split(/\r?\n/);

  const titleLine = lines.find((line) => line.startsWith('# ')) ?? '# API Reference';
  const title = titleLine.replace(/^#\s+/, '').trim();

  let separatorIndex = lines.findIndex((line, index) => index > 0 && line.trim() === '---');
  if (separatorIndex < 0) {
    separatorIndex = 1;
  }

  const introLines = [];
  for (let index = 1; index < separatorIndex; index += 1) {
    const line = lines[index]?.trim();
    if (line) {
      introLines.push(line);
    }
  }

  const body = lines.slice(separatorIndex + 1).join('\n').trim();
  const sections = extractSections(body);

  return {
    title,
    intro: introLines.join(' '),
    body,
    sections,
  };
}

export function extractSections(markdown) {
  const sections = [];
  const lines = String(markdown).split(/\r?\n/);

  for (const line of lines) {
    if (line.startsWith('## ')) {
      const title = line.replace(/^##\s+/, '').trim();
      sections.push({
        title,
        id: slugify(title),
      });
    }
  }

  return sections;
}

export function renderableText(children) {
  if (Array.isArray(children)) {
    return children.map(renderableText).join('');
  }

  if (children === null || children === undefined) {
    return '';
  }

  return String(children);
}
