import { DOCUMENT } from '@angular/common';
import { Injectable, effect, inject, signal } from '@angular/core';

export type Theme = 'dark' | 'light';

export const THEME_STORAGE_KEY = 're-theme';
const THEME_COLOR: Record<Theme, string> = { dark: '#0b0e13', light: '#f4f6f8' };

/**
 * Dark or light theme. The inline script in index.html applies the saved theme before the first
 * paint; this service reads it from there, keeps <html data-theme> in sync and remembers changes.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);

  readonly theme = signal<Theme>(this.initialTheme());

  constructor() {
    effect(() => {
      const theme = this.theme();
      const root = this.document.documentElement;
      root.dataset['theme'] = theme;
      this.document
        .querySelector('meta[name="theme-color"]')
        ?.setAttribute('content', THEME_COLOR[theme]);
      try {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
      } catch {
        // Storage can be unavailable (private mode); the theme still applies for this visit.
      }
    });
  }

  toggle(): void {
    this.theme.update((theme) => (theme === 'dark' ? 'light' : 'dark'));
  }

  private initialTheme(): Theme {
    return this.document.documentElement.dataset['theme'] === 'light' ? 'light' : 'dark';
  }
}
