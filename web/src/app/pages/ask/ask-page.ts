import { DOCUMENT } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  ElementRef,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';

import { RouterLink } from '@angular/router';

import { RetrievalMode } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { Illustration } from '../../shared/illustration';
import { SegmentOption, Segmented } from '../../shared/segmented';
import { AbstainCard } from './abstain-card';
import { AnswerView } from './answer-view';
import { AskStore, MAX_QUESTION } from './ask.store';
import { EvidenceMeter } from './evidence-meter';
import { PassageCard } from './passage-card';

@Component({
  selector: 'app-ask-page',
  imports: [
    RouterLink,
    Segmented,
    AnswerView,
    PassageCard,
    EvidenceMeter,
    AbstainCard,
    Illustration,
  ],
  providers: [AskStore],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './ask-page.html',
  styleUrl: './ask-page.css',
})
export class AskPage implements OnInit {
  private readonly document = inject(DOCUMENT);
  protected readonly store = inject(AskStore);
  protected readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().ask;
  protected readonly max = MAX_QUESTION;

  private readonly box = viewChild.required<ElementRef<HTMLTextAreaElement>>('box');
  protected readonly copied = signal(false);

  protected readonly modes = computed<SegmentOption<RetrievalMode>[]>(() => {
    const labels = this.t().modes;
    return [
      { value: 'hybrid', label: labels.hybrid },
      { value: 'dense', label: labels.dense },
      { value: 'lexical', label: labels.lexical },
    ];
  });
  protected readonly ks: SegmentOption<number>[] = [3, 5, 8].map((k) => ({
    value: k,
    label: String(k),
  }));

  ngOnInit(): void {
    this.store.refreshQuota();
  }

  protected onKey(event: KeyboardEvent): void {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      this.store.ask();
    }
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    this.store.ask();
  }

  protected useSample(sample: string): void {
    this.store.question.set(sample);
    this.store.ask();
  }

  protected rephrase(): void {
    const box = this.box().nativeElement;
    box.focus();
    box.select();
  }

  /** From a citation: bring its passage into view and move focus there. */
  protected openPassage(n: number): void {
    const passage = this.document.getElementById(`passage-${n}`);
    passage?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    passage?.focus({ preventScroll: true });
  }

  protected async copy(): Promise<void> {
    const answer = this.store.response()?.answer;
    if (!answer) return;
    try {
      await navigator.clipboard.writeText(answer);
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 1600);
    } catch {
      // Clipboard can be blocked; the text stays selectable.
    }
  }
}
