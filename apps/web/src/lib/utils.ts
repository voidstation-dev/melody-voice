export function getFirstLine(text: string): string {
  if (!text) return "";
  const lines = text.split(/\r?\n/);
  const firstLine = lines.find(line => line.trim().length > 0) || "audio";
  // Limit length so filename isn't too long
  return firstLine.substring(0, 50).trim();
}

export function slugify(text: string): string {
  return text
    .toString()
    .normalize("NFD")                   // Separate accents from letters
    .replace(/[\u0300-\u036f]/g, "")    // Remove accents
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9 -]/g, "")        // Remove special characters
    .replace(/\s+/g, "-")               // Replace spaces with hyphens
    .replace(/-+/g, "-");               // Remove consecutive hyphens
}

export async function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  
  // Cleanup
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }, 100);
}
