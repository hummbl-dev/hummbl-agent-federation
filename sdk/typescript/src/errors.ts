/**
 * SDK error classes
 */

export class FederationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FederationError';
  }
}

export class RoutingError extends FederationError {
  constructor(message: string) {
    super(message);
    this.name = 'RoutingError';
  }
}

export class AuthenticationError extends FederationError {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends FederationError {
  constructor(message: string) {
    super(message);
    this.name = 'RateLimitError';
  }
}
