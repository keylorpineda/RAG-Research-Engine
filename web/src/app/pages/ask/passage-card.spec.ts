import { TestBed } from '@angular/core/testing';

import { I18nService } from '../../core/i18n/i18n.service';
import { ref } from './ask.fixtures';
import { PassageCard } from './passage-card';

describe('PassageCard', () => {
  beforeEach(() => localStorage.clear());

  function render(n: number) {
    TestBed.inject(I18nService).setLang('en');
    const fixture = TestBed.createComponent(PassageCard);
    fixture.componentRef.setInput('ref', ref(n));
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('shows the section the passage sits under', () => {
    const chunk = render(1).querySelector('.chunk');
    expect(chunk?.textContent?.trim()).toBe('§ Rationale');
    expect(chunk?.getAttribute('title')).toBe('Rationale');
  });

  it('falls back to the chunk number for window chunks', () => {
    expect(render(2).querySelector('.chunk')?.textContent?.trim()).toBe('§ 4');
  });

  it('is a focus target named after its source', () => {
    const host = render(1);
    expect(host.id).toBe('passage-1');
    expect(host.getAttribute('tabindex')).toBe('-1');
    expect(host.getAttribute('aria-label')).toBe('Passage 1 from pep-1.txt, part 2');
  });
});
