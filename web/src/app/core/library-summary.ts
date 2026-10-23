import { DocumentOut } from './api/api.types';

/** What a library holds, in a form short enough for one line of copy. */
export interface LibrarySummary {
  count: number;
  /** Every document is a PEP, as on the public demo. */
  peps: boolean;
  /** A few display names, for libraries that are not all PEPs. */
  names: string[];
}

const PEP = /^pep-0*(\d+)\.\w+$/i;
const NAMES_SHOWN = 3;

/** `pep-0008.rst` reads as "PEP 8"; other files lose their extension. */
export function displayName(filename: string): string {
  const pep = PEP.exec(filename);
  if (pep) return `PEP ${pep[1]}`;
  return filename.replace(/\.[^.]+$/, '');
}

/** Summarizes the searchable (ready) documents; null when there are none. */
export function summarizeLibrary(docs: readonly DocumentOut[]): LibrarySummary | null {
  const ready = docs.filter((d) => d.status === 'READY');
  if (!ready.length) return null;
  const names = ready.slice(0, NAMES_SHOWN).map((d) => displayName(d.filename));
  if (ready.length > NAMES_SHOWN) names.push('…');
  return {
    count: ready.length,
    peps: ready.every((d) => PEP.test(d.filename)),
    names,
  };
}
