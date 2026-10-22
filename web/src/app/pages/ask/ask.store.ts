import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';
import { Subscription } from 'rxjs';

import { ApiError } from '../../core/api/api-error';
import { ApiService } from '../../core/api/api.service';
import { QueryResponse, RetrievalMode } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';

export type AskState = 'idle' | 'loading' | 'done' | 'error';

export const MAX_QUESTION = 2000;

@Injectable()
export class AskStore {
  private readonly api = inject(ApiService);
  private readonly i18n = inject(I18nService);
  private request: Subscription | null = null;

  readonly question = signal('');
  readonly mode = signal<RetrievalMode>('hybrid');
  readonly k = signal(5);

  readonly state = signal<AskState>('idle');
  readonly response = signal<QueryResponse | null>(null);
  /** The question the current response answers (the box may have changed since). */
  readonly asked = signal('');
  readonly seconds = signal(0);
  readonly error = signal<string | null>(null);
  /** Passage number highlighted from a citation. */
  readonly active = signal<number | null>(null);
  /** Remaining questions under the server's daily demo cap; null when there is none. */
  readonly questionsLeft = signal<number | null>(null);

  readonly canAsk = computed(() => {
    const q = this.question().trim();
    return q.length > 0 && q.length <= MAX_QUESTION;
  });
  readonly citedCount = computed(() => this.response()?.refs.filter((r) => r.cited).length ?? 0);
  readonly maxLexical = computed(() =>
    Math.max(0, ...(this.response()?.refs ?? []).map((r) => r.lexicalScore ?? 0)),
  );

  constructor() {
    inject(DestroyRef).onDestroy(() => this.request?.unsubscribe());
  }

  refreshQuota(): void {
    this.api.health().subscribe({
      next: (health) => this.questionsLeft.set(health.questionsLeftToday ?? null),
      error: () => undefined,
    });
  }

  ask(): void {
    if (!this.canAsk()) return;
    const q = this.question().trim();
    this.request?.unsubscribe(); // a new question replaces one still in flight
    this.state.set('loading');
    this.error.set(null);
    this.active.set(null);
    this.asked.set(q);
    const started = performance.now();

    this.request = this.api.query({ q, mode: this.mode(), k: this.k() }).subscribe({
      next: (response) => {
        this.seconds.set((performance.now() - started) / 1000);
        this.response.set(response);
        this.state.set('done');
        if (this.questionsLeft() !== null) this.refreshQuota();
      },
      error: (error: unknown) => {
        this.response.set(null);
        this.error.set(this.describe(error));
        this.state.set('error');
        if (error instanceof ApiError && error.code === 'daily_limit_reached') {
          this.questionsLeft.set(0);
        }
      },
    });
  }

  private describe(error: unknown): string {
    if (error instanceof ApiError) {
      const errors = this.i18n.t().errors;
      if (error.isNetwork) return errors.network;
      if (error.code === 'daily_limit_reached' || error.code === 'too_many_requests') {
        return errors[error.code];
      }
      return error.message;
    }
    return this.i18n.t().errors.unknown;
  }
}
