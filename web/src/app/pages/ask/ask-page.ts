import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';

/** Placeholder until the ask view lands (#41). */
@Component({
  selector: 'app-ask-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<h1 class="page-title rise">{{ i18n.t().ask.title }}</h1>`,
})
export class AskPage {
  protected readonly i18n = inject(I18nService);
}
