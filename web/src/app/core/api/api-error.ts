import { HttpErrorResponse } from '@angular/common/http';

/**
 * Every API failure as one type. The backend answers errors with
 * {"error": {"code", "message", "requestId"}}; a status of 0 means the request never got there.
 */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isNetwork(): boolean {
    return this.status === 0;
  }

  static from(response: HttpErrorResponse): ApiError {
    if (response.status === 0) {
      return new ApiError(0, 'network_error', 'The API cannot be reached.');
    }
    const body: unknown = response.error;
    if (isErrorBody(body)) {
      const { code, message, requestId } = body.error;
      return new ApiError(response.status, code, message, requestId ?? null);
    }
    return new ApiError(response.status, 'http_error', response.statusText || 'Request failed.');
  }
}

interface ErrorBody {
  error: { code: string; message: string; requestId?: string };
}

function isErrorBody(body: unknown): body is ErrorBody {
  if (typeof body !== 'object' || body === null || !('error' in body)) return false;
  const error = (body as { error: unknown }).error;
  return (
    typeof error === 'object' &&
    error !== null &&
    typeof (error as { code?: unknown }).code === 'string' &&
    typeof (error as { message?: unknown }).message === 'string'
  );
}
