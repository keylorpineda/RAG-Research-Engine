import { ChangeDetectionStrategy, Component, input } from '@angular/core';

export type IllustrationName = 'empty-library' | 'pipeline' | 'retrieval' | 'no-evidence';

/**
 * Small inline scenes for empty, waiting and abstaining states. Colors come from the design
 * tokens so they follow the theme; motion uses transform and opacity only and stops under
 * prefers-reduced-motion (global rule in styles.css).
 */
@Component({
  selector: 'app-illustration',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { role: 'img', '[attr.aria-label]': 'label()' },
  template: `
    <svg viewBox="0 0 160 120" [attr.width]="size()" aria-hidden="true">
      @switch (name()) {
        @case ('empty-library') {
          <g class="card c1"><rect x="34" y="34" width="56" height="70" rx="8" /></g>
          <g class="card c2"><rect x="52" y="26" width="56" height="70" rx="8" /></g>
          <g class="card c3 float">
            <rect x="70" y="18" width="56" height="70" rx="8" />
            <path class="line" d="M80 36h36M80 46h28M80 56h34M80 66h20" />
          </g>
          <path class="bracket" d="M22 20h-8v84h8M138 20h8v84h-8" />
        }
        @case ('pipeline') {
          <g class="card">
            <rect x="10" y="30" width="40" height="54" rx="7" />
            <path class="line" d="M18 44h24M18 52h18M18 60h22M18 68h14" />
          </g>
          <path class="flow" d="M56 57h14" />
          <rect class="chunk k1" x="76" y="38" width="26" height="10" rx="3" />
          <rect class="chunk k2" x="76" y="52" width="26" height="10" rx="3" />
          <rect class="chunk k3" x="76" y="66" width="26" height="10" rx="3" />
          <path class="flow" d="M108 57h12" />
          @for (dot of dots; track $index) {
            <circle
              class="dot"
              [attr.cx]="dot[0]"
              [attr.cy]="dot[1]"
              r="3.2"
              [style.animation-delay]="$index * 0.18 + 's'"
            />
          }
        }
        @case ('retrieval') {
          <rect class="query" x="14" y="12" width="132" height="22" rx="11" />
          <circle class="lens" cx="28" cy="23" r="5" />
          <path class="lens" d="M32 27l4 4" />
          <rect class="typing" x="42" y="20" width="60" height="6" rx="3" />
          @for (row of [0, 1, 2]; track row) {
            <g class="passage" [style.animation-delay]="row * 0.25 + 's'">
              <rect [attr.x]="14" [attr.y]="44 + row * 24" width="132" height="18" rx="6" />
              <rect
                class="score"
                [attr.x]="22"
                [attr.y]="51 + row * 24"
                [attr.width]="[70, 48, 30][row]"
                height="4"
                rx="2"
              />
            </g>
          }
        }
        @case ('no-evidence') {
          <path class="bracket" d="M44 22h-10v62h10M116 22h10v62h-10" />
          <g class="float">
            <circle class="lens big" cx="78" cy="50" r="16" />
            <path class="lens big" d="M90 62l10 10" />
          </g>
          <path class="threshold" d="M18 100h124" />
          <rect class="meter" x="18" y="96" width="62" height="8" rx="4" />
          <path class="mark" d="M110 92v16" />
        }
      }
    </svg>
  `,
  styles: `
    :host {
      display: inline-grid;
      place-items: center;
    }
    svg {
      height: auto;
      overflow: visible;
    }
    .card rect,
    .query,
    .passage rect:first-child {
      fill: var(--surface);
      stroke: var(--line);
      stroke-width: 1.5;
    }
    .c3 rect {
      stroke: var(--accent);
    }
    .line,
    .flow,
    .bracket,
    .lens,
    .threshold,
    .mark {
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .line {
      stroke: var(--line);
      stroke-width: 3;
    }
    .bracket {
      stroke: var(--accent);
      stroke-width: 2.5;
      opacity: 0.7;
    }
    .flow {
      stroke: var(--faint);
      stroke-width: 1.5;
      stroke-dasharray: 3 4;
    }
    .chunk {
      fill: var(--lex-bg);
      stroke: var(--lex);
      stroke-width: 1.2;
      animation: settle 2.4s var(--ease) infinite;
    }
    .k2 {
      animation-delay: 0.2s;
    }
    .k3 {
      animation-delay: 0.4s;
    }
    .dot {
      fill: var(--dense);
      transform-box: fill-box;
      transform-origin: center;
      animation: pulse 2.4s ease-in-out infinite;
    }
    .lens {
      stroke: var(--muted);
      stroke-width: 2;
    }
    .lens.big {
      stroke: var(--rose);
      stroke-width: 3;
    }
    .typing {
      fill: var(--line);
      transform-box: fill-box;
      transform-origin: left;
      animation: type 2.4s var(--ease) infinite;
    }
    .passage {
      animation: rise-in 2.4s var(--ease) infinite;
    }
    .score {
      fill: var(--accent);
      transform-box: fill-box;
      transform-origin: left;
      animation: grow 2.4s var(--ease) infinite;
    }
    .threshold {
      stroke: var(--line);
      stroke-width: 1.5;
      stroke-dasharray: 4 4;
    }
    .meter {
      fill: var(--rose);
      opacity: 0.8;
      transform-box: fill-box;
      transform-origin: left;
      animation: grow 2.8s var(--ease) infinite alternate;
    }
    .mark {
      stroke: var(--text);
      stroke-width: 2;
    }
    .float {
      animation: float 4s ease-in-out infinite;
    }
    @keyframes float {
      50% {
        transform: translateY(-5px);
      }
    }
    @keyframes settle {
      0% {
        opacity: 0;
        transform: translateX(-10px);
      }
      30%,
      80% {
        opacity: 1;
        transform: none;
      }
      100% {
        opacity: 0;
      }
    }
    @keyframes pulse {
      0%,
      100% {
        opacity: 0.35;
        transform: scale(0.8);
      }
      50% {
        opacity: 1;
        transform: scale(1);
      }
    }
    @keyframes type {
      0% {
        transform: scaleX(0);
      }
      40%,
      100% {
        transform: scaleX(1);
      }
    }
    @keyframes rise-in {
      0%,
      30% {
        opacity: 0;
        transform: translateY(6px);
      }
      50%,
      100% {
        opacity: 1;
        transform: none;
      }
    }
    @keyframes grow {
      0%,
      45% {
        transform: scaleX(0);
      }
      75%,
      100% {
        transform: scaleX(1);
      }
    }
  `,
})
export class Illustration {
  readonly name = input.required<IllustrationName>();
  /** Text alternative, announced as an image. */
  readonly label = input.required<string>();
  readonly size = input(160);

  protected readonly dots: readonly [number, number][] = [
    [128, 40],
    [140, 48],
    [130, 58],
    [146, 64],
    [134, 74],
  ];
}
