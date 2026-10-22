import { TestBed } from '@angular/core/testing';

import { I18nService } from '../../core/i18n/i18n.service';
import { AnswerView } from './answer-view';
import { answered, ref } from './ask.fixtures';

function render(answer: string) {
  TestBed.inject(I18nService).setLang('en');
  const fixture = TestBed.createComponent(AnswerView);
  fixture.componentRef.setInput('answer', answer);
  fixture.componentRef.setInput('refs', [ref(1), ref(2)]);
  fixture.detectChanges();
  return fixture;
}

describe('AnswerView', () => {
  beforeEach(() => localStorage.clear());

  it('renders citations as buttons named after their source', () => {
    const root = render(answered().answer ?? '').nativeElement as HTMLElement;
    const chips = [...root.querySelectorAll<HTMLButtonElement>('button.chip')];

    expect(chips.map((c) => c.textContent?.trim())).toEqual(['1', '2']);
    expect(chips[0].getAttribute('aria-label')).toBe('Source 1: pep-1.txt');
    expect(chips[0].getAttribute('aria-controls')).toBe('passage-1');
    expect(root.querySelector('code')?.textContent).toBe('async def');
  });

  it('keeps text spacing exactly as written', () => {
    const root = render('Use `x`, then y [1].').nativeElement as HTMLElement;
    expect(root.textContent?.replace(/\s+/g, ' ').trim()).toBe('Use x, then y 1 .');
    expect(root.querySelector('p')?.firstElementChild?.textContent).toBe('Use ');
  });

  it('does not render a chip for a number with no passage', () => {
    const root = render('Unknown source [9].').nativeElement as HTMLElement;
    expect(root.querySelectorAll('button.chip')).toHaveLength(0);
  });

  it('highlights on hover and focus, and opens the passage on click', () => {
    const fixture = render('See [2].');
    const highlights: (number | null)[] = [];
    const opened: number[] = [];
    fixture.componentInstance.highlight.subscribe((n) => highlights.push(n));
    fixture.componentInstance.open.subscribe((n) => opened.push(n));

    const chip = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.chip')!;
    chip.dispatchEvent(new Event('mouseenter'));
    chip.dispatchEvent(new Event('mouseleave'));
    chip.dispatchEvent(new Event('focus'));
    chip.click();

    expect(highlights).toEqual([2, null, 2]);
    expect(opened).toEqual([2]);
  });
});
