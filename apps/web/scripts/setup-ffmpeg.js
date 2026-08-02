const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const targetDir = path.join(__dirname, '../src-tauri/bin');
fs.mkdirSync(targetDir, { recursive: true });

const ext = process.platform === 'win32' ? '.exe' : '';
const targetPath = path.join(targetDir, `ffmpeg${ext}`);

try {
  // Use system ffmpeg to avoid npm postinstall issues
  const command = process.platform === 'win32' ? 'where ffmpeg' : 'which ffmpeg';
  const ffmpegSystemPath = execSync(command).toString().split('\n')[0].trim();
  fs.copyFileSync(ffmpegSystemPath, targetPath);
  fs.chmodSync(targetPath, '755');
  console.log(`Successfully copied system FFmpeg (${ffmpegSystemPath}) to ${targetPath}`);
} catch (e) {
  console.error('Failed to find system ffmpeg. Please install ffmpeg and ensure it is in your PATH.', e);
  process.exit(1);
}

const voiceJsonSrc = path.join(__dirname, '../../../vendor/capcut-tts-api/Voice.json');
const voiceJsonDest = path.join(targetDir, 'Voice.json');
if (fs.existsSync(voiceJsonSrc)) {
  fs.copyFileSync(voiceJsonSrc, voiceJsonDest);
  console.log(`Successfully copied Voice.json to ${voiceJsonDest}`);
} else {
  console.warn(`Warning: Voice.json not found at ${voiceJsonSrc}`);
}

// Create dummy files for missing platform binaries to satisfy Tauri
const dummyFiles = ['ffmpeg', 'ffmpeg.exe'];
dummyFiles.forEach(file => {
  const filePath = path.join(targetDir, file);
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, '');
    console.log(`Created dummy file for missing platform binary: ${file}`);
  }
});
