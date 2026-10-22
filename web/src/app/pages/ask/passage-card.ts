import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';

import { Reference } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';

/** One retrieved passage with the scores that ranked it. */
@Component({
  selector: 'app-passage-card',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[attr.id]': "'passage-' + ref().n",
    tabindex: '-1',
    '[attr.aria-label]': 'label()',
    '[class.active]': 'active()',
    '[class.dim]': 'dim()',
    '[class.uncited]': '!ref().cited',
  },
  template: `
    @let r = ref();
    <div class="top">
      <span class="n">{{ r.n }}</span>
      <span class="file">{{ r.filename }}</span>
      @if (!r.cited) {
        <span class="tag">{{ t().notCited }}</span>
      }
      <span class="chunk">§ {{ r.chunkIndex }}</span>
    </div>
    <p>{{ r.text }}</p>
    <div class="scores">
      @if (r.denseScore !== null) {
        <span class="bar" aria-hidden="true">
          <span class="dense" [style.transform]="'scaleX(' + width(r.denseScore) + ')'"></span>
        </span>
        <span class="value dense-fg" [attr.aria-label]="t().similarity + ' ' + num(r.denseScore)">
          {{ num(r.denseScore) }}
        </span>
      }
      @if (r.lexicalScore !== null) {
        <span class="bar" aria-hidden="true">
          <span class="lex" [style.transform]="'scaleX(' + lexicalWidth() + ')'"></span>
        </span>
        <span class="value lex-fg" [attr.aria-label]="t().keywords + ' ' + num(r.lexicalScore)">
          {{ num(r.lexicalScore) }}
        </span>
      }
      @if (r.rerankScore !== null) {
        <span class="bar" aria-hidden="true">
          <span class="rerank" [style.transform]="'scaleX(' + width(r.rerankScore) + ')'"></span>
        </span>
        <span class="value accent-fg" [attr.aria-label]="t().rerank + ' ' + num(r.rerankScore)">
          {{ num(r.rerankScore) }}
        </span>
      }
    </div>
  `,
  styleUrl: './passage-card.css',
})
export class PassageCard {
  private readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().ask;

  readonly ref = input.required<Reference>();
  /** Highest lexical score among the passages: ts_rank has no fixed scale, so bars are relative. */
  readonly maxLexical = input(1);
  readonly active = input(false);
  readonly dim = input(false);

  protected readonly label = computed(() =>
    this.i18n.format(this.t().passageLabel, {
      n: this.ref().n,
      file: this.ref().filename,
      chunk: this.ref().chunkIndex,
    }),
  );
  protected readonly lexicalWidth = computed(() => {
    const score = this.ref().lexicalScore ?? 0;
    return this.maxLexical() > 0 ? Math.min(1, score / this.maxLexical()) : 0;
  });

  protected width(value: number): number {
    return Math.min(1, Math.max(0, value));
  }

  protected num(value: number): string {
    return this.i18n.decimal(value);
  }
}
