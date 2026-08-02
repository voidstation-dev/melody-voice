#!/usr/bin/env node

import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repositoryRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const vendorDirectory = resolve(repositoryRoot, 'vendor/capcut-tts-api');
const patchPath = resolve(repositoryRoot, 'patches/capcut-tts-api-succeed-status.patch');
const git = process.env.GIT || 'git';

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

try {
  runGit(['submodule', 'update', '--init', '--recursive']);

  const canApply = runGit(['apply', '--check', patchPath], vendorDirectory, { allowFailure: true });
  if (canApply.status === 0) {
    runGit(['apply', patchPath], vendorDirectory);
    process.stdout.write('Applied VoidMelody compatibility patch to capcut-tts-api.\n');
  } else {
    const alreadyApplied = runGit(
      ['apply', '--reverse', '--check', patchPath],
      vendorDirectory,
      { allowFailure: true },
    );
    if (alreadyApplied.status !== 0) {
      throw new Error(
        'The capcut-tts-api compatibility patch does not match this submodule revision. ' +
          'Reset the submodule or update the patch before continuing.',
      );
    }
    process.stdout.write('VoidMelody compatibility patch is already applied.\n');
  }
} catch (error) {
  process.stderr.write(`setup-vendor: ${error.message}\n`);
  process.exitCode = 1;
}
