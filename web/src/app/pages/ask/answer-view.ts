import { NgTemplateOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, input, output } from '@angular/core';

import { Reference } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { Inline, parseAnswer } from './answer-format';

/**
 * The answer text with its [n] citations as buttons. Hovering or focusing a citation highlights
 * its passage; activating it moves focus to the passage.
 */
@Component({
  selector: 'app-answer-view',
  imports: [NgTemplateOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @for (block of blocks(); track $index) {
      @switch (block.kind) {
        @case ('p') {
          <p><ng-container *ngTemplateOutlet="inlines; context: { $implicit: block.inlines }" /></p>
        }
        @case ('ul') {
          <ul>
            @for (item of block.items; track $index) {
              <li><ng-container *ngTemplateOutlet="inlines; context: { $implicit: item }" /></li>
            }
          </ul>
        }
        @case ('ol') {
          <ol>
            @for (item of block.items; track $index) {
              <li><ng-container *ngTemplateOutlet="inlines; context: { $implicit: item }" /></li>
            }
          </ol>
        }
      }
    }

    <ng-template #inlines let-parts>
      @for (part of asInlines(parts); track $index) {
        @switch (part.kind) {
          @case ('text') {
            <!-- A span, so template whitespace never adds spaces around the text. -->
            <span>{{ part.value }}</span>
          }
          @case ('code') {
            <code>{{ part.value }}</code>
          }
          @case ('strong') {
            <strong>{{ part.value }}</strong>
          }
          @case ('em') {
            <em>{{ part.value }}</em>
          }
          @case ('cite') {
            @let ref = byNumber().get(part.n);
            @if (ref) {
              <button
                type="button"
                class="chip"
                [class.on]="active() === part.n"
                [attr.aria-label]="citeLabel(ref)"
                [attr.aria-controls]="'passage-' + part.n"
                (mouseenter)="highlight.emit(part.n)"
                (mouseleave)="highlight.emit(null)"
                (focus)="highlight.emit(part.n)"
                (blur)="highlight.emit(null)"
                (click)="open.emit(part.n)"
              >
                {{ part.n }}
              </button>
            }
          }
        }
      }
    </ng-template>
  `,
  styles: `
    :host {
      display: block;
      font-size: 18px;
      line-height: 1.75;
    }
    p,
    ul,
    ol {
      margin: 0 0 0.8em;
    }
    :host > :last-child {
      margin-bottom: 0;
    }
    ul,
    ol {
      padding-left: 1.3em;
    }
    code {
      padding: 2px 6px;
      border-radius: 6px;
      background: var(--code);
      font-size: 15px;
    }
    .chip {
      display: inline-grid;
      place-items: center;
      min-width: 24px;
      height: 24px;
      margin: 0 2px;
      padding: 0 6px;
      vertical-align: 2px;
      border-radius: 7px;
      border: 1px solid var(--accent-line);
      background: var(--accent-bg);
      color: var(--accent-fg);
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1;
      cursor: pointer;
      transition:
        background-color var(--duration-fast) ease,
        color var(--duration-fast) ease,
        transform var(--duration-fast) var(--ease);
    }
    .chip:hover,
    .chip.on {
      background: var(--accent);
      color: var(--on-accent);
      transform: translateY(-1px);
    }
  `,
})
export class AnswerView {
  private readonly i18n = inject(I18nService);

  readonly answer = input.required<string>();
  readonly refs = input.required<readonly Reference[]>();
  readonly active = input<number | null>(null);
  readonly highlight = output<number | null>();
  readonly open = output<number>();

  protected readonly blocks = computed(() => parseAnswer(this.answer()));
  protected readonly byNumber = computed(() => new Map(this.refs().map((r) => [r.n, r])));

  protected asInlines(parts: unknown): Inline[] {
    return parts as Inline[];
  }

  protected citeLabel(ref: Reference): string {
    return this.i18n.format(this.i18n.t().ask.citeLabel, { n: ref.n, file: ref.filename });
  }
}
