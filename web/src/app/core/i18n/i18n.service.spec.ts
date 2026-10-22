import { TestBed } from '@angular/core/testing';

import { I18nService, LANG_STORAGE_KEY } from './i18n.service';
import { EN, ES } from './messages';

describe('I18nService', () => {
  beforeEach(() => localStorage.clear());

  it('restores the saved language', () => {
    localStorage.setItem(LANG_STORAGE_KEY, 'es');
    expect(TestBed.inject(I18nService).lang()).toBe('es');
  });

  it('switches copy, <html lang> and storage together', () => {
    const i18n = TestBed.inject(I18nService);
    i18n.setLang('es');
    TestBed.tick();

    expect(i18n.t().nav.library).toBe('Biblioteca');
    expect(document.documentElement.lang).toBe('es');
    expect(localStorage.getItem(LANG_STORAGE_KEY)).toBe('es');
  });

  it('formats numbers the way each language writes them', () => {
    const i18n = TestBed.inject(I18nService);
    i18n.setLang('en');
    expect(i18n.decimal(0.55)).toBe('0.55');
    i18n.setLang('es');
    expect(i18n.decimal(0.55)).toBe('0,55');
  });

  it('uses the singular for one and the plural otherwise, in both languages', () => {
    const i18n = TestBed.inject(I18nService);
    i18n.setLang('es');
    expect(i18n.count(i18n.t().library.passages, 1)).toBe('1 pasaje');
    expect(i18n.count(i18n.t().library.passages, 0)).toBe('0 pasajes');
    expect(i18n.count(i18n.t().ask.meta, 1, { s: '1,2' })).toBe('1 fuente · 1,2 s');
    i18n.setLang('en');
    expect(i18n.count(i18n.t().ask.left, 1)).toBe('1 demo question left today');
    expect(i18n.count(i18n.t().ask.left, 1240)).toBe('1,240 demo questions left today');
  });

  it('has a Spanish string for every English key', () => {
    const keys = (value: object, prefix = ''): string[] =>
      Object.entries(value).flatMap(([key, child]) =>
        typeof child === 'object' && child !== null
          ? keys(child as object, `${prefix}${key}.`)
          : [`${prefix}${key}`],
      );
    expect(keys(ES)).toEqual(keys(EN));
  });
});
