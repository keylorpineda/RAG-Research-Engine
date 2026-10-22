import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { I18nService } from '../../core/i18n/i18n.service';

@Component({
  selector: 'app-not-found-page',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="rise">
      <p class="code">404</p>
      <h1 class="page-title">{{ i18n.t().notFound.title }}</h1>
      <a routerLink="/ask">{{ i18n.t().notFound.back }}</a>
    </section>
  `,
  styles: `
    section {
      display: grid;
      gap: var(--space-3);
      justify-items: start;
    }
    .code {
      margin: 0;
      font-family: var(--font-mono);
      color: var(--faint);
    }
  `,
})
export class NotFoundPage {
  protected readonly i18n = inject(I18nService);
}
