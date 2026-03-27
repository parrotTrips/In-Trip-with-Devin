// @vitest-environment node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, test } from 'vitest';

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.resolve(currentDir, '..');
const featuresDir = path.join(srcDir, 'features');
const legacyPagesDir = path.join(srcDir, 'pages');

function listFiles(dir: string): string[] {
  if (!fs.existsSync(dir)) {
    return [];
  }

  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return listFiles(entryPath);
    }

    return [entryPath];
  });
}

describe('frontend modular architecture', () => {
  test('keeps feature pages independent from legacy src/pages', () => {
    const featurePageFiles = listFiles(featuresDir).filter(file =>
      file.endsWith('.tsx') && file.includes(`${path.sep}pages${path.sep}`)
    );

    const invalidReexports = featurePageFiles.filter(file => {
      const source = fs.readFileSync(file, 'utf8');
      return source.includes('../../../pages/');
    });

    expect(invalidReexports).toEqual([]);
  });

  test('does not keep legacy screen implementations under src/pages', () => {
    const legacyScreenFiles = listFiles(legacyPagesDir).filter(file => file.endsWith('.tsx'));
    expect(legacyScreenFiles).toEqual([]);
  });
});
