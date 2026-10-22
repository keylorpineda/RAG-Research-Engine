import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  linkedSignal,
  signal,
} from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';
import { SegmentOption, Segmented } from '../../shared/segmented';
import { AbstentionChart } from './abstention-chart';
import { BENCHMARKS, Provider } from './benchmarks.data';

type ProviderKey = Provider['key'];

const DOCS = 'https://github.com/keylorpineda/RAG-Research-Engine/blob/main/docs/BENCHMARKS.md';

/** Speed bars use a log scale: the slowest and fastest differ by more than three orders. */
function logWidth(ms: number, maxMs: number): number {
  return Math.max(0.04, Math.log10(1 + ms) / Math.log10(1 + maxMs));
}

@Component({
  selector: 'app-benchmarks-page',
  imports: [Segmented, AbstentionChart],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './benchmarks-page.html',
  styleUrl: './benchmarks-page.css',
})
export class BenchmarksPage {
  protected readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().benchmarks;
  protected readonly data = BENCHMARKS;
  protected readonly docs = DOCS;

  protected readonly providerKey = signal<ProviderKey>('local');
  protected readonly providers: SegmentOption<ProviderKey>[] = BENCHMARKS.providers.map((p) => ({
    value: p.key,
    label: p.label,
  }));
  protected readonly provider = computed(
    () => BENCHMARKS.providers.find((p) => p.key === this.providerKey()) ?? BENCHMARKS.providers[0],
  );

  /** Starts at the calibrated threshold whenever the provider changes. */
  protected readonly sweepIndex = linkedSignal(() => {
    const p = this.provider();
    return Math.max(
      0,
      p.sweep.findIndex((s) => s.threshold === p.threshold),
    );
  });

  protected readonly kpis = computed(() => {
    const k = this.provider().kpis;
    const i = this.i18n;
    return [
      { key: 'recall5', value: i.decimal(k.recall5) },
      { key: 'mrr10', value: i.decimal(k.mrr10) },
      { key: 'recall5Es', value: i.decimal(k.recall5Es) },
      { key: 'p50', value: `${i.integer(Math.round(k.p50Ms))} ms` },
    ] as const;
  });

  protected readonly modes = computed(() => {
    const modes = this.provider().modes;
    const best = Math.max(...modes.map((m) => m.recall5));
    return modes.map((m) => ({ ...m, best: m.recall5 === best }));
  });

  protected readonly speed = computed(() => {
    const s = BENCHMARKS.search;
    const t = this.t();
    return [
      { label: t.legacy, ms: s.legacyMs, tone: 'rose' },
      { label: t.exact, ms: s.exactMs, tone: 'dense' },
      { label: t.hnsw, ms: s.hnswMs, tone: 'accent' },
    ].map((row) => ({ ...row, width: logWidth(row.ms, s.legacyMs), text: this.duration(row.ms) }));
  });

  private duration(ms: number): string {
    return ms >= 1000
      ? `${this.i18n.decimal(ms / 1000).replace(/0$/, '')} s`
      : `${this.i18n.decimal(ms)} ms`;
  }
}
