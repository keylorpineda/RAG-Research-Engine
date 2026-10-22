import { ChangeDetectionStrategy, Component } from '@angular/core';

/** The citation brackets mark: a passage [·] between the brackets of a citation. */
@Component({
  selector: 'app-logo',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
      <path d="M10 5H6v18h4" />
      <path d="M18 5h4v18h-4" />
      <circle cx="14" cy="14" r="2.4" />
    </svg>
  `,
  styles: `
    :host {
      display: inline-flex;
    }
    path {
      fill: none;
      stroke: var(--accent);
      stroke-width: 2.2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    circle {
      fill: var(--text);
      animation: blink 2.8s ease-in-out infinite;
    }
    @keyframes blink {
      50% {
        opacity: 0.35;
      }
    }
  `,
})
export class Logo {}
