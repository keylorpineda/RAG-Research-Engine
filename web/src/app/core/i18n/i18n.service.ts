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

  private readonly pluralRules = computed(() => new Intl.PluralRules(this.lang()));

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

  /** Fills `{key}` placeholders. Numbers are formatted for the current language. */
  format(template: string, params: Record<string, string | number>): string {
    return template.replace(/\{(\w+)\}/g, (match, key: string) => {
      const value = params[key];
      if (value === undefined) return match;
      return typeof value === 'number' ? this.integer(value) : value;
    });
  }

  /** Picks the singular or plural form for `n`, then fills `{n}` and the other placeholders. */
  count(
    forms: { one: string; other: string },
    n: number,
    params: Record<string, string | number> = {},
  ): string {
    const form = this.pluralRules().select(n) === 'one' ? forms.one : forms.other;
    return this.format(form, { ...params, n });
  }

  bytes(size: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let value = size;
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value /= 1024;
      unit += 1;
    }
    const digits = unit === 0 || value >= 10 ? 0 : 1;
    const locale = this.lang() === 'es' ? 'es-CR' : 'en-US';
    return `${value.toLocaleString(locale, { maximumFractionDigits: digits })} ${units[unit]}`;
  }

  /** "3 min ago" / "hace 3 min", from an ISO timestamp. */
  relative(iso: string, now: number = Date.now()): string {
    // The API sends UTC timestamps without an offset; read them as UTC, not local time.
    const utc = /(?:[zZ]|[+-]\d\d:?\d\d)$/.test(iso) ? iso : `${iso}Z`;
    const seconds = Math.round((new Date(utc).getTime() - now) / 1000);
    if (Math.abs(seconds) < 45) return this.t().time.now;
    const steps: [Intl.RelativeTimeFormatUnit, number][] = [
      ['minute', 60],
      ['hour', 3600],
      ['day', 86400],
      ['month', 2592000],
      ['year', 31536000],
    ];
    let [unit, size] = steps[0];
    for (const step of steps) {
      if (Math.abs(seconds) >= step[1]) [unit, size] = step;
    }
    return new Intl.RelativeTimeFormat(this.lang(), { numeric: 'auto', style: 'short' }).format(
      Math.round(seconds / size),
      unit,
    );
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
