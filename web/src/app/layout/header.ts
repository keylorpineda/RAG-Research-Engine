import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { I18nService, Lang } from '../core/i18n/i18n.service';
import { ThemeService } from '../core/theme.service';
import { Logo } from './logo';

@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive, Logo],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  protected readonly i18n = inject(I18nService);
  protected readonly theme = inject(ThemeService);

  protected readonly langs: readonly Lang[] = ['en', 'es'];
  protected readonly links = [
    { path: '/ask', key: 'ask' },
    { path: '/library', key: 'library' },
    { path: '/benchmarks', key: 'benchmarks' },
  ] as const;
  protected readonly isDark = computed(() => this.theme.theme() === 'dark');
  protected readonly themeLabel = computed(() =>
    this.isDark() ? this.i18n.t().theme.toLight : this.i18n.t().theme.toDark,
  );
}
