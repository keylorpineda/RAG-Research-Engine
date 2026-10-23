import { DocumentOut } from './api/api.types';
import { displayName, summarizeLibrary } from './library-summary';

function doc(id: number, filename: string, status: DocumentOut['status'] = 'READY'): DocumentOut {
  return { id, filename, mime: null, size: null, status, uploadTs: null, chunkCount: 3 };
}

describe('library summary', () => {
  it('names PEPs by number and other files without their extension', () => {
    expect(displayName('pep-0008.rst')).toBe('PEP 8');
    expect(displayName('pep-0572.txt')).toBe('PEP 572');
    expect(displayName('notes.v2.md')).toBe('notes.v2');
  });

  it('recognizes a library of PEPs and counts only searchable documents', () => {
    const summary = summarizeLibrary([
      doc(1, 'pep-0008.rst'),
      doc(2, 'pep-0020.rst'),
      doc(3, 'pep-0257.rst', 'PROCESSING'),
    ]);
    expect(summary).toEqual({ count: 2, peps: true, names: ['PEP 8', 'PEP 20'] });
  });

  it('lists a few names when the library is not all PEPs', () => {
    const summary = summarizeLibrary([
      doc(1, 'pep-0008.rst'),
      doc(2, 'handbook.pdf'),
      doc(3, 'notes.md'),
      doc(4, 'faq.txt'),
    ]);
    expect(summary).toEqual({
      count: 4,
      peps: false,
      names: ['PEP 8', 'handbook', 'notes', '…'],
    });
  });

  it('is null when nothing is ready', () => {
    expect(summarizeLibrary([])).toBeNull();
    expect(summarizeLibrary([doc(1, 'pep-0008.rst', 'ERROR')])).toBeNull();
  });
});
