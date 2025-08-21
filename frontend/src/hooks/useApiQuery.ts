import { useQuery, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { apiService } from '@/services/apiService';
import { AnalyticsData, ApiQueryOptions, ApiQueryResult } from '@/types';

interface ShopAnalyticsParams {
  startDate?: string;
  endDate?: string;
  period?: 'day' | 'week' | 'month' | 'year';
  platform?: 'shopify' | 'etsy' | 'all';
}

interface TopSellersResponse {
  products: Array<{
    id: string;
    title: string;
    sales: number;
    revenue: number;
    platform: 'shopify' | 'etsy';
  }>;
  total: number;
  period: string;
}

// Generic API query hook
export const useApiQuery = <TData = unknown, TError = Error>(
  queryKey: (string | number | object)[],
  queryFn: () => Promise<TData>,
  options?: ApiQueryOptions & UseQueryOptions<TData, TError>
): ApiQueryResult<TData> => {
  const {
    enabled = true,
    refetchOnWindowFocus = false,
    retry = 3,
    retryDelay = (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...queryOptions
  } = options || {};

  const query = useQuery<TData, TError>({
    queryKey,
    queryFn,
    enabled,
    refetchOnWindowFocus,
    retry,
    retryDelay,
    staleTime: 5 * 60 * 1000, // 5 minutes default
    gcTime: 10 * 60 * 1000, // 10 minutes default (was cacheTime)
    ...queryOptions,
  });

  return {
    data: query.data,
    error: query.error,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: async () => {
      await query.refetch();
    },
  };
};

// Shop analytics hook
export const useShopAnalytics = (
  params: ShopAnalyticsParams = {},
  options?: ApiQueryOptions
): ApiQueryResult<AnalyticsData> => {
  return useApiQuery(
    ['shopAnalytics', params],
    () => apiService.getShopAnalytics(params),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      ...options,
    }
  );
};

// Top sellers hook
export const useTopSellers = (
  year: number,
  options?: ApiQueryOptions
): ApiQueryResult<TopSellersResponse> => {
  return useApiQuery(
    ['topSellers', year],
    () => apiService.getTopSellers(year),
    {
      staleTime: 60 * 60 * 1000, // 1 hour
      gcTime: 2 * 60 * 60 * 1000, // 2 hours
      enabled: !!year,
      ...options,
    }
  );
};

// Local images hook
export const useLocalImages = (
  options?: ApiQueryOptions
): ApiQueryResult<{ images: Array<{ id: string; filename: string; url: string; size: number; mimeType: string; createdAt: string }> }> => {
  return useApiQuery(
    ['localImages'],
    () => apiService.getLocalImages(),
    {
      staleTime: 10 * 60 * 1000, // 10 minutes
      gcTime: 30 * 60 * 1000, // 30 minutes
      ...options,
    }
  );
};

// Health check hook
export const useHealthCheck = (
  intervalMs: number = 30000, // 30 seconds
  options?: ApiQueryOptions
): ApiQueryResult<{ status: string; timestamp: number }> => {
  return useApiQuery(
    ['healthCheck'],
    () => apiService.healthCheck(),
    {
      staleTime: intervalMs / 2,
      gcTime: intervalMs * 2,
      refetchInterval: intervalMs,
      refetchOnWindowFocus: true,
      retry: 1, // Don't retry health checks too much
      ...options,
    }
  );
};

// Generic mutation-like hook for API operations
export const useApiMutation = <TData = unknown, TVariables = unknown>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables) => void;
    onSettled?: (data: TData | undefined, error: Error | null, variables: TVariables) => void;
  }
) => {
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);
  const [data, setData] = React.useState<TData | undefined>(undefined);

  const mutate = React.useCallback(async (variables: TVariables) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await mutationFn(variables);
      setData(result);
      options?.onSuccess?.(result, variables);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      options?.onError?.(error, variables);
      throw error;
    } finally {
      setIsLoading(false);
      options?.onSettled?.(data, error, variables);
    }
  }, [mutationFn, options, data, error]);

  return {
    mutate,
    isLoading,
    error,
    data,
    reset: () => {
      setError(null);
      setData(undefined);
    },
  };
};

// Specialized mutation hooks
export const useSaveMaskData = () => {
  return useApiMutation(
    (maskData: { name: string; data: any; thumbnail?: string; category?: string }) =>
      apiService.saveMaskData(maskData),
    {
      onSuccess: (data) => {
        console.log('Mask data saved successfully:', data);
      },
      onError: (error) => {
        console.error('Failed to save mask data:', error);
      },
    }
  );
};

export const useFileUpload = () => {
  return useApiMutation(
    ({ file, path }: { file: File; path?: string }) =>
      apiService.uploadFile(file, path),
    {
      onSuccess: (data) => {
        console.log('File uploaded successfully:', data);
      },
      onError: (error) => {
        console.error('Failed to upload file:', error);
      },
    }
  );
};

// Hook for paginated queries
export const usePaginatedQuery = <TData>(
  baseQueryKey: (string | number | object)[],
  queryFn: (page: number, limit: number) => Promise<{ data: TData[]; total: number; page: number; totalPages: number }>,
  options?: {
    initialPage?: number;
    pageSize?: number;
    enabled?: boolean;
  }
) => {
  const [page, setPage] = React.useState(options?.initialPage || 1);
  const pageSize = options?.pageSize || 10;

  const query = useApiQuery(
    [...baseQueryKey, 'paginated', page, pageSize],
    () => queryFn(page, pageSize),
    {
      enabled: options?.enabled,
      keepPreviousData: true, // This may need to be replaced with placeholderData in newer versions
    }
  );

  return {
    ...query,
    page,
    pageSize,
    setPage,
    hasNextPage: query.data ? page < query.data.totalPages : false,
    hasPreviousPage: page > 1,
    nextPage: () => setPage(p => p + 1),
    previousPage: () => setPage(p => Math.max(1, p - 1)),
    goToPage: (newPage: number) => setPage(newPage),
  };
};

export default useApiQuery;