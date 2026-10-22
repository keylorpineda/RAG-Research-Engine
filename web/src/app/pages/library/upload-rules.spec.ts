import { DEFAULT_LIMITS, checkFiles, extensionOf } from './upload-rules';

const file = (name: string, size = 10) => new File(['x'.repeat(size)], name);

describe('upload rules', () => {
  it('reads extensions case-insensitively and ignores dotfiles', () => {
    expect(extensionOf('Paper.PDF')).toBe('.pdf');
    expect(extensionOf('.env')).toBe('');
    expect(extensionOf('archive.tar.gz')).toBe('.gz');
  });

  it('accepts PDF, Markdown and text files', () => {
    const { accepted, rejected } = checkFiles(
      [file('a.pdf'), file('b.md'), file('c.TXT')],
      DEFAULT_LIMITS,
    );
    expect(accepted.map((f) => f.name)).toEqual(['a.pdf', 'b.md', 'c.TXT']);
    expect(rejected).toEqual([]);
  });

  it('rejects other types, empty files and files over the size limit', () => {
    const limits = { maxUploadMb: 1, maxFilesPerUpload: 10 };
    const { accepted, rejected } = checkFiles(
      [file('tool.exe'), file('empty.txt', 0), file('big.pdf', 1024 * 1024 + 1), file('ok.md')],
      limits,
    );
    expect(accepted.map((f) => f.name)).toEqual(['ok.md']);
    expect(rejected).toEqual([
      { name: 'tool.exe', reason: 'type' },
      { name: 'empty.txt', reason: 'empty' },
      { name: 'big.pdf', reason: 'size' },
    ]);
  });

  it('refuses the whole batch when it has too many files, like the API', () => {
    const files = Array.from({ length: 3 }, (_, i) => file(`${i}.txt`));
    const { accepted, rejected } = checkFiles(files, { maxUploadMb: 20, maxFilesPerUpload: 2 });
    expect(accepted).toEqual([]);
    expect(rejected).toEqual([{ name: '', reason: 'count' }]);
  });
});
