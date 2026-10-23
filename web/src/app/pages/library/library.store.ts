import { HttpEventType } from '@angular/common/http';
import { DOCUMENT } from '@angular/common';
import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { ApiError } from '../../core/api/api-error';
import { ApiService } from '../../core/api/api.service';
import { DocumentOut, HealthOut } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { summarizeLibrary } from '../../core/library-summary';
import { DEFAULT_LIMITS, UploadLimits, checkFiles } from './upload-rules';

export type Filter = 'all' | 'ready' | 'working' | 'error';
export type LoadState = 'loading' | 'ready' | 'error';

export interface UploadItem {
  key: number;
  name: string;
  size: number;
  /** 0 to 1. */
  progress: number;
}

export interface Notice {
  key: number;
  text: string;
  tone: 'info' | 'error';
}

interface PendingDelete {
  doc: DocumentOut;
  timer: ReturnType<typeof setTimeout>;
}

export const POLL_MS = 2000;
export const UNDO_MS = 5000;

const FILTERS: Record<Filter, (doc: DocumentOut) => boolean> = {
  all: () => true,
  ready: (d) => d.status === 'READY',
  working: (d) => d.status === 'PENDING' || d.status === 'PROCESSING',
  error: (d) => d.status === 'ERROR',
};

/**
 * State of the library page: documents (polled while any is being processed), uploads in flight,
 * deletions waiting out their undo window, and messages for the user.
 */
@Injectable()
export class LibraryStore {
  private readonly api = inject(ApiService);
  private readonly i18n = inject(I18nService);

  private readonly docs = signal<DocumentOut[]>([]);
  private readonly hidden = signal<ReadonlySet<number>>(new Set());
  private readonly pendingDeletes = new Map<number, PendingDelete>();
  private pollTimer: ReturnType<typeof setTimeout> | null = null;
  private nextKey = 1;

  readonly state = signal<LoadState>('loading');
  readonly loadError = signal<string | null>(null);
  readonly health = signal<HealthOut | null>(null);
  readonly uploads = signal<UploadItem[]>([]);
  readonly notices = signal<Notice[]>([]);
  readonly lastDeleted = signal<DocumentOut | null>(null);
  readonly filter = signal<Filter>('all');

  readonly limits = computed<UploadLimits>(() => {
    const health = this.health();
    return health
      ? { maxUploadMb: health.maxUploadMb, maxFilesPerUpload: health.maxFilesPerUpload }
      : DEFAULT_LIMITS;
  });
  readonly uploadsEnabled = computed(() => this.health()?.uploadsEnabled ?? true);

  readonly documents = computed(() => {
    const hidden = this.hidden();
    return this.docs().filter((d) => !hidden.has(d.id));
  });
  readonly counts = computed(() => {
    const docs = this.documents();
    return {
      all: docs.length,
      ready: docs.filter(FILTERS.ready).length,
      working: docs.filter(FILTERS.working).length,
      error: docs.filter(FILTERS.error).length,
    } satisfies Record<Filter, number>;
  });
  readonly visible = computed(() => this.documents().filter(FILTERS[this.filter()]));
  readonly summary = computed(() => summarizeLibrary(this.documents()));
  readonly passages = computed(() =>
    this.documents().reduce((total, d) => total + (d.chunkCount ?? 0), 0),
  );

  constructor() {
    // Documents can change from elsewhere (another tab, the CLI): refresh when the tab returns.
    const document = inject(DOCUMENT);
    const onVisible = () => {
      if (document.visibilityState === 'visible' && this.state() !== 'loading') void this.refresh();
    };
    document.addEventListener('visibilitychange', onVisible);

    inject(DestroyRef).onDestroy(() => {
      document.removeEventListener('visibilitychange', onVisible);
      this.stopPolling();
      // Leaving the page commits deletions that were waiting for an undo.
      for (const id of [...this.pendingDeletes.keys()]) void this.commitDelete(id);
    });
  }

  async init(): Promise<void> {
    this.api.health().subscribe({ next: (h) => this.health.set(h), error: () => undefined });
    await this.refresh();
  }

  async refresh(): Promise<void> {
    try {
      const docs = await firstValueFrom(this.api.documents());
      this.docs.set([...docs].sort((a, b) => b.id - a.id)); // newest first
      this.state.set('ready');
      this.loadError.set(null);
    } catch (error) {
      if (this.state() !== 'ready') this.state.set('error');
      this.loadError.set(this.describe(error));
    }
    this.schedulePoll();
  }

  upload(files: readonly File[]): void {
    if (!this.uploadsEnabled()) {
      this.notify(this.i18n.t().library.uploadsOff, 'error');
      return;
    }
    const { accepted, rejected } = checkFiles(files, this.limits());
    const copy = this.i18n.t().library.rejected;
    for (const r of rejected) {
      const { maxUploadMb: mb, maxFilesPerUpload: max } = this.limits();
      this.notify(this.i18n.format(copy[r.reason], { name: r.name, mb, max }), 'error');
    }
    for (const file of accepted) this.uploadOne(file);
  }

  remove(doc: DocumentOut): void {
    // Only one deletion shows the undo toast at a time: the previous one is committed now.
    const previous = this.lastDeleted();
    if (previous) void this.commitDelete(previous.id);

    this.hidden.update((ids) => new Set(ids).add(doc.id));
    const timer = setTimeout(() => void this.commitDelete(doc.id), UNDO_MS);
    this.pendingDeletes.set(doc.id, { doc, timer });
    this.lastDeleted.set(doc);
  }

  undo(): void {
    const doc = this.lastDeleted();
    if (!doc) return;
    const pending = this.pendingDeletes.get(doc.id);
    if (pending) clearTimeout(pending.timer);
    this.pendingDeletes.delete(doc.id);
    this.unhide(doc.id);
    this.lastDeleted.set(null);
  }

  async retry(doc: DocumentOut): Promise<void> {
    try {
      await firstValueFrom(this.api.reingest(doc.id));
    } catch (error) {
      this.notify(this.describe(error), 'error');
    }
    await this.refresh();
  }

  dismiss(key: number): void {
    this.notices.update((list) => list.filter((n) => n.key !== key));
  }

  private uploadOne(file: File): void {
    const key = this.nextKey++;
    this.uploads.update((list) => [
      ...list,
      { key, name: file.name, size: file.size, progress: 0 },
    ]);
    const done = () => this.uploads.update((list) => list.filter((u) => u.key !== key));

    this.api.uploadWithProgress(file).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          const progress = event.loaded / event.total;
          this.uploads.update((list) => list.map((u) => (u.key === key ? { ...u, progress } : u)));
        } else if (event.type === HttpEventType.Response) {
          done();
          void this.refresh();
        }
      },
      error: (error: unknown) => {
        done();
        this.notify(`${file.name}: ${this.describe(error)}`, 'error');
      },
    });
  }

  private async commitDelete(id: number): Promise<void> {
    const pending = this.pendingDeletes.get(id);
    if (!pending) return;
    clearTimeout(pending.timer);
    this.pendingDeletes.delete(id);
    if (this.lastDeleted()?.id === id) this.lastDeleted.set(null);
    try {
      await firstValueFrom(this.api.deleteDocument(id));
      this.docs.update((docs) => docs.filter((d) => d.id !== id));
    } catch (error) {
      this.notify(this.describe(error), 'error');
    } finally {
      this.unhide(id);
    }
  }

  private unhide(id: number): void {
    this.hidden.update((ids) => {
      const next = new Set(ids);
      next.delete(id);
      return next;
    });
  }

  private schedulePoll(): void {
    this.stopPolling();
    const busy = this.docs().some(FILTERS.working);
    if (busy) this.pollTimer = setTimeout(() => void this.refresh(), POLL_MS);
  }

  private stopPolling(): void {
    if (this.pollTimer) clearTimeout(this.pollTimer);
    this.pollTimer = null;
  }

  private notify(text: string, tone: Notice['tone']): void {
    const key = this.nextKey++;
    this.notices.update((list) => [...list, { key, text, tone }]);
  }

  private describe(error: unknown): string {
    if (error instanceof ApiError) {
      return error.isNetwork ? this.i18n.t().errors.network : error.message;
    }
    return this.i18n.t().errors.unknown;
  }
}
