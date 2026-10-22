import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AbstainReason } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { AbstainCard } from './abstain-card';
import { abstained, ref } from './ask.fixtures';

function render(reason: AbstainReason, refs = [ref(1, false)]) {
  TestBed.configureTestingModule({ providers: [provideRouter([])] });
  TestBed.inject(I18nService).setLang('en');
  const fixture = TestBed.createComponent(AbstainCard);
  fixture.componentRef.setInput('response', abstained(reason, refs));
  fixture.detectChanges();
  return fixture;
}

describe('AbstainCard', () => {
  beforeEach(() => localStorage.clear());

  it('explains weak evidence with the gauge and both numbers', () => {
    const root = render('insufficient_evidence').nativeElement as HTMLElement;
    expect(root.querySelector('h2')?.textContent).toBe('Not in your documents');
    expect(root.querySelector('p')?.textContent).toContain('0.31');
    expect(root.querySelector('p')?.textContent).toContain('0.55');
    expect(root.querySelector('app-gauge')?.getAttribute('aria-label')).toBe(
      'Best similarity 0.31, below the 0.55 needed to answer',
    );
  });

  it('points to the library when there is nothing indexed', () => {
    const root = render('no_passages', []).nativeElement as HTMLElement;
    expect(root.querySelector('h2')?.textContent).toBe('The library is empty');
    expect(root.querySelector('app-gauge')).toBeNull();
    expect(root.querySelector('a')?.getAttribute('href')).toBe('/library');
    expect(root.querySelector('[aria-expanded]')).toBeNull(); // no passages to show
  });

  it('says the model declined and lets the user read the passages', () => {
    const fixture = render('model_declined', [ref(1, false), ref(2, false)]);
    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('h2')?.textContent).toBe('The passages do not answer it');

    const toggle = root.querySelector<HTMLButtonElement>('[aria-expanded]')!;
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    toggle.click();
    fixture.detectChanges();
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    expect(root.querySelectorAll('app-passage-card')).toHaveLength(2);
  });

  it('asks the page to focus the question box on rephrase', () => {
    const fixture = render('insufficient_evidence');
    let asked = false;
    fixture.componentInstance.rephrase.subscribe(() => (asked = true));
    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.primary')!.click();
    expect(asked).toBe(true);
  });
});
