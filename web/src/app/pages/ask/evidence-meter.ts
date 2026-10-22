import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';

/** Best similarity as a bar, with the threshold τ marked on it. */
@Component({
  selector: 'app-evidence-meter',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="label">{{ i18n.t().ask.evidence }}</span>
    <span class="track" role="img" [attr.aria-label]="description()">
      <span class="fill" [style.transform]="'scaleX(' + clamp(best()) + ')'"></span>
      <span class="tau" [style.left.%]="clamp(min()) * 100"></span>
      <span class="tau-label" [style.left.%]="clamp(min()) * 100" aria-hidden="true">τ</span>
    </span>
    <span class="numbers" aria-hidden="true">
      {{ i18n.decimal(best()) }} <span>≥ {{ i18n.decimal(min()) }}</span>
    </span>
  `,
  styles: `
    :host {
      display: flex;
      align-items: center;
      gap: 14px;
      padding-top: 14px;
      border-top: 1px solid var(--line-soft);
    }
    .label {
      color: var(--muted);
      font-size: 13px;
    }
    .track {
      flex: 1;
      position: relative;
      height: 6px;
      border-radius: var(--radius-pill);
      background: var(--track);
    }
    .fill {
      position: absolute;
      inset: 0;
      border-radius: var(--radius-pill);
      background: var(--accent);
      transform-origin: left;
      animation: grow 900ms var(--ease) both;
    }
    .tau {
      position: absolute;
      top: -5px;
      width: 2px;
      height: 16px;
      border-radius: 2px;
      background: var(--text);
    }
    .tau-label {
      position: absolute;
      top: 14px;
      transform: translateX(-40%);
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--faint);
    }
    .numbers {
      font-family: var(--font-mono);
      font-size: 13px;
    }
    .numbers span {
      color: var(--faint);
    }
    @keyframes grow {
      from {
        transform: scaleX(0);
      }
    }
  `,
})
export class EvidenceMeter {
  protected readonly i18n = inject(I18nService);

  readonly best = input.required<number>();
  readonly min = input.required<number>();

  protected readonly description = computed(() =>
    this.i18n.format(this.i18n.t().ask.evidenceLabel, {
      best: this.i18n.decimal(this.best()),
      min: this.i18n.decimal(this.min()),
    }),
  );

  protected clamp(value: number): number {
    return Math.min(1, Math.max(0, value));
  }
}
