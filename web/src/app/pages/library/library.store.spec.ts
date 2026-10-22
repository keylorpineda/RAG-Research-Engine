import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { DocumentOut } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { LibraryStore, POLL_MS, UNDO_MS } from './library.store';

const doc = (id: number, status: DocumentOut['status'], chunkCount = 0): DocumentOut => ({
  id,
  filename: `doc-${id}.md`,
  mime: 'text/markdown',
  size: 100,
  status,
  uploadTs: '2026-10-22T08:00:00',
  chunkCount,
});

const flush = () => new Promise((resolve) => setTimeout(resolve));

describe('LibraryStore', () => {
  let store: LibraryStore;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), LibraryStore],
    });
    TestBed.inject(I18nService).setLang('en');
    store = TestBed.inject(LibraryStore);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => vi.useRealTimers());

  async function load(docs: DocumentOut[]): Promise<void> {
    const done = store.refresh();
    http.expectOne('/api/documents').flush(docs);
    await done;
  }

  it('sorts newest first, counts per filter and sums passages', async () => {
    await load([doc(1, 'READY', 10), doc(2, 'PROCESSING'), doc(3, 'ERROR'), doc(4, 'READY', 5)]);

    expect(store.state()).toBe('ready');
    expect(store.documents().map((d) => d.id)).toEqual([4, 3, 2, 1]);
    expect(store.counts()).toEqual({ all: 4, ready: 2, working: 1, error: 1 });
    expect(store.passages()).toBe(15);

    store.filter.set('working');
    expect(store.visible().map((d) => d.id)).toEqual([2]);
  });

  it('polls while a document is being processed and stops once all are done', async () => {
    vi.useFakeTimers();
    await load([doc(1, 'PENDING')]);

    vi.advanceTimersByTime(POLL_MS);
    http.expectOne('/api/documents').flush([doc(1, 'READY', 3)]);
    await vi.runOnlyPendingTimersAsync();

    vi.advanceTimersByTime(POLL_MS * 3);
    http.expectNone('/api/documents');
    expect(store.documents()[0].status).toBe('READY');
  });

  it('shows an error state when the first load fails', async () => {
    const done = store.refresh();
    http.expectOne('/api/documents').error(new ProgressEvent('error'));
    await done;

    expect(store.state()).toBe('error');
    expect(store.loadError()).toContain('cannot be reached');
  });

  it('hides a deleted document and only calls the API after the undo window', async () => {
    vi.useFakeTimers();
    await load([doc(1, 'READY'), doc(2, 'READY')]);

    store.remove(store.documents()[0]);
    expect(store.documents().map((d) => d.id)).toEqual([1]);
    http.expectNone('/api/documents/2');

    vi.advanceTimersByTime(UNDO_MS);
    http.expectOne({ method: 'DELETE', url: '/api/documents/2' }).flush({ message: 'ok' });
    await vi.runOnlyPendingTimersAsync();
    expect(store.lastDeleted()).toBeNull();
    expect(store.documents().map((d) => d.id)).toEqual([1]);
  });

  it('brings the document back on undo without calling the API', async () => {
    vi.useFakeTimers();
    await load([doc(1, 'READY')]);

    store.remove(store.documents()[0]);
    store.undo();
    vi.advanceTimersByTime(UNDO_MS * 2);

    http.expectNone('/api/documents/1');
    expect(store.documents().map((d) => d.id)).toEqual([1]);
  });

  it('reports rejected files and uploads the rest', async () => {
    store.upload([new File(['x'], 'tool.exe'), new File(['hello'], 'notes.txt')]);

    expect(store.notices().map((n) => n.text)).toEqual([
      'tool.exe: only PDF, MD and TXT files are accepted.',
    ]);
    expect(store.uploads().map((u) => u.name)).toEqual(['notes.txt']);

    http.expectOne('/api/upload').flush({ ids: [7], message: 'uploaded' });
    expect(store.uploads()).toEqual([]);
    http.expectOne('/api/documents').flush([doc(7, 'PENDING')]);
    await flush();
    expect(store.documents().map((d) => d.id)).toEqual([7]);
  });

  it('does not upload when the server has uploads turned off', async () => {
    const init = store.init();
    http.expectOne('/api/health').flush({
      status: 'ok',
      embeddingModel: 'm',
      minSimilarity: 0.55,
      uploadsEnabled: false,
      maxUploadMb: 20,
      maxFilesPerUpload: 10,
      jobs: {},
    });
    http.expectOne('/api/documents').flush([]);
    await init;

    store.upload([new File(['hello'], 'notes.txt')]);
    http.expectNone('/api/upload');
    expect(store.notices()[0].text).toContain('turned off');
  });
});
