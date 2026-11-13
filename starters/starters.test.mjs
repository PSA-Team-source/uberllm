// node starters.test.mjs          every starter has what the README promises
// node starters.test.mjs --live   also: the badge and every public link answer
// (run --live after the folder is pushed to github.com/PSA-Team-source/uberllm and
// before the docs page that links to it ships)
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const read = (...p) => readFileSync(join(root, ...p), 'utf8');
const REPO = 'https://github.com/PSA-Team-source/uberllm/tree/main/starters';
const BADGE = /https:\/\/api\.uberllm\.dev\/api\/v1\/public\/badge\/([a-z0-9.-]+\/[a-z0-9.-]+)\.svg/g;
// smoke = the command the README names; pins = the file whose versions must be exact
const STARTERS = {
  'nextjs-ai-sdk-chat': { smoke: 'smoke.test.mts', pins: 'package.json', lock: true },
  'langgraph-agent': { smoke: 'test_agent.py', pins: 'requirements.txt' },
  'crewai-crew': { smoke: 'test_crew.py', pins: 'requirements.txt' },
  'tool-agent-cli': { smoke: 'agent.test.ts', pins: 'package.json', lock: true },
};

const dirs = readdirSync(root).filter((n) => statSync(join(root, n)).isDirectory());
assert.deepEqual(dirs.sort(), Object.keys(STARTERS).sort(), 'every starter folder is listed here and in the README');

const walk = (dir) =>
  readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)],
  );

// Every badge links to its model page with the utm the embed docs use, so a visit
// from someone's README is counted as badge traffic (docs/embed.md, web/lib/embed.ts badgeMarkdown).
const BADGE_UTM = 'utm_source=embed&utm_medium=referral&utm_campaign=price-badge';
function badgeLinksCounted(text, where) {
  for (const [, id] of text.matchAll(BADGE)) {
    const page = `https://uberllm.dev/models/${id}?`;
    const md = text.includes(`${id}.svg)](${page}${BADGE_UTM})`);
    const html = text.includes(`<a href="${page}${BADGE_UTM.replaceAll('&', '&amp;')}"`);
    assert.ok(md || html, `${where}: the ${id} badge links to its model page with ${BADGE_UTM}`);
  }
  assert.ok(!/uberllm\.dev\/models\/[a-z0-9.\/-]+[)"]/.test(text.split('\n').filter((l) => l.includes('/public/badge/')).join('\n')), `${where}: a badge link has no utm`);
}
const index = read('README.md');
badgeLinksCounted(index, 'starters/README.md');
for (const doc of ['starters.md', 'price-api.md']) badgeLinksCounted(readFileSync(join(root, '..', 'docs', doc), 'utf8'), `docs/${doc}`);
for (const [name, s] of Object.entries(STARTERS)) {
  const at = (f) => join(root, name, f);
  assert.ok(index.includes(`(${name})`), `${name}: linked from starters/README.md`);
  for (const junk of ['node_modules', '.venv', '.next', '.env', '.env.local']) {
    assert.ok(!existsSync(at(junk)), `${name}: ${junk} must not be left in the folder`);
  }

  const readme = read(name, 'README.md');
  assert.ok([...readme.matchAll(BADGE)].length >= 1, `${name}: README has the live price badge`);
  badgeLinksCounted(readme, `${name}/README.md`);
  assert.match(readme, /## Quick start\n\n1\. [^]+\n2\. [^]+\n3\. /, `${name}: README has a 3-step quick start`);
  assert.ok(!/\n4\. /.test(readme.split('## Quick start')[1].split('\n## ')[0]), `${name}: quick start is 3 steps`);
  assert.ok(readme.includes(`npx degit PSA-Team-source/uberllm/starters/${name} `), `${name}: copy command names this folder`);
  assert.ok(existsSync(at(s.smoke)) && readme.includes(s.smoke), `${name}: smoke test exists and the README names it`);

  // Each starter is copied by itself (degit), so it carries its own .gitignore
  // and the key file can never be committed by a plain `git add .`.
  const ignore = read(name, '.gitignore');
  for (const line of ['.env', s.lock ? 'node_modules/' : '.venv/', ...(name.startsWith('nextjs') ? ['.env.local', '.next/'] : [])]) {
    assert.ok(ignore.split('\n').includes(line), `${name}: .gitignore lists ${line}`);
  }
  // The price a starter quotes is the price the model page and the badge show.
  assert.ok(!/\/models\/\$?\{|input_usd|output_usd/.test(walk(join(root, name)).filter((f) => /\.(ts|mts|tsx|py)$/.test(f)).map((f) => readFileSync(f, 'utf8')).join('\n')), `${name}: prices come from /api/v1/public/prices`);

  // .env.example: the key line is empty.
  const env = read(name, '.env.example');
  assert.match(env, /^UBERLLM_API_KEY=$/m, `${name}: .env.example leaves the key empty`);

  // Exact versions only.
  const pins = read(name, s.pins);
  if (s.pins === 'package.json') {
    const pkg = JSON.parse(pins);
    for (const [dep, v] of Object.entries({ ...pkg.dependencies, ...pkg.devDependencies })) {
      assert.match(v, /^\d+\.\d+\.\d+$/, `${name}: ${dep} is pinned to an exact version (got ${v})`);
    }
    if (s.lock) assert.ok(existsSync(at('package-lock.json')), `${name}: package-lock.json is committed`);
  } else {
    for (const line of pins.split('\n').filter((l) => l.trim() && !l.startsWith('#'))) {
      assert.match(line, /^[a-z0-9-]+==\d+(\.\d+)+$/, `${name}: "${line}" is pinned with ==`);
    }
  }

  for (const file of walk(join(root, name))) {
    if (file.endsWith('package-lock.json')) continue;
    const text = readFileSync(file, 'utf8');
    // No real key in any file (keys are ull_ + a long random part).
    assert.ok(!/ull_[A-Za-z0-9_-]{20,}/.test(text), `${file}: looks like a real API key`);
    // The key may only go to api.uberllm.dev: code never reads a base URL from the environment.
    assert.ok(!/(OPENAI|UBERLLM)_(BASE_URL|API_BASE)['"\]]/.test(text) || file.endsWith('.md'), `${file}: base URL must not come from the environment`);
  }
  const code = walk(join(root, name)).filter((f) => /\.(ts|tsx|py)$/.test(f)).map((f) => readFileSync(f, 'utf8')).join('\n');
  assert.ok(code.includes('https://api.uberllm.dev/v1'), `${name}: sets the UberLLM base URL in code`);
}
console.log(`starters ok (${Object.keys(STARTERS).length} starters)`);

if (process.argv.includes('--live')) {
  const docs = join(root, '..', 'docs', 'starters.md');
  const text = [index, ...Object.keys(STARTERS).map((n) => read(n, 'README.md')), existsSync(docs) ? readFileSync(docs, 'utf8') : ''].join('\n');
  const urls = new Set([
    ...Object.keys(STARTERS).map((n) => `${REPO}/${n}`),
    ...[...text.matchAll(/https:\/\/(?:github\.com|uberllm\.dev|api\.uberllm\.dev)\/[^\s)>"'`]*/g)]
      .map((m) => m[0].replace(/[.,]$/, ''))
      .filter((u) => !u.includes('<') && !u.endsWith('/v1') && !u.includes('/public/prices?model=')),
    'https://api.uberllm.dev/api/v1/public/prices?model=deepseek/deepseek-v4-flash',
  ]);
  const bad = [];
  for (const url of urls) {
    const res = await fetch(url, { redirect: 'follow' }).catch((e) => ({ status: String(e.cause?.code ?? e.message), headers: new Headers() }));
    const svg = !url.endsWith('.svg') || (res.headers.get('content-type') ?? '').includes('image/svg+xml');
    if (res.status !== 200 || !svg) bad.push(`${res.status} ${url}`);
  }
  assert.deepEqual(bad, [], 'public links that do not answer');
  console.log(`live ok (${urls.size} links)`);
}
