// @vitest-environment node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, test } from 'vitest';

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.resolve(currentDir, '..');
const frontendDir = path.resolve(srcDir, '..');
const repoDir = path.resolve(frontendDir, '..');

describe('repository hygiene', () => {
  test('does not keep legacy compatibility wrappers', () => {
    expect(fs.existsSync(path.join(srcDir, 'services', 'api.ts'))).toBe(false);
    expect(fs.existsSync(path.join(srcDir, 'app', 'providers', 'useAuth.ts'))).toBe(false);
  });

  test('does not keep the orphan high-level document at repo root', () => {
    expect(fs.existsSync(path.join(repoDir, 'DOCUMENTACAO_ALTO_NIVEL.md'))).toBe(false);
  });
});
