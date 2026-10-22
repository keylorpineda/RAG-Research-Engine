import { ChangeDetectionStrategy, Component, computed, inject, input, output } from '@angular/core';

import { DocumentOut } from '../../core/api/api.types';
import { I18nService } from '../../core/i18n/i18n.service';
import { extensionOf } from './upload-rules';

@Component({
  selector: 'app-document-row',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @let d = doc();
    <span class="type" [attr.data-ext]="ext()" aria-hidden="true">{{ ext() }}</span>
    <span class="name">
      <span class="filename" [title]="d.filename">{{ d.filename }}</span>
      <span class="meta">{{ meta() }}</span>
    </span>
    <span class="state">
      @if (working()) {
        <span class="track" aria-hidden="true"><span class="indet"></span></span>
      }
      <span class="pill" [attr.data-status]="d.status">
        @if (d.status === 'PROCESSING') {
          <svg class="spin" width="11" height="11" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
          </svg>
        }
        {{ t().status[d.status] }}
      </span>
    </span>
    <span class="actions">
      @if (d.status === 'ERROR') {
        <button
          type="button"
          class="retry"
          [attr.aria-label]="i18n.format(t().retryLabel, { name: d.filename })"
          (click)="retry.emit(d)"
        >
          {{ t().retry }}
        </button>
      }
      <button
        type="button"
        class="delete"
        [attr.aria-label]="i18n.format(t().deleteLabel, { name: d.filename })"
        (click)="remove.emit(d)"
      >
        <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" />
        </svg>
      </button>
    </span>
  `,
  styleUrl: './document-row.css',
})
export class DocumentRow {
  protected readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().library;

  readonly doc = input.required<DocumentOut>();
  readonly retry = output<DocumentOut>();
  readonly remove = output<DocumentOut>();

  protected readonly ext = computed(() => extensionOf(this.doc().filename).slice(1).toUpperCase());
  protected readonly working = computed(() =>
    ['PENDING', 'PROCESSING'].includes(this.doc().status),
  );
  protected readonly meta = computed(() => {
    const d = this.doc();
    const parts: string[] = [];
    if (d.size != null) parts.push(this.i18n.bytes(d.size));
    if (d.status === 'READY') parts.push(this.i18n.count(this.t().passages, d.chunkCount));
    if (d.uploadTs) parts.push(this.i18n.relative(d.uploadTs));
    return parts.join(' · ');
  });
}
