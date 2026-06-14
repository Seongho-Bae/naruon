export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;

    // In production, remove the stack trace to prevent information disclosure
    if (process.env.NODE_ENV === 'production') {
      this.stack = '';
    }
  }
}
