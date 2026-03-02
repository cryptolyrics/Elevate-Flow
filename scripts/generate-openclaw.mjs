import path from 'path';
import { fileURLToPath } from 'url';
import { buildGenerated, loadRegistry, validateRegistry, writeGenerated } from './lib/registry.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const { agentsDoc, jobsDoc } = loadRegistry(rootDir);
const validation = validateRegistry(agentsDoc, jobsDoc);

if (!validation.valid) {
  console.error('Registry validation failed:');
  for (const err of validation.errors) {
    console.error(`- ${err}`);
  }
  process.exit(1);
}

const generated = buildGenerated(agentsDoc, jobsDoc);
writeGenerated(rootDir, generated);
console.log('Generated openclaw snapshots from registry.');
