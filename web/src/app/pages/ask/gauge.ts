import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

const CX = 120;
const CY = 120;
const R = 90;
const ARC = Math.PI * R;

function point(value: number, radius: number): { x: number; y: number } {
  const angle = Math.PI * (1 - value);
  return { x: CX + radius * Math.cos(angle), y: CY - radius * Math.sin(angle) };
}

/** Half-circle meter: best similarity (needle and arc) against the threshold (tick). */
@Component({
  selector: 'app-gauge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { role: 'img', '[attr.aria-label]': 'label()' },
  template: `
    <svg width="240" height="180" viewBox="0 -10 240 180" aria-hidden="true">
      <path class="track" d="M30 120 A90 90 0 0 1 210 120" />
      <path
        class="arc"
        d="M30 120 A90 90 0 0 1 210 120"
        [style.stroke-dasharray]="arc"
        [style.stroke-dashoffset]="offset()"
      />
      <line
        class="threshold"
        [attr.x1]="threshold().a.x"
        [attr.y1]="threshold().a.y"
        [attr.x2]="threshold().b.x"
        [attr.y2]="threshold().b.y"
      />
      <text class="small" [attr.x]="threshold().label.x" [attr.y]="threshold().label.y">
        τ {{ minText() }}
      </text>
      <text class="faint" x="26" y="140">0</text>
      <text class="faint" x="214" y="140">1</text>
      <g class="needle" [style.transform]="'rotate(' + angle() + 'deg)'">
        <line x1="120" y1="120" x2="120" y2="50" />
      </g>
      <circle class="hub" cx="120" cy="120" r="6" />
      <text class="value" x="120" y="156">{{ valueText() }}</text>
    </svg>
  `,
  styles: `
    :host {
      display: inline-flex;
    }
    text {
      font-family: var(--font-mono);
      text-anchor: middle;
    }
    .track,
    .arc {
      fill: none;
      stroke-width: 12;
      stroke-linecap: round;
    }
    .track {
      stroke: var(--track);
    }
    .arc {
      stroke: var(--rose);
      animation: sweep 1s var(--ease) both;
    }
    .threshold,
    .needle line {
      stroke: var(--text);
      stroke-width: 2.5;
      stroke-linecap: round;
    }
    .needle {
      transform-origin: 120px 120px;
      animation: swing 1s var(--ease) both;
    }
    .hub {
      fill: var(--surface);
      stroke: var(--text);
      stroke-width: 2.5;
    }
    .small {
      fill: var(--muted);
      font-size: 12px;
    }
    .faint {
      fill: var(--faint);
      font-size: 10px;
    }
    .value {
      fill: var(--text);
      font-size: 22px;
    }
    @keyframes sweep {
      from {
        stroke-dashoffset: 282.75; /* π × 90, the arc length */
      }
    }
    @keyframes swing {
      from {
        transform: rotate(-90deg);
      }
    }
  `,
})
export class Gauge {
  readonly value = input.required<number>();
  readonly min = input.required<number>();
  readonly valueText = input.required<string>();
  readonly minText = input.required<string>();
  readonly label = input.required<string>();

  protected readonly arc = ARC;

  private readonly clamped = computed(() => Math.min(1, Math.max(0, this.value())));
  protected readonly offset = computed(() => ARC * (1 - this.clamped()));
  protected readonly angle = computed(() => -90 + this.clamped() * 180);
  protected readonly threshold = computed(() => {
    const t = Math.min(1, Math.max(0, this.min()));
    return { a: point(t, R - 12), b: point(t, R + 12), label: point(t, R + 22) };
  });
}
