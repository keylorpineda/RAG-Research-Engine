import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

import { App } from './app';
import { routes } from './app.routes';
import { I18nService } from './core/i18n/i18n.service';

describe('App shell', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ providers: [provideRouter(routes)] });
  });

  it('renders the brand, the three sections and the copyright line', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const root = fixture.nativeElement as HTMLElement;

    expect(root.querySelector('.brand')?.textContent).toContain('Research Engine');
    const links = [...root.querySelectorAll('.nav-link')].map((a) => a.textContent?.trim());
    expect(links).toEqual(['Ask', 'Library', 'Benchmarks']);
    expect(root.querySelector('footer')?.textContent).toContain('Keylor Pineda');
  });

  it('switches the copy to Spanish', async () => {
    const fixture = TestBed.createComponent(App);
    TestBed.inject(I18nService).setLang('es');
    await fixture.whenStable();
    const root = fixture.nativeElement as HTMLElement;

    const links = [...root.querySelectorAll('.nav-link')].map((a) => a.textContent?.trim());
    expect(links).toEqual(['Preguntar', 'Biblioteca', 'Benchmarks']);
    expect(document.documentElement.lang).toBe('es');
  });

  it('redirects the root to /ask', async () => {
    const harness = await RouterTestingHarness.create('/');
    expect(harness.routeNativeElement?.textContent).toContain('Ask your documents');
  });

  it('shows the not-found page for unknown routes', async () => {
    const harness = await RouterTestingHarness.create('/nope');
    expect(harness.routeNativeElement?.textContent).toContain('Page not found');
  });
});
