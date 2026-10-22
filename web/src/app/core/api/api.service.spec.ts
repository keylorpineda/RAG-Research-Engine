import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import { ApiError } from './api-error';
import { API_BASE_URL, ApiService } from './api.service';
import { QueryResponse } from './api.types';

describe('ApiService', () => {
  let api: ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: 'https://api.example.test/' },
      ],
    });
    api = TestBed.inject(ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('posts the question to /api/query on the configured host', async () => {
    const body: QueryResponse = {
      answered: false,
      answer: null,
      reason: 'insufficient_evidence',
      refs: [],
      invalidCitations: [],
      evidence: { bestSimilarity: 0.41, minSimilarity: 0.55 },
    };
    const result = firstValueFrom(api.query({ q: 'What is PEP 8?', mode: 'hybrid' }));

    const request = http.expectOne('https://api.example.test/api/query');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ q: 'What is PEP 8?', mode: 'hybrid' });
    request.flush(body);

    expect(await result).toEqual(body);
  });

  it('sends uploads as multipart files', () => {
    const file = new File(['hello'], 'notes.txt', { type: 'text/plain' });
    api.upload([file]).subscribe();

    const request = http.expectOne('https://api.example.test/api/upload');
    const form = request.request.body as FormData;
    expect(form.getAll('files')).toHaveLength(1);
    request.flush({ ids: [1], message: 'uploaded' });
  });

  it('turns the API error body into an ApiError', async () => {
    const result = firstValueFrom(api.document(9));
    http
      .expectOne('https://api.example.test/api/documents/9')
      .flush(
        { error: { code: 'not_found', message: 'Document 9 not found.', requestId: 'abc' } },
        { status: 404, statusText: 'Not Found' },
      );

    const error = await result.catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: 'not_found', requestId: 'abc' });
  });

  it('marks unreachable APIs as network errors', async () => {
    const result = firstValueFrom(api.health());
    http.expectOne('https://api.example.test/api/health').error(new ProgressEvent('error'));

    const error = (await result.catch((e: unknown) => e)) as ApiError;
    expect(error.isNetwork).toBe(true);
  });

  it('falls back to the status text when the body is not the API format', async () => {
    const result = firstValueFrom(api.documents());
    http
      .expectOne('https://api.example.test/api/documents')
      .flush('<html>Bad gateway</html>', { status: 502, statusText: 'Bad Gateway' });

    const error = (await result.catch((e: unknown) => e)) as ApiError;
    expect(error).toMatchObject({ status: 502, code: 'http_error', message: 'Bad Gateway' });
  });
});
