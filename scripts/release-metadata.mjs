#!/usr/bin/env node

import { appendFileSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const NUMERIC_IDENTIFIER = '(?:0|[1-9]\\d*)';
const VERSION_PATTERN = new RegExp(`^${NUMERIC_IDENTIFIER}\\.${NUMERIC_IDENTIFIER}\\.${NUMERIC_IDENTIFIER}$`);
const TAG_PATTERN = new RegExp(`^v(${NUMERIC_IDENTIFIER}\\.${NUMERIC_IDENTIFIER}\\.${NUMERIC_IDENTIFIER})$`);

function fail(message) {
  throw new Error(message);
}

function readJsonVersion(path, label) {
  let data;
  try {
    data = JSON.parse(readFileSync(path, 'utf8'));
  } catch (error) {
    fail(`Unable to read ${label} at ${path}: ${error.message}`);
  }
  if (typeof data.version !== 'string' || !VERSION_PATTERN.test(data.version)) {
    fail(`${label} at ${path} must contain a stable X.Y.Z version`);
  }
  return data.version;
}

function readCargoVersion(path) {
  const manifestPath = resolve(path);
  const result = spawnSync(process.env.CARGO || 'cargo', [
    'metadata',
    '--no-deps',
    '--format-version',
    '1',
    '--manifest-path',
    manifestPath,
  ], { encoding: 'utf8' });
  if (result.error) {
    fail(`Unable to run Cargo metadata for ${path}: ${result.error.message}`);
  }
  if (result.status !== 0) {
    const detail = result.stderr.trim().split(/\r?\n/).at(-1);
    fail(`Unable to read Cargo package at ${path} through Cargo metadata${detail ? `: ${detail}` : ''}`);
  }
  let metadata;
  try {
    metadata = JSON.parse(result.stdout);
  } catch (error) {
    fail(`Cargo metadata returned invalid JSON for ${path}: ${error.message}`);
  }
  const packageMetadata = metadata.packages?.find((entry) => resolve(entry.manifest_path) === manifestPath);
  const version = packageMetadata?.version;
  if (!version || !VERSION_PATTERN.test(version)) {
    fail(`Cargo package at ${path} must contain a stable X.Y.Z version`);
  }
  return version;
}

function changelogSection(changelog, version) {
  const header = new RegExp(`^## \\[${version.replaceAll('.', '\\.') }\\](?:\\s+-\\s+.*)?\\s*$`, 'm');
  const match = header.exec(changelog);
  if (!match) {
    fail(`CHANGELOG.md is missing an exact [${version}] section`);
  }
  const sectionStart = match.index + match[0].length;
  const nextHeader = /^##\s+/m;
  nextHeader.lastIndex = sectionStart;
  const following = changelog.slice(sectionStart).search(nextHeader);
  const sectionEnd = following === -1 ? changelog.length : sectionStart + following;
  const notes = changelog.slice(sectionStart, sectionEnd).trim();
  if (!notes) {
    fail(`CHANGELOG.md [${version}] section must not be empty`);
  }
  return notes;
}

function outputDelimiter(value) {
  let sequence = 0;
  while (value.split(/\r?\n/).includes(`VOIDMELODY_RELEASE_NOTES_${sequence}`)) {
    sequence += 1;
  }
  return `VOIDMELODY_RELEASE_NOTES_${sequence}`;
}

function writeGithubOutput(metadata, outputPath) {
  if (!outputPath) fail('GITHUB_OUTPUT is required with --github-output');
  const delimiter = outputDelimiter(metadata.notes);
  const output = [
    `version<<${delimiter}`,
    metadata.version,
    delimiter,
    `tag<<${delimiter}`,
    metadata.tag,
    delimiter,
    `notes<<${delimiter}`,
    metadata.notes,
    delimiter,
    '',
  ].join('\n');
  appendFileSync(outputPath, output, 'utf8');
}

function parseArguments(argumentsList) {
  const options = { root: process.cwd(), tag: process.env.RELEASE_TAG, githubOutput: false };
  for (let index = 0; index < argumentsList.length; index += 1) {
    const argument = argumentsList[index];
    if (argument === '--root') options.root = argumentsList[++index];
    else if (argument === '--tag') options.tag = argumentsList[++index];
    else if (argument === '--github-output') options.githubOutput = true;
    else fail(`Unknown argument: ${argument}`);
  }
  if (!options.root) fail('--root requires a directory');
  if (!options.tag) fail('A release tag is required through --tag or RELEASE_TAG');
  return options;
}

function releaseMetadata(root, tag) {
  const tagMatch = TAG_PATTERN.exec(tag);
  if (!tagMatch) fail(`Release tag "${tag}" must match vX.Y.Z`);
  const tauriVersion = readJsonVersion(resolve(root, 'apps/web/src-tauri/tauri.conf.json'), 'Tauri config');
  const cargoVersion = readCargoVersion(resolve(root, 'apps/web/src-tauri/Cargo.toml'));
  const webVersion = readJsonVersion(resolve(root, 'apps/web/package.json'), 'web package');
  for (const [label, version] of [['Cargo package', cargoVersion], ['web package', webVersion]]) {
    if (version !== tauriVersion) fail(`${label} version is "${version}" but expected "${tauriVersion}"`);
  }
  if (tagMatch[1] !== tauriVersion) fail(`Release tag "${tag}" does not equal source version "${tauriVersion}"`);
  const notes = changelogSection(readFileSync(resolve(root, 'CHANGELOG.md'), 'utf8'), tauriVersion);
  return { version: tauriVersion, tag, notes };
}

try {
  const options = parseArguments(process.argv.slice(2));
  const metadata = releaseMetadata(resolve(options.root), options.tag);
  if (options.githubOutput) writeGithubOutput(metadata, process.env.GITHUB_OUTPUT);
  else process.stdout.write(`${JSON.stringify(metadata)}\n`);
} catch (error) {
  process.stderr.write(`release-metadata: ${error.message}\n`);
  process.exitCode = 1;
}
