import { useState, useCallback, useRef } from "react";
import { ImportedTextFile, TextImportError } from "@/types/text-import";

type UseTextFileDropOptions = {
  maxFileBytes?: number;
  maxCharacters?: number;
  allowMultiple?: boolean;
  onFiles: (files: ImportedTextFile[]) => void;
  onErrors: (errors: TextImportError[]) => void;
};

export function useTextFileDrop({
  maxFileBytes = 2 * 1024 * 1024,
  maxCharacters = 500000,
  allowMultiple = false,
  onFiles,
  onErrors,
}: UseTextFileDropOptions) {
  const [isDragging, setIsDragging] = useState(false);
  const [isValidDrag, setIsValidDrag] = useState(false);
  const dragCounter = useRef(0);

  const processFiles = async (files: File[]) => {
    const validFiles: ImportedTextFile[] = [];
    const errors: TextImportError[] = [];

    const filesToProcess = allowMultiple ? files : [files[0]].filter(Boolean);

    for (const file of filesToProcess) {
      if (!file.name.toLowerCase().endsWith(".txt")) {
        errors.push({ fileName: file.name, code: "UNSUPPORTED_FILE_TYPE", message: "Only .txt files are supported" });
        continue;
      }
      if (file.size === 0) {
        errors.push({ fileName: file.name, code: "EMPTY_FILE", message: "File is empty" });
        continue;
      }
      if (file.size > maxFileBytes) {
        errors.push({ fileName: file.name, code: "FILE_TOO_LARGE", message: `File exceeds ${(maxFileBytes / 1024 / 1024).toFixed(1)}MB limit` });
        continue;
      }

      try {
        let text = await file.text();
        
        // Strip BOM
        if (text.charCodeAt(0) === 0xfeff) {
          text = text.slice(1);
        }
        
        // Basic binary check
        if (text.slice(0, 8000).includes('\u0000')) {
          errors.push({ fileName: file.name, code: "BINARY_FILE", message: "File appears to be binary, not text" });
          continue;
        }

        // Normalize line endings
        text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

        if (text.length > maxCharacters) {
          errors.push({ fileName: file.name, code: "TEXT_TOO_LONG", message: `Text exceeds maximum allowed length of ${maxCharacters} characters` });
          continue;
        }

        validFiles.push({
          id: crypto.randomUUID(),
          fileName: file.name,
          sizeBytes: file.size,
          mimeType: file.type || "text/plain",
          text,
          characterCount: text.length,
          importedAt: new Date().toISOString(),
        });
      } catch (err) {
        errors.push({ fileName: file.name, code: "READ_FAILED", message: "Failed to read file contents" });
      }
    }

    if (validFiles.length > 0) onFiles(validFiles);
    if (errors.length > 0) onErrors(errors);
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current += 1;

    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsValidDrag(true);
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current === 0) {
      setIsDragging(false);
      setIsValidDrag(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      setIsValidDrag(false);
      dragCounter.current = 0;

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        await processFiles(Array.from(e.dataTransfer.files));
      }
    },
    [allowMultiple, maxFileBytes, maxCharacters, onFiles, onErrors]
  );

  return {
    isDragging,
    isValidDrag,
    processFiles,
    dragProps: {
      onDragEnter: handleDragEnter,
      onDragLeave: handleDragLeave,
      onDragOver: handleDragOver,
      onDrop: handleDrop,
    },
  };
}
