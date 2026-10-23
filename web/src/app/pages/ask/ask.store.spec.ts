import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { I18nService } from '../../core/i18n/i18n.service';
import { answered } from './ask.fixtures';
import { AskStore, MAX_QUESTION } from './ask.store';

describe('AskStore', () => {
  let store: AskStore;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), AskStore],
    });
    TestBed.inject(I18nService).setLang('en');
    store = TestBed.inject(AskStore);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('only asks with a non-empty question within the limit', () => {
    store.question.set('   ');
    expect(store.canAsk()).toBe(false);
    store.question.set('x'.repeat(MAX_QUESTION + 1));
    expect(store.canAsk()).toBe(false);
    store.ask();
    http.expectNone('/api/query');
  });

  it('sends the question with the chosen mode and passage count', () => {
    store.question.set('  How do coroutines work?  ');
    store.mode.set('lexical');
    store.k.set(8);
    store.ask();

    expect(store.state()).toBe('loading');
    const request = http.expectOne('/api/query');
    expect(request.request.body).toEqual({ q: 'How do coroutines work?', mode: 'lexical', k: 8 });
    request.flush(answered());

    expect(store.state()).toBe('done');
    expect(store.asked()).toBe('How do coroutines work?');
    expect(store.citedCount()).toBe(2);
  });

  it('shows the API message when the request fails', () => {
    store.question.set('Anything?');
    store.ask();
    http
      .expectOne('/api/query')
      .flush(
        { error: { code: 'rate_limited', message: 'Daily question limit reached.' } },
        { status: 429, statusText: 'Too Many Requests' },
      );

    expect(store.state()).toBe('error');
    expect(store.error()).toBe('Daily question limit reached.');
  });

  it('words the demo limits in the visitor language and shows the cap as spent', () => {
    TestBed.inject(I18nService).setLang('es');
    store.question.set('¿Algo?');
    store.ask();
    http
      .expectOne('/api/query')
      .flush(
        { error: { code: 'daily_limit_reached', message: 'The demo has used today.' } },
        { status: 429, statusText: 'Too Many Requests' },
      );

    expect(store.error()).toContain('vuelve mañana');
    expect(store.questionsLeft()).toBe(0);
  });

  it('refreshes the questions left after each answer when there is a cap', () => {
    store.refreshQuota();
    http.expectOne('/api/health').flush({ questionsLeftToday: 3 });
    expect(store.questionsLeft()).toBe(3);

    store.question.set('Anything?');
    store.ask();
    http.expectOne('/api/query').flush(answered());
    http.expectOne('/api/health').flush({ questionsLeftToday: 2 });
    expect(store.questionsLeft()).toBe(2);
  });

  it('drops the previous request when a new question is asked', () => {
    store.question.set('First?');
    store.ask();
    const first = http.expectOne('/api/query');
    store.question.set('Second?');
    store.ask();

    expect(first.cancelled).toBe(true);
    http.expectOne('/api/query').flush(answered());
    expect(store.asked()).toBe('Second?');
  });

  it('loads what the library holds when uploads are off, once', () => {
    store.refreshQuota();
    http.expectOne('/api/health').flush({ uploadsEnabled: false, questionsLeftToday: 3 });
    http.expectOne('/api/documents').flush([
      { id: 1, filename: 'pep-0008.rst', status: 'READY', chunkCount: 4 },
      { id: 2, filename: 'pep-0020.rst', status: 'READY', chunkCount: 1 },
    ]);
    expect(store.library()).toEqual({ count: 2, peps: true, names: ['PEP 8', 'PEP 20'] });

    store.refreshQuota();
    http.expectOne('/api/health').flush({ uploadsEnabled: false, questionsLeftToday: 2 });
    http.expectNone('/api/documents');
  });

  it('does not describe the library when uploads are on', () => {
    store.refreshQuota();
    http.expectOne('/api/health').flush({ uploadsEnabled: true, questionsLeftToday: null });
    http.expectNone('/api/documents');
    expect(store.library()).toBeNull();
  });
});
