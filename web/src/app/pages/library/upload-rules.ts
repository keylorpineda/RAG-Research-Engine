/** Client-side checks that mirror the API (app/ingestion/storage.py and the upload settings). */

export const ACCEPTED_EXTENSIONS = ['.pdf', '.md', '.txt'] as const;
export const ACCEPT_ATTRIBUTE = ACCEPTED_EXTENSIONS.join(',');

export interface UploadLimits {
  maxUploadMb: number;
  maxFilesPerUpload: number;
}

export const DEFAULT_LIMITS: UploadLimits = { maxUploadMb: 20, maxFilesPerUpload: 10 };

export type RejectReason = 'type' | 'size' | 'empty' | 'count';

export interface Rejection {
  name: string;
  reason: RejectReason;
}

export interface Checked {
  accepted: File[];
  rejected: Rejection[];
}

export function extensionOf(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot > 0 ? name.slice(dot).toLowerCase() : '';
}

export function checkFiles(files: readonly File[], limits: UploadLimits): Checked {
  const accepted: File[] = [];
  const rejected: Rejection[] = [];
  for (const file of files) {
    const reason = rejectReason(file, limits);
    if (reason) rejected.push({ name: file.name, reason });
    else accepted.push(file);
  }
  // Same rule as the API: too many files is refused as a whole, not trimmed.
  if (accepted.length > limits.maxFilesPerUpload) {
    return { accepted: [], rejected: [...rejected, { name: '', reason: 'count' }] };
  }
  return { accepted, rejected };
}

function rejectReason(file: File, limits: UploadLimits): RejectReason | null {
  if (!(ACCEPTED_EXTENSIONS as readonly string[]).includes(extensionOf(file.name))) return 'type';
  if (file.size === 0) return 'empty';
  if (file.size > limits.maxUploadMb * 1024 * 1024) return 'size';
  return null;
}
