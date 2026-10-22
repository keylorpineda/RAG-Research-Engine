import { TestBed } from '@angular/core/testing';

import { I18nService } from '../../core/i18n/i18n.service';
import { BenchmarksPage } from './benchmarks-page';

describe('BenchmarksPage', () => {
  beforeEach(() => localStorage.clear());

  function render() {
    TestBed.inject(I18nService).setLang('en');
    const fixture = TestBed.createComponent(BenchmarksPage);
    fixture.detectChanges();
    return fixture;
  }

  const text = (root: HTMLElement, selector: string) =>
    [...root.querySelectorAll(selector)].map((e) => e.textContent?.trim());

  it('shows the local results and starts at the calibrated threshold', () => {
    const root = render().nativeElement as HTMLElement;
    expect(text(root, '.kpi-value')).toEqual(['0.53', '0.35', '0.47', '139 ms']);
    expect(root.querySelector('.tau')?.textContent).toContain('0.55');
    expect(root.querySelector('.tau')?.textContent).toContain('calibrated');
  });

  it('switches provider with the keyboard and resets the threshold', () => {
    const fixture = render();
    const root = fixture.nativeElement as HTMLElement;
    const local = root.querySelector<HTMLButtonElement>('app-segmented button')!;

    local.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft' })); // wraps to the last
    fixture.detectChanges();

    expect(root.querySelector('[role=radio][aria-checked=true]')?.textContent?.trim()).toBe(
      'Cohere + rerank',
    );
    expect(text(root, '.kpi-value')[0]).toBe('0.88');
    expect(text(root, '.modes dt')).toContain('+ Rerank');
    expect(root.querySelector('.tau')?.textContent).toContain('0.60');
  });

  it('moves the marker with the slider and announces the rates', () => {
    const fixture = render();
    const root = fixture.nativeElement as HTMLElement;
    const range = root.querySelector<HTMLInputElement>('#tau')!;
    range.value = '0';
    range.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(range.getAttribute('aria-valuetext')).toBe('0.20');
    expect(text(root, '.figure strong')).toEqual(['100%', '0%']);
  });
});
