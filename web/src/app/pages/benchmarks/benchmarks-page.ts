import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';

/** Placeholder until the benchmarks view lands (#41). */
@Component({
  selector: 'app-benchmarks-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<h1 class="page-title rise">{{ i18n.t().benchmarks.title }}</h1>`,
})
export class BenchmarksPage {
  protected readonly i18n = inject(I18nService);
}
