import { DOCUMENT } from '@angular/common';
import { Injectable, computed, effect, inject, signal } from '@angular/core';

import { EN, ES, Messages } from './messages';

export type Lang = 'en' | 'es';

export const LANG_STORAGE_KEY = 're-lang';
const MESSAGES: Record<Lang, Messages> = { en: EN, es: ES };

/**
 * English and Spanish UI copy. Answers follow the question's language on the server; this only
 * translates the interface, and formats numbers the way each language writes them (0.55 / 0,55).
 */
@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly document = inject(DOCUMENT);

  readonly lang = signal<Lang>(this.initialLang());
  readonly t = computed<Messages>(() => MESSAGES[this.lang()]);

  private readonly numberFormats = computed(() => {
    const locale = this.lang() === 'es' ? 'es-CR' : 'en-US';
    return {
      decimal: new Intl.NumberFormat(locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
      percent: new Intl.NumberFormat(locale, { style: 'percent', maximumFractionDigits: 0 }),
      integer: new Intl.NumberFormat(locale),
    };
  });

  constructor() {
    effect(() => {
      const lang = this.lang();
      this.document.documentElement.lang = lang;
      try {
        localStorage.setItem(LANG_STORAGE_KEY, lang);
      } catch {
        // Storage can be unavailable; the language still applies for this visit.
      }
    });
  }

  setLang(lang: Lang): void {
    this.lang.set(lang);
  }

  decimal(value: number): string {
    return this.numberFormats().decimal.format(value);
  }

  percent(value: number): string {
    return this.numberFormats().percent.format(value);
  }

  integer(value: number): string {
    return this.numberFormats().integer.format(value);
  }

  private initialLang(): Lang {
    try {
      const saved = localStorage.getItem(LANG_STORAGE_KEY);
      if (saved === 'en' || saved === 'es') return saved;
    } catch {
      // Fall through to the browser language.
    }
    const browser = this.document.defaultView?.navigator.language ?? 'en';
    return browser.toLowerCase().startsWith('es') ? 'es' : 'en';
  }
}
