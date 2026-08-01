export type ImportedTextFile = {
  id: string;
  fileName: string;
  sizeBytes: number;
  mimeType: string;
  text: string;
  characterCount: number;
  importedAt: string;
  speed?: number;
};

export type TextImportErrorCode =
  | "UNSUPPORTED_FILE_TYPE"
  | "FILE_TOO_LARGE"
  | "EMPTY_FILE"
  | "READ_FAILED"
  | "TEXT_TOO_LONG"
  | "BINARY_FILE";

export type TextImportError = {
  fileName: string;
  code: TextImportErrorCode;
  message: string;
};
