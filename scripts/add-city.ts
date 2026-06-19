#!/usr/bin/env bun
/**
 * City template pipeline — config-driven GTFS/OSM setup.
 * Usage: bun scripts/add-city.ts cities/bandung.yaml
 */

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

type CityConfig = {
  city: string;
  bbox: [number, number, number, number];
  gtfs_urls: string[];
  osm_extract: string;
  warnings?: string[];
};

function parseYaml(text: string): CityConfig {
  const lines = text.split('\n');
  const config: Record<string, unknown> = {};
  for (const line of lines) {
    const m = line.match(/^(\w+):\s*(.+)$/);
    if (!m) continue;
    const [, key, raw] = m;
    if (raw.startsWith('[')) {
      config[key] = JSON.parse(raw.replace(/'/g, '"'));
    } else if (raw.startsWith('http')) {
      config[key] = [raw.trim()];
    } else {
      config[key] = raw.replace(/"/g, '').trim();
    }
  }
  return config as CityConfig;
}

const configPath = process.argv[2];
if (!configPath) {
  console.error('Usage: bun scripts/add-city.ts cities/<city>.yaml');
  process.exit(1);
}

const yaml = readFileSync(configPath, 'utf8');
const config = parseYaml(yaml);
const outDir = resolve('data/cities', config.city);
mkdirSync(outDir, { recursive: true });

const manifest = {
  ...config,
  generated_at: new Date().toISOString(),
  transit_available: (config.gtfs_urls?.length ?? 0) > 0,
};

writeFileSync(
  resolve(outDir, 'manifest.json'),
  JSON.stringify(manifest, null, 2),
);
console.log(`City template written: ${outDir}/manifest.json`);

if (!config.gtfs_urls?.length) {
  console.warn(`No GTFS for ${config.city} — walk+car only mode`);
}
