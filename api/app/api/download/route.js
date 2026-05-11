import fs from 'node:fs/promises';
import path from 'node:path';
import { NextResponse } from 'next/server';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const file = searchParams.get('file') || 'api-reference.md';

  if (file !== 'api-reference.md') {
    return NextResponse.json({ error: 'Unsupported file.' }, { status: 400 });
  }

  const docPath = path.join(process.cwd(), '..', 'docs', 'v2', 'api-reference.md');

  try {
    const content = await fs.readFile(docPath, 'utf8');

    return new NextResponse(content, {
      status: 200,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Content-Disposition': `attachment; filename="${file}"`,
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    return NextResponse.json({ error: 'File not found.' }, { status: 404 });
  }
}
