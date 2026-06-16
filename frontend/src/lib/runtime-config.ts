export interface RuntimeConfig {
  product_name: string;
  version: string;
  features: Record<string, boolean>;
}

let configCache: RuntimeConfig | null = null;
let fetchPromise: Promise<RuntimeConfig> | null = null;

export async function fetchRuntimeConfig(baseUrl: string = ''): Promise<RuntimeConfig> {
  if (configCache) return configCache;
  if (fetchPromise) return fetchPromise;

  const configUrl = baseUrl ? `${baseUrl}/api/runtime-config` : '/api/runtime-config';
  
  fetchPromise = fetch(configUrl)
    .then((res) => {
      if (!res.ok) throw new Error('Failed to fetch runtime config');
      return res.json();
    })
    .then((config) => {
      configCache = config;
      fetchPromise = null;
      return config;
    })
    .catch((err) => {
      console.error('Runtime config fetch failed, using fallback', err);
      const fallback: RuntimeConfig = {
        product_name: 'Naruon',
        version: 'fallback',
        features: {}
      };
      configCache = fallback;
      fetchPromise = null;
      return fallback;
    });

  return fetchPromise;
}

export function getCachedConfig(): RuntimeConfig | null {
  return configCache;
}
