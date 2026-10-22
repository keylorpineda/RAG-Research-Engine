import { ChangeDetectionStrategy, Component, computed, inject, input, model } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';

export interface SweepPoint {
  threshold: number;
  answered: number;
  refused: number;
}

const W = 600;
const TOP = 20;
const BOTTOM = 180;

/**
 * Answered and refused rates across thresholds, with a slider that moves a marker along both
 * lines. The slider is the accessible control; the chart is described by its numbers.
 */
@Component({
  selector: 'app-abstention-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="figures" aria-live="polite">
      <span class="figure">
        <strong class="answered">{{ i18n.percent(current().answered) }}</strong>
        <span><i class="answered-key"></i>{{ t().answered }}</span>
      </span>
      <span class="figure">
        <strong class="refused">{{ i18n.percent(current().refused) }}</strong>
        <span><i class="refused-key"></i>{{ t().refused }}</span>
      </span>
    </div>
    <svg viewBox="-40 0 650 216" role="img" [attr.aria-label]="t().chart">
      @for (y of [0, 0.5, 1]; track y) {
        <line class="grid" x1="0" [attr.y1]="yOf(y)" [attr.x2]="width" [attr.y2]="yOf(y)" />
        <text class="axis" x="-8" [attr.y]="yOf(y) + 4" text-anchor="end">
          {{ i18n.percent(y) }}
        </text>
      }
      @for (p of points(); track p.threshold; let i = $index) {
        @if (i % 2 === 0) {
          <text class="axis" [attr.x]="xOf(i)" y="204" text-anchor="middle">
            {{ i18n.decimal(p.threshold) }}
          </text>
        }
      }
      <polyline class="line answered-line" [attr.points]="answeredPath()" />
      <polyline class="line refused-line" [attr.points]="refusedPath()" />
      <g class="marker" [style.transform]="'translateX(' + xOf(index()) + 'px)'">
        <line x1="0" y1="10" x2="0" y2="186" />
        <circle class="dot-answered" cx="0" [attr.cy]="yOf(current().answered)" r="5.5" />
        <circle class="dot-refused" cx="0" [attr.cy]="yOf(current().refused)" r="5.5" />
      </g>
    </svg>
    <label for="tau">
      {{ t().threshold }}
      <span class="tau">
        τ {{ i18n.decimal(current().threshold) }}
        @if (current().threshold === calibrated()) {
          · {{ t().calibrated }}
        }
      </span>
    </label>
    <input
      id="tau"
      type="range"
      min="0"
      [max]="points().length - 1"
      step="1"
      [value]="index()"
      [attr.aria-valuetext]="i18n.decimal(current().threshold)"
      (input)="index.set(+$any($event.target).value)"
    />
  `,
  styleUrl: './abstention-chart.css',
})
export class AbstentionChart {
  protected readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().benchmarks;
  protected readonly width = W;

  readonly points = input.required<readonly SweepPoint[]>();
  readonly calibrated = input.required<number>();
  /** Selected point in the sweep. */
  readonly index = model(0);

  protected readonly current = computed(() => this.points()[this.index()] ?? this.points()[0]);
  protected readonly answeredPath = computed(() => this.path((p) => p.answered));
  protected readonly refusedPath = computed(() => this.path((p) => p.refused));

  protected xOf(i: number): number {
    return (i / Math.max(1, this.points().length - 1)) * W;
  }

  protected yOf(rate: number): number {
    return BOTTOM - rate * (BOTTOM - TOP);
  }

  private path(rate: (p: SweepPoint) => number): string {
    return this.points()
      .map((p, i) => `${this.xOf(i)},${this.yOf(rate(p))}`)
      .join(' ');
  }
}
