import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';

/** Placeholder until the library view lands (#40). */
@Component({
  selector: 'app-library-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<h1 class="page-title rise">{{ i18n.t().library.title }}</h1>`,
})
export class LibraryPage {
  protected readonly i18n = inject(I18nService);
}
