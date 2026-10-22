import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, InjectionToken, inject } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ApiError } from './api-error';
import {
  DocumentDetailOut,
  DocumentOut,
  HealthOut,
  MessageOut,
  QueryRequest,
  QueryResponse,
  UploadOut,
} from './api.types';

/** Base URL of the API, without a trailing slash. Empty means same origin (the dev proxy). */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => environment.apiBaseUrl,
});

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_BASE_URL).replace(/\/$/, '');

  health(): Observable<HealthOut> {
    return this.wrap(this.http.get<HealthOut>(this.url('/api/health')));
  }

  documents(): Observable<DocumentOut[]> {
    return this.wrap(this.http.get<DocumentOut[]>(this.url('/api/documents')));
  }

  document(id: number): Observable<DocumentDetailOut> {
    return this.wrap(this.http.get<DocumentDetailOut>(this.url(`/api/documents/${id}`)));
  }

  upload(files: readonly File[]): Observable<UploadOut> {
    const form = new FormData();
    for (const file of files) form.append('files', file, file.name);
    return this.wrap(this.http.post<UploadOut>(this.url('/api/upload'), form));
  }

  deleteDocument(id: number): Observable<MessageOut> {
    return this.wrap(this.http.delete<MessageOut>(this.url(`/api/documents/${id}`)));
  }

  reingest(id: number): Observable<MessageOut> {
    return this.wrap(this.http.post<MessageOut>(this.url(`/api/documents/${id}/reingest`), null));
  }

  query(request: QueryRequest): Observable<QueryResponse> {
    return this.wrap(this.http.post<QueryResponse>(this.url('/api/query'), request));
  }

  private url(path: string): string {
    return `${this.base}${path}`;
  }

  private wrap<T>(request: Observable<T>): Observable<T> {
    return request.pipe(
      catchError((error: unknown) =>
        throwError(() => (error instanceof HttpErrorResponse ? ApiError.from(error) : error)),
      ),
    );
  }
}
