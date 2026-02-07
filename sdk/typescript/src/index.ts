/**
 * Federation TypeScript SDK
 */

export { FederationClient } from './client';
export type {
  RouteRequest,
  RouteResponse,
  RouteConstraints,
  FederationConfig
} from './types';
export {
  FederationError,
  RoutingError,
  AuthenticationError
} from './errors';
