import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { RouterLink } from '@angular/router';

import { QueryResponse } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { Illustration } from '../../shared/illustration';
import { Gauge } from './gauge';
import { PassageCard } from './passage-card';

/**
 * "What is this about?" and its Spanish forms: a request for an overview of the library, which
 * the engine cannot answer from a few passages.
 */
const OVERVIEW =
  /\bwhat\s+(is|are)\s+(this|these|it|they|the\s+(texts?|documents?|files?|library|demo))(\s+all)?\s+about\b|\bde\s+qu[eé]\s+(se\s+)?(trata|tratan|va|van|habla|hablan)\b/i;

export function isOverviewQuestion(question: string): boolean {
  return OVERVIEW.test(question);
}

/** Why the engine did not answer, with the evidence behind that decision. */
@Component({
  selector: 'app-abstain-card',
  imports: [RouterLink, Gauge, Illustration, PassageCard],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @let r = response();
    <section class="card" aria-labelledby="abstain-title">
      @if (r.reason === 'insufficient_evidence' && r.evidence.bestSimilarity !== null) {
        <app-gauge
          [value]="r.evidence.bestSimilarity"
          [min]="r.evidence.minSimilarity"
          [valueText]="best()"
          [minText]="min()"
          [label]="i18n.format(t().gauge, { best: best(), min: min() })"
        />
      } @else {
        <app-illustration
          [name]="r.reason === 'no_passages' ? 'empty-library' : 'no-evidence'"
          [label]="r.reason === 'no_passages' ? i18n.t().art.emptyLibrary : i18n.t().art.noEvidence"
          [size]="200"
        />
      }
      <div class="copy">
        <span class="badge">{{ t().badge }}</span>
        <h2 id="abstain-title">{{ copy().title }}</h2>
        <p>{{ i18n.format(copy().body, { best: best(), min: min() }) }}</p>
        @if (overview()) {
          <p class="overview">{{ t().overview }}</p>
        }
        <div class="actions">
          <button type="button" class="primary" (click)="rephrase.emit()">
            {{ t().rephrase }}
          </button>
          <a class="ghost" routerLink="/library">
            {{ overview() ? t().browseLibrary : t().addDocument }}
          </a>
          @if (r.refs.length) {
            <button
              type="button"
              class="link"
              [attr.aria-expanded]="expanded()"
              aria-controls="closest"
              (click)="expanded.set(!expanded())"
            >
              {{ expanded() ? t().hideClosest : t().showClosest }}
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                aria-hidden="true"
                [class.open]="expanded()"
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>
          }
        </div>
      </div>
    </section>
    @if (expanded()) {
      <div id="closest" class="closest" role="list" [attr.aria-label]="t().closest">
        @for (ref of r.refs; track ref.n) {
          <app-passage-card role="listitem" [ref]="ref" [maxLexical]="maxLexical()" />
        }
      </div>
    }
  `,
  styles: `
    :host {
      display: flex;
      flex-direction: column;
      gap: var(--space-4);
    }
    .card {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--space-5) var(--space-6);
      padding: 32px;
      background: var(--surface);
      border: 1px solid var(--rose-line);
      border-radius: 22px;
      animation: rise 500ms var(--ease) both;
    }
    app-gauge,
    app-illustration {
      flex: none;
      margin: 0 auto;
    }
    .copy {
      flex: 999 1 340px;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: var(--space-4);
    }
    .badge {
      align-self: flex-start;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      background: var(--rose-bg);
      color: var(--rose-fg);
      font-size: 12px;
      font-weight: 600;
    }
    h2 {
      font-size: clamp(26px, 3.4vw, 34px);
      line-height: 1.1;
      letter-spacing: -0.02em;
    }
    p {
      margin: 0;
      color: var(--soft);
      font-size: 16px;
    }
    p.overview {
      color: var(--text);
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }
    .actions > * {
      height: var(--target);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: var(--radius-m);
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
    }
    .primary {
      padding: 0 18px;
      border: 0;
      background: var(--accent);
      color: var(--on-accent);
    }
    .ghost {
      padding: 0 var(--space-4);
      border: 1px solid var(--line);
      color: var(--text);
    }
    .ghost:hover {
      background: var(--raised);
    }
    .link {
      padding: 0 var(--space-2);
      border: 0;
      background: transparent;
      color: var(--muted);
      font-weight: 500;
    }
    .link:hover {
      color: var(--text);
    }
    .link svg {
      fill: none;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
      transition: transform 250ms var(--ease);
    }
    .link svg.open {
      transform: rotate(180deg);
    }
    .closest {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr));
      gap: 10px;
      animation: rise 400ms var(--ease) both;
    }
  `,
})
export class AbstainCard {
  protected readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().ask.abstain;

  readonly response = input.required<QueryResponse>();
  /** The question that was asked, to recognize requests for an overview of the library. */
  readonly question = input('');
  readonly rephrase = output();

  protected readonly expanded = signal(false);

  protected readonly copy = computed(() => {
    const reason = this.response().reason ?? 'insufficient_evidence';
    return this.t()[reason];
  });
  protected readonly overview = computed(
    () => this.response().reason !== 'no_passages' && isOverviewQuestion(this.question()),
  );
  protected readonly best = computed(() =>
    this.i18n.decimal(this.response().evidence.bestSimilarity ?? 0),
  );
  protected readonly min = computed(() =>
    this.i18n.decimal(this.response().evidence.minSimilarity),
  );
  protected readonly maxLexical = computed(() =>
    Math.max(0, ...this.response().refs.map((r) => r.lexicalScore ?? 0)),
  );
}
