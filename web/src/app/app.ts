import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Footer } from './layout/footer';
import { Header } from './layout/header';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header, Footer],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="dots" aria-hidden="true"></div>
    <app-header />
    <main class="main">
      <router-outlet />
    </main>
    <app-footer />
  `,
  styles: `
    :host {
      position: relative;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .dots {
      position: absolute;
      inset: 0 0 auto;
      height: 340px;
      pointer-events: none;
      background-image: radial-gradient(var(--dot) 1.2px, transparent 1.2px);
      background-size: 22px 22px;
      mask-image: linear-gradient(to bottom, #000, transparent);
    }
    app-header,
    app-footer {
      position: relative;
    }
    .main {
      position: relative;
      flex: 1;
      width: 100%;
      max-width: var(--content-width);
      margin: 0 auto;
      padding: var(--space-6) var(--space-5);
    }
    @media (max-width: 560px) {
      .main {
        padding: var(--space-5) var(--space-4);
      }
    }
  `,
})
export class App {}
