import { apiClient } from './api-client';

export interface RuntimeConfig {
  product_name: string;
  version: string;
  features: {
    llm_enabled: boolean;
    smtp_enabled: boolean;
    imap_enabled: boolean;
    dev_header_auth_enabled: boolean;
    manual_bearer_login_enabled: boolean;
  };
}

let runtimeConfigPromise: Promise<RuntimeConfig> | null = null;

export function getRuntimeConfig() {
  if (!runtimeConfigPromise) {
    runtimeConfigPromise = apiClient.get<RuntimeConfig>('/api/runtime-config').then((config) => {
      apiClient.setDevHeaderAuthEnabled(config.features.dev_header_auth_enabled);
      return config;
    });
  }
  return runtimeConfigPromise;
}

export function resetRuntimeConfigCache() {
  runtimeConfigPromise = null;
}
