import { TestBed } from '@angular/core/testing';

import { DocumentOut } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { DocumentRow } from './document-row';

function render(doc: Partial<DocumentOut>) {
  TestBed.inject(I18nService).setLang('en');
  const fixture = TestBed.createComponent(DocumentRow);
  fixture.componentRef.setInput('doc', {
    id: 1,
    filename: 'paper.pdf',
    mime: 'application/pdf',
    size: 2048,
    status: 'READY',
    uploadTs: null,
    chunkCount: 12,
    ...doc,
  });
  fixture.detectChanges();
  return fixture;
}

describe('DocumentRow', () => {
  beforeEach(() => localStorage.clear());

  it.each([
    ['PENDING', 'Queued'],
    ['PROCESSING', 'Processing'],
    ['READY', 'Ready'],
    ['ERROR', 'Failed'],
  ] as const)('shows the %s status as "%s"', (status, label) => {
    const root = render({ status }).nativeElement as HTMLElement;
    expect(root.querySelector('.pill')?.textContent?.trim()).toBe(label);
    expect(root.querySelector('.pill')?.getAttribute('data-status')).toBe(status);
  });

  it('shows size and passages for ready documents', () => {
    const root = render({}).nativeElement as HTMLElement;
    expect(root.querySelector('.meta')?.textContent).toBe('2 KB · 12 passages');
    expect(root.querySelector('.type')?.textContent).toBe('PDF');
  });

  it('offers retry only for failed documents, with a labelled button', () => {
    const ready = render({}).nativeElement as HTMLElement;
    expect(ready.querySelector('.retry')).toBeNull();

    const fixture = render({ status: 'ERROR' });
    const emitted: DocumentOut[] = [];
    fixture.componentInstance.retry.subscribe((d) => emitted.push(d));
    const retry = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('.retry');
    expect(retry?.getAttribute('aria-label')).toBe('Process paper.pdf again');
    retry?.click();
    expect(emitted.map((d) => d.id)).toEqual([1]);
  });

  it('labels the delete button with the file name', () => {
    const root = render({}).nativeElement as HTMLElement;
    expect(root.querySelector('.delete')?.getAttribute('aria-label')).toBe('Delete paper.pdf');
  });
});
