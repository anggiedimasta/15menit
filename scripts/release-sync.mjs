#!/usr/bin/env node
/**
 * Changelog (docs/changelog.md) + semver sync from git.
 *
 * - Default: refresh auto block inside `## [Unreleased]` only (no version bump).
 * - `--release`: cut `## [Unreleased]` → new `## [x.y.z] - date`, bump patch in package.json.
 * - `--if-needed`: like `--release` but only if there are commits in `@{u}..HEAD`;
 *   then `git commit` and exit 1 so the next `git push` ships the release line (pre-push hook).
 * - `--rebuild-recent [N]`: rebuild `## [x.y.z]` sections from last N `chore(release)` commits (default 90);
 *   keeps `## [0.1.0]` baseline. Use when `[Unreleased]` was missing and versions drifted from package.json.
 *
 * Markers in docs/changelog.md: `<!-- changelog:sync-begin -->` … `<!-- changelog:sync-end -->`
 * under `## [Unreleased]` (auto-inserted when missing).
 */
import { execSync, spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __root = join(dirname(fileURLToPath(import.meta.url)), '..');
const CHANGELOG = join(__root, 'docs', 'changelog.md');
const PKG_JSON = join(__root, 'apps', 'web', 'package.json');
const ROOT_PKG_JSON = join(__root, 'package.json');
const MARK_BEGIN = '<!-- changelog:sync-begin -->';
const MARK_END = '<!-- changelog:sync-end -->';

function readPkg() {
  return JSON.parse(readFileSync(PKG_JSON, 'utf8'));
}

function commitUrlBase() {
  try {
    const pkg = readPkg();
    const u = pkg.repository?.url || pkg.repository;
    if (typeof u === 'string') {
      const m = /github\.com[:/]([^/]+\/[^/.]+)/i.exec(u);
      if (m) return `https://github.com/${m[1].replace(/\.git$/, '')}`;
    }
  } catch {
    /* ignore */
  }
  return 'https://github.com/anggiedimasta/15menit';
}

function sh(cmd) {
  return execSync(cmd, { encoding: 'utf8', cwd: __root }).trim();
}

function bumpPatch(version) {
  const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(version);
  if (!m) throw new Error(`package.json version not semver: ${version}`);
  const [, a, b, c] = m;
  return `${a}.${b}.${Number(c) + 1}`;
}

/** @returns {string[]} lines `hash|subject` (spawn avoids `%h` mangling on Windows cmd) */
function commitsForRange(revArgs) {
  /** @type {string[]} */
  const args =
    typeof revArgs === 'string'
      ? ['log', revArgs, '--pretty=format:%h|%s']
      : ['log', ...revArgs, '--pretty=format:%h|%s'];
  const r = spawnSync('git', args, { encoding: 'utf8', cwd: __root });
  if (r.status !== 0) return [];
  const out = r.stdout.trim();
  return out ? out.split('\n').filter(Boolean) : [];
}

/** Commits not yet on upstream (what you are about to push). */
function commitsPendingPush() {
  try {
    const upstream = sh('git rev-parse --abbrev-ref @{u}');
    return commitsForRange([`${upstream}..HEAD`]);
  } catch {
    for (const base of ['origin/master', 'origin/main']) {
      try {
        sh(`git rev-parse ${base}`);
        const mb = sh(`git merge-base HEAD ${base}`);
        return commitsForRange([`${mb}..HEAD`]);
      } catch {}
    }
  }
  return [];
}

/** History window for manual sync when no upstream range. */
function commitsFallback() {
  return commitsForRange(['-80']);
}

function pipeSubject(line) {
  const i = line.indexOf('|');
  return i >= 0 ? line.slice(i + 1).trim() : line;
}

/** Short git hash segment before first `|` in `git log` pretty line. */
function shortHashBeforePipe(line) {
  const i = line.indexOf('|');
  return i >= 0 ? line.slice(0, i).trim() : '';
}

/** Omit automated `chore(release)` lines from changelog bullets when rendering. */
function excludeReleaseSubjects(lines) {
  return lines.filter((l) => !/^chore\(release\):/i.test(pipeSubject(l)));
}

function parseArgs() {
  const rebuildIdx = process.argv.indexOf('--rebuild-recent');
  let rebuildRecent = 0;
  if (rebuildIdx >= 0) {
    const next = process.argv[rebuildIdx + 1];
    rebuildRecent = next && /^\d+$/.test(next) ? Number(next) : 90;
  }
  return {
    dryRun: process.argv.includes('--dry-run'),
    ifNeeded: process.argv.includes('--if-needed'),
    release: process.argv.includes('--release'),
    rebuildRecent,
  };
}

/**
 * @param {string} subject
 * @returns {{ type: string; scope?: string; desc: string } | null}
 */
function parseConventional(subject) {
  const m = /^(\w+)(?:\(([^)]+)\))?:\s*(.+)$/.exec(subject);
  if (!m) return null;
  return { type: m[1], scope: m[2], desc: m[3] };
}

function groupCommits(lines) {
  const base = commitUrlBase();
  /** @type {Record<string, string[]>} */
  const buckets = {
    Added: [],
    Changed: [],
    Fixed: [],
    Deprecated: [],
    Removed: [],
    Security: [],
    Other: [],
  };

  for (const line of lines) {
    const pipe = line.indexOf('|');
    const hash = pipe >= 0 ? line.slice(0, pipe) : '';
    const subject = pipe >= 0 ? line.slice(pipe + 1).trim() : line;
    const link = hash ? `([${hash}](${base}/commit/${hash}))` : '';
    const c = parseConventional(subject);
    const text = c
      ? `${c.scope ? `**${c.scope}** — ` : ''}${c.desc} ${link}`.trim()
      : `${subject} ${link}`.trim();

    if (!c) {
      buckets.Other.push(`- ${text}`);
      continue;
    }
    const t = c.type.toLowerCase();
    if (t === 'feat') buckets.Added.push(`- ${text}`);
    else if (t === 'fix') buckets.Fixed.push(`- ${text}`);
    else if (t === 'sec' || t === 'security')
      buckets.Security.push(`- ${text}`);
    else if (t === 'deprecate' || t === 'deprecated')
      buckets.Deprecated.push(`- ${text}`);
    else if (t === 'remove' || t === 'rm') buckets.Removed.push(`- ${text}`);
    else if (
      [
        'refactor',
        'perf',
        'style',
        'docs',
        'chore',
        'build',
        'ci',
        'test',
      ].includes(t)
    )
      buckets.Changed.push(`- ${text}`);
    else buckets.Other.push(`- ${text}`);
  }

  return buckets;
}

function renderSyncBody(lines) {
  const g = groupCommits(lines);
  const parts = [];
  for (const title of [
    'Added',
    'Changed',
    'Fixed',
    'Deprecated',
    'Removed',
    'Security',
    'Other',
  ]) {
    const items = g[title];
    if (!items?.length) continue;
    parts.push(`### ${title}\n\n${items.join('\n')}\n`);
  }
  if (parts.length === 0) return `_No conventional entries in this range._\n`;
  return `${parts.join('\n')}\n`;
}

const UNRELEASED = '## [Unreleased]';

/** Insert [Unreleased] + sync markers after intro when missing (keeps existing version sections). */
function ensureUnreleasedSection(text) {
  if (text.includes(UNRELEASED)) return text;
  const firstVersion = text.search(/^## \[/m);
  if (firstVersion < 0) {
    return `${text.trimEnd()}\n\n${UNRELEASED}\n\n${MARK_BEGIN}\n\n${MARK_END}\n\n`;
  }
  return `${text.slice(0, firstVersion).trimEnd()}\n\n${UNRELEASED}\n\n${MARK_BEGIN}\n\n${MARK_END}\n\n${text.slice(firstVersion)}`;
}

function ensureMarkers(text) {
  let out = ensureUnreleasedSection(text);
  if (!out.includes(MARK_BEGIN) || !out.includes(MARK_END)) {
    if (!out.includes(UNRELEASED)) {
      return `# Changelog\n\n${UNRELEASED}\n\n${MARK_BEGIN}\n\n${MARK_END}\n\n`;
    }
    return out.replace(
      UNRELEASED,
      `${UNRELEASED}\n\n${MARK_BEGIN}\n\n${MARK_END}`,
    );
  }
  const unreleasedIdx = out.indexOf(UNRELEASED);
  const unreleasedSlice = out.slice(unreleasedIdx);
  if (
    unreleasedSlice.includes(MARK_BEGIN) &&
    unreleasedSlice.includes(MARK_END)
  ) {
    return out;
  }
  return out.replace(
    UNRELEASED,
    `${UNRELEASED}\n\n${MARK_BEGIN}\n\n${MARK_END}`,
  );
}

function replaceSyncBlock(changelogText, innerMd) {
  const re = new RegExp(`${MARK_BEGIN}[\\s\\S]*?${MARK_END}`, 'm');
  const block = `${MARK_BEGIN}\n${innerMd}\n${MARK_END}`;
  const unreleasedIdx = changelogText.indexOf(UNRELEASED);
  if (unreleasedIdx >= 0) {
    const head = changelogText.slice(0, unreleasedIdx);
    const tail = changelogText.slice(unreleasedIdx);
    return head + tail.replace(re, block);
  }
  return changelogText.replace(re, block);
}

/**
 * Move current [Unreleased] body (incl. sync block) to a new version section; reset [Unreleased].
 */
/** @returns {{ version: string; hash: string; isoDate: string }[]} newest first */
function listReleaseCommits(limit) {
  const r = spawnSync(
    'git',
    ['log', '--grep=chore(release)', `-${limit}`, '--pretty=format:%h|%s|%ci'],
    { encoding: 'utf8', cwd: __root },
  );
  if (r.status !== 0) return [];
  /** @type {{ version: string; hash: string; isoDate: string }[]} */
  const out = [];
  for (const line of (r.stdout || '').trim().split('\n').filter(Boolean)) {
    const parts = line.split('|');
    const hash = parts[0] ?? '';
    const subject = parts[1] ?? '';
    const ci = parts[2] ?? '';
    const m = /v(\d+\.\d+\.\d+)/i.exec(subject);
    if (!m || !hash) continue;
    out.push({
      version: m[1],
      hash,
      isoDate: ci.slice(0, 10) || new Date().toISOString().slice(0, 10),
    });
  }
  return out;
}

function buildVersionSectionsFromReleases(releases) {
  let md = '';
  for (let i = 0; i < releases.length; i++) {
    const cur = releases[i];
    const prev = releases[i + 1];
    if (!prev) break;
    const lines = excludeReleaseSubjects(
      commitsForRange([`${prev.hash}..${cur.hash}`]),
    );
    if (lines.length === 0) continue;
    md += `## [${cur.version}] - ${cur.isoDate}\n\n${MARK_BEGIN}\n${renderSyncBody(lines)}${MARK_END}\n\n`;
  }
  return md;
}

function rebuildRecentChangelog(changelogText, limit = 90) {
  const baselineMarker = '## [0.1.0]';
  const baselineIdx = changelogText.indexOf(baselineMarker);
  const baseline =
    baselineIdx >= 0 ? changelogText.slice(baselineIdx).trimStart() : '';
  const introEnd = changelogText.search(/^## \[/m);
  const intro =
    introEnd >= 0
      ? changelogText.slice(0, introEnd).trimEnd()
      : changelogText.trimEnd();
  const sections = buildVersionSectionsFromReleases(listReleaseCommits(limit));
  return `${intro}\n\n${UNRELEASED}\n\n${MARK_BEGIN}\n\n${MARK_END}\n\n${sections}${baseline ? `${baseline}\n` : ''}`;
}

function promoteUnreleased(changelogText, version, isoDate) {
  const marker = UNRELEASED;
  const start = changelogText.indexOf(marker);
  if (start < 0) return changelogText;
  const after = changelogText
    .slice(start + marker.length)
    .replace(/^\s*\n/, '');
  const nextIdx = after.search(/^## \[/m);
  const unreleasedBody =
    nextIdx < 0 ? after.trimEnd() : after.slice(0, nextIdx).trimEnd();
  const remainder = nextIdx < 0 ? '' : after.slice(nextIdx);
  const head = changelogText.slice(0, start);
  return `${head}${marker}\n\n${MARK_BEGIN}\n\n${MARK_END}\n\n## [${version}] - ${isoDate}\n\n${unreleasedBody}\n\n${remainder}`;
}

async function main() {
  const { dryRun, ifNeeded, release, rebuildRecent } = parseArgs();
  const doRelease = release || ifNeeded;

  if (!existsSync(CHANGELOG)) {
    console.error('docs/changelog.md missing');
    process.exit(1);
  }

  if (rebuildRecent > 0) {
    const before = readFileSync(CHANGELOG, 'utf8');
    const rebuilt = rebuildRecentChangelog(before, rebuildRecent);
    if (dryRun) {
      console.log(rebuilt.slice(0, 4000));
      console.log('\n... (truncated) ...\n');
      process.exit(0);
    }
    writeFileSync(CHANGELOG, rebuilt, 'utf8');
    console.log(
      `CHANGELOG rebuilt from last ${rebuildRecent} chore(release) commits (keeps ## [0.1.0] baseline).`,
    );
    process.exit(0);
  }

  let lines = commitsPendingPush();
  if (!lines.length && !ifNeeded) lines = commitsFallback();
  else if (!lines.length && ifNeeded) {
    console.log('release-sync: no commits ahead of upstream; skipping');
    process.exit(0);
  }

  const changelogCommits = excludeReleaseSubjects(lines);

  /** Pre-push: local `@{u}..HEAD` can list `feat` + prior `chore(release)`; treat release-only slice as noop. */
  if (ifNeeded && lines.length > 0 && changelogCommits.length === 0) {
    console.log(
      'release-sync: only chore(release) in push range; skipping hook',
    );
    process.exit(0);
  }

  const bodySource = changelogCommits.length > 0 ? changelogCommits : lines;
  let changelog = ensureMarkers(
    ensureUnreleasedSection(readFileSync(CHANGELOG, 'utf8')),
  );

  /**
   * After first `git push`, hook exited 1 with a `chore(release)` commit still unpushed alongside the
   * feature commit — `lines` repeats the same hashes. Avoid cutting a duplicate version bump.
   */
  if (ifNeeded && doRelease && changelogCommits.length > 0) {
    const hashes = changelogCommits.map(shortHashBeforePipe).filter(Boolean);
    if (
      hashes.length > 0 &&
      hashes.every((h) => changelog.includes(`/commit/${h}`))
    ) {
      console.log(
        'release-sync: changelog already links these commits; skipping hook.',
      );
      process.exit(0);
    }
  }

  const body = renderSyncBody(bodySource);
  changelog = replaceSyncBlock(changelog, body);

  const pkgBefore = readPkg();
  const pkg = { ...pkgBefore, version: pkgBefore.version };
  let nextVersion = pkg.version;

  const iso = new Date().toISOString().slice(0, 10);

  if (doRelease) {
    nextVersion = bumpPatch(pkg.version);
    pkg.version = nextVersion;
    changelog = promoteUnreleased(changelog, nextVersion, iso);
  }

  if (dryRun) {
    console.log('--- sync block ---\n');
    console.log(body);
    if (doRelease) console.log(`\nWould bump → ${nextVersion}`);
    process.exit(0);
  }

  writeFileSync(CHANGELOG, changelog, 'utf8');
  writeFileSync(PKG_JSON, `${JSON.stringify(pkg, null, 2)}\n`, 'utf8');
  if (doRelease && existsSync(ROOT_PKG_JSON)) {
    const rootPkg = JSON.parse(readFileSync(ROOT_PKG_JSON, 'utf8'));
    rootPkg.version = nextVersion;
    writeFileSync(
      ROOT_PKG_JSON,
      `${JSON.stringify(rootPkg, null, 2)}\n`,
      'utf8',
    );
  }

  if (!doRelease)
    console.log(
      `CHANGELOG [Unreleased] refreshed from ${lines.length} commit(s).`,
    );

  if (doRelease && ifNeeded) {
    try {
      sh('git add docs/changelog.md apps/web/package.json package.json');
      const st = sh(
        'git status --porcelain docs/changelog.md apps/web/package.json package.json',
      );
      if (!st) {
        console.log('release-sync: nothing to commit');
        process.exit(0);
      }
      execSync(
        `git commit -m "chore(release): v${nextVersion} changelog sync"`,
        {
          cwd: __root,
          stdio: 'inherit',
          env: { ...process.env, HUSKY: '0' },
        },
      );
      console.log(
        `\nrelease-sync: committed v${nextVersion}. Re-run git push.\n`,
      );
      process.exit(1);
    } catch (e) {
      console.error(e);
      process.exit(1);
    }
  }

  if (doRelease && !ifNeeded)
    console.log(
      `Release cut v${pkgBefore.version} → ${nextVersion} (${iso}). Commit when ready.`,
    );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
