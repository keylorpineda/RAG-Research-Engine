import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';
import { Illustration } from '../../shared/illustration';
import { DocumentRow } from './document-row';
import { DropZone } from './drop-zone';
import { Filter, LibraryStore } from './library.store';

@Component({
  selector: 'app-library-page',
  imports: [DropZone, DocumentRow, Illustration],
  providers: [LibraryStore],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './library-page.html',
  styleUrl: './library-page.css',
})
export class LibraryPage implements OnInit {
  protected readonly store = inject(LibraryStore);
  protected readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().library;

  protected readonly filters: readonly Filter[] = ['all', 'ready', 'working', 'error'];

  ngOnInit(): void {
    void this.store.init();
  }

  /** Arrow keys move between filter tabs, as the tab pattern expects. */
  protected onTabKey(event: KeyboardEvent, index: number): void {
    const step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
    if (!step) return;
    event.preventDefault();
    const next = (index + step + this.filters.length) % this.filters.length;
    this.store.filter.set(this.filters[next]);
    const tabs = (event.currentTarget as HTMLElement).parentElement?.querySelectorAll('button');
    tabs?.[next]?.focus();
  }
}
