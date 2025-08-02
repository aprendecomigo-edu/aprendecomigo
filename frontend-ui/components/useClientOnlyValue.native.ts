// This function is native-only as native doesn't have server rendering.
// On native platforms, we can always return the client value directly.
export function useClientOnlyValue<S, C>(server: S, client: C): S | C {
  return client;
}