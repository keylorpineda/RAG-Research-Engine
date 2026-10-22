import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { I18nService } from '../core/i18n/i18n.service';

const REPO = 'https://github.com/keylorpineda/RAG-Research-Engine';

@Component({
  selector: 'app-footer',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <footer class="footer">
      <div class="inner">
        <span>© {{ year }} Keylor Pineda · Research Engine</span>
        <nav [attr.aria-label]="i18n.t().footer.label">
          <a [href]="repo">GitHub</a>
          <a [href]="repo + '/blob/main/LICENSE'">{{ i18n.t().footer.license }}</a>
          <a routerLink="/benchmarks">{{ i18n.t().nav.benchmarks }}</a>
        </nav>
      </div>
    </footer>
  `,
  styles: `
    .footer {
      border-top: 1px solid var(--line-soft);
    }
    .inner {
      max-width: var(--content-width);
      margin: 0 auto;
      padding: 18px var(--space-5);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px 20px;
      font-size: 13px;
      color: var(--faint);
    }
    nav {
      margin-left: auto;
      display: flex;
      flex-wrap: wrap;
      gap: 18px;
    }
    a {
      color: var(--muted);
      text-decoration: none;
      transition: color var(--duration-fast) ease;
    }
    a:hover {
      color: var(--text);
    }
  `,
})
export class Footer {
  protected readonly i18n = inject(I18nService);
  protected readonly repo = REPO;
  protected readonly year = new Date().getFullYear();
}
