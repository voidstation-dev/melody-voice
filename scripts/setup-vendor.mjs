#!/usr/bin/env node

// Initializes the vendored TTS provider submodules and applies the tracked
// VoidMelody compatibility patches. Supports both the CapCut legacy provider
// (vendor/capcut-tts-api) and the VieNeu engine (vendor/vieneu-tts).

import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repositoryRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const git = process.env.GIT || 'git';

const submodules = [
  {
    name: 'capcut-tts-api',
    directory: resolve(repositoryRoot, 'vendor/capcut-tts-api'),
    patchPath: resolve(repositoryRoot, 'patches/capcut-tts-api-succeed-status.patch'),
  },
  {
    name: 'vieneu-tts',
    directory: resolve(repositoryRoot, 'vendor/vieneu-tts'),
    patchPath: resolve(repositoryRoot, 'patches/vieneu-tts-remove-gradio-librosa-from-core.patch'),
  },
];

function runGit(argumentsList, cwd = repositoryRoot, { allowFailure = false } = {}) {
  const result = spawnSync(git, argumentsList, { cwd, encoding: 'utf8' });
  if (result.error) {
    throw new Error(`Unable to run Git: ${result.error.message}`);
  }
  if (!allowFailure && result.status !== 0) {
    const detail = (result.stderr || result.stdout).trim();
    throw new Error(`git ${argumentsList.join(' ')} failed${detail ? `: ${detail}` : ''}`);
  }
  return result;
}

function applyPatch(patchPath, directory) {
  const canApply = runGit(['apply', '--check', patchPath], directory, { allowFailure: true });
  if (canApply.status === 0) {
    runGit(['apply', patchPath], directory);
    process.stdout.write(`Applied VoidMelody compatibility patch to ${patchPath}.\n`);
    return;
  }
  const alreadyApplied = runGit(
    ['apply', '--reverse', '--check', patchPath],
    directory,
    { allowFailure: true },
  );
  if (alreadyApplied.status !== 0) {
    throw new Error(
      `The compatibility patch ${patchPath} does not match this submodule revision. ` +
        'Reset the submodule or update the patch before continuing.',
    );
  }
  process.stdout.write(`VoidMelody compatibility patch is already applied.\n`);
}

try {
  runGit(['submodule', 'update', '--init', '--recursive']);
  for (const { name, directory, patchPath } of submodules) {
    applyPatch(patchPath, directory);
  }
} catch (error) {
  process.stderr.write(`setup-vendor: ${error.message}\n`);
  process.exitCode = 1;
}