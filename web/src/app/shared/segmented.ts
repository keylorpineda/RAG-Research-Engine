import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  computed,
  inject,
  input,
  model,
} from '@angular/core';

export interface SegmentOption<T> {
  value: T;
  label: string;
}

/**
 * A radio group drawn as segments, with a pill that slides to the selected one.
 * Arrow keys move the selection, as the radio group pattern expects.
 */
@Component({
  selector: 'app-segmented',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    role: 'radiogroup',
    '[attr.aria-label]': 'label()',
    '[style.--count]': 'options().length',
    '[style.--index]': 'index()',
  },
  template: `
    <span class="pill" aria-hidden="true"></span>
    @for (option of options(); track option.value; let i = $index) {
      <button
        type="button"
        role="radio"
        [attr.aria-checked]="i === index()"
        [attr.tabindex]="i === index() ? 0 : -1"
        [class.on]="i === index()"
        (click)="value.set(option.value)"
        (keydown)="onKey($event, i)"
      >
        {{ option.label }}
      </button>
    }
  `,
  styles: `
    :host {
      position: relative;
      display: inline-grid;
      grid-template-columns: repeat(var(--count), minmax(0, 1fr));
      padding: 3px;
      background: var(--input);
      border: 1px solid var(--line);
      border-radius: var(--radius-m);
    }
    .pill {
      position: absolute;
      top: 3px;
      bottom: 3px;
      left: 3px;
      width: calc((100% - 6px) / var(--count));
      border-radius: 9px;
      background: var(--accent-bg);
      border: 1px solid var(--accent-line);
      transform: translateX(calc(var(--index) * 100%));
      transition: transform var(--duration-emphasis) var(--ease);
    }
    button {
      position: relative;
      min-width: var(--segment-min, 0);
      height: 36px;
      padding: 0 14px;
      border: 0;
      background: transparent;
      color: var(--muted);
      font-size: 14px;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
      transition: color 200ms ease;
    }
    button:hover {
      color: var(--text);
    }
    button.on {
      color: var(--accent-fg);
    }
    @media (max-width: 480px) {
      button {
        height: 40px;
        padding: 0 6px;
        font-size: 13px;
        white-space: normal;
        line-height: 1.15;
      }
    }
  `,
})
export class Segmented<T> {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly options = input.required<readonly SegmentOption<T>[]>();
  readonly label = input.required<string>();
  readonly value = model.required<T>();

  protected readonly index = computed(() =>
    Math.max(
      0,
      this.options().findIndex((o) => o.value === this.value()),
    ),
  );

  protected onKey(event: KeyboardEvent, index: number): void {
    const keys: Record<string, number> = {
      ArrowRight: 1,
      ArrowDown: 1,
      ArrowLeft: -1,
      ArrowUp: -1,
    };
    const step = keys[event.key];
    if (!step) return;
    event.preventDefault();
    const options = this.options();
    const next = (index + step + options.length) % options.length;
    this.value.set(options[next].value);
    this.host.nativeElement.querySelectorAll('button')[next]?.focus();
  }
}
