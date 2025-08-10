import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';

export const useShopAnalytics = (params = {}) => {
  return useQuery({
    queryKey: ['shopAnalytics', params],
    queryFn: () => apiService.getShopAnalytics(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false,
  });
};

export const useTopSellers = (year) => {
  return useQuery({
    queryKey: ['topSellers', year],
    queryFn: () => apiService.getTopSellers(year),
    staleTime: 60 * 60 * 1000, // 1 hour
    enabled: !!year,
  });
};