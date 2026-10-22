import { ChangeDetectionStrategy, Component, inject, input, output, signal } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';
import { ACCEPT_ATTRIBUTE } from './upload-rules';

/** Drop files or pick them with the keyboard: the whole zone is the label of a file input. */
@Component({
  selector: 'app-drop-zone',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <label
      class="drop"
      [class.over]="over()"
      [class.off]="disabled()"
      (dragenter)="onDrag($event, true)"
      (dragover)="onDrag($event, true)"
      (dragleave)="onDrag($event, false)"
      (drop)="onDrop($event)"
    >
      <svg class="frame" aria-hidden="true">
        <rect x="1" y="1" rx="19" />
      </svg>
      <svg class="art" width="64" height="56" viewBox="0 0 64 56" aria-hidden="true">
        <rect class="back" x="10" y="14" width="30" height="38" rx="6" />
        <g class="lift">
          <rect class="front" x="22" y="4" width="30" height="38" rx="6" />
          <path d="M37 30V16M31 22l6-6 6 6" />
        </g>
      </svg>
      <span class="copy">
        <strong>{{ over() ? t().release : t().drop }}</strong>
        <span>{{ i18n.format(t().accepted, { mb: maxMb() }) }}</span>
      </span>
      <span class="button">{{ t().browse }}</span>
      <input
        type="file"
        multiple
        [accept]="accept"
        [disabled]="disabled()"
        (change)="onPick($event)"
      />
    </label>
  `,
  styleUrl: './drop-zone.css',
})
export class DropZone {
  protected readonly i18n = inject(I18nService);
  protected readonly t = () => this.i18n.t().library;
  protected readonly accept = ACCEPT_ATTRIBUTE;

  readonly maxMb = input(20);
  readonly disabled = input(false);
  readonly files = output<File[]>();

  protected readonly over = signal(false);

  protected onDrag(event: DragEvent, over: boolean): void {
    event.preventDefault();
    if (!this.disabled()) this.over.set(over);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.over.set(false);
    const files = [...(event.dataTransfer?.files ?? [])];
    if (files.length && !this.disabled()) this.files.emit(files);
  }

  protected onPick(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = [...(input.files ?? [])];
    input.value = ''; // picking the same file again still fires change
    if (files.length) this.files.emit(files);
  }
}
