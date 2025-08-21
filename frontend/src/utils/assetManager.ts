import React, { useState, useEffect, useRef } from 'react';
import { AssetConfig } from '@/types';

interface Asset {
  url: string;
  type: 'image' | 'video' | 'audio' | 'document' | 'other';
  priority?: 'high' | 'medium' | 'low';
}

interface ImageOptimizationOptions {
  width?: number;
  height?: number;
  quality?: number;
  format?: 'webp' | 'jpeg' | 'png' | 'avif';
}

interface OptimizedImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  lazy?: boolean;
  fallbackSrc?: string;
  onLoadingChange?: (loading: boolean) => void;
  onError?: (error: Error) => void;
}

class AssetManager {
  private cdnBaseUrl: string;
  private assetCache: Map<string, Promise<string>> = new Map();
  private config: AssetConfig;

  constructor() {
    this.cdnBaseUrl = process.env.REACT_APP_CDN_BASE_URL || '';
    this.config = {
      baseUrl: this.cdnBaseUrl,
      version: process.env.REACT_APP_VERSION || '1.0.0',
      cacheDuration: 24 * 60 * 60 * 1000, // 24 hours
    };
  }

  getTenantAssetUrl(tenantId: string, assetPath: string): string {
    const baseUrl = this.cdnBaseUrl || (typeof window !== 'undefined' ? window.location.origin : '');
    const cleanPath = assetPath.startsWith('/') ? assetPath.slice(1) : assetPath;
    return `${baseUrl}/tenant-assets/${tenantId}/${cleanPath}`;
  }

  getOptimizedImageUrl(src: string, options: ImageOptimizationOptions = {}): string {
    const { width, height, quality = 80, format = 'webp' } = options;
    
    if (!this.cdnBaseUrl || !src) {
      return src; // No CDN or invalid src, return original
    }

    try {
      const params = new URLSearchParams();
      if (width) params.set('w', width.toString());
      if (height) params.set('h', height.toString());
      params.set('q', quality.toString());
      params.set('f', format);
      params.set('v', this.config.version); // Cache busting

      return `${this.cdnBaseUrl}/optimize?url=${encodeURIComponent(src)}&${params}`;
    } catch (error) {
      console.error('Error generating optimized image URL:', error);
      return src;
    }
  }

  async preloadAssets(assets: Asset[]): Promise<PromiseSettledResult<string>[]> {
    const promises = assets.map(async (asset) => {
      // Check cache first
      if (this.assetCache.has(asset.url)) {
        return this.assetCache.get(asset.url)!;
      }

      const promise = this.loadAsset(asset);
      this.assetCache.set(asset.url, promise);
      return promise;
    });

    return Promise.allSettled(promises);
  }

  private loadAsset(asset: Asset): Promise<string> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Asset loading timeout: ${asset.url}`));
      }, 30000); // 30 second timeout

      const cleanup = () => {
        clearTimeout(timeout);
      };

      if (asset.type === 'image') {
        const img = new Image();
        img.onload = () => {
          cleanup();
          resolve(asset.url);
        };
        img.onerror = (error) => {
          cleanup();
          reject(new Error(`Failed to load image: ${asset.url}`));
        };
        img.src = asset.url;
      } else {
        // For other asset types, use fetch
        fetch(asset.url, {
          method: 'HEAD', // Just check if resource exists
          signal: AbortSignal.timeout(10000), // 10 second timeout
        })
          .then(response => {
            cleanup();
            if (response.ok) {
              resolve(asset.url);
            } else {
              reject(new Error(`Asset not found: ${asset.url} (${response.status})`));
            }
          })
          .catch(error => {
            cleanup();
            reject(error);
          });
      }
    });
  }

  preloadCriticalAssets(tenantId: string): Promise<PromiseSettledResult<string>[]> {
    const criticalAssets: Asset[] = [
      {
        url: this.getTenantAssetUrl(tenantId, 'logo.png'),
        type: 'image',
        priority: 'high',
      },
      {
        url: this.getTenantAssetUrl(tenantId, 'favicon.ico'),
        type: 'image',
        priority: 'high',
      },
      {
        url: this.getTenantAssetUrl(tenantId, 'theme.css'),
        type: 'other',
        priority: 'high',
      },
    ];

    return this.preloadAssets(criticalAssets);
  }

  clearCache(): void {
    this.assetCache.clear();
  }

  getCacheSize(): number {
    return this.assetCache.size;
  }

  // Generate responsive image srcSet
  generateResponsiveSrcSet(src: string, widths: number[] = [320, 640, 1024, 1920]): string {
    if (!this.cdnBaseUrl) {
      return src;
    }

    return widths
      .map(width => {
        const optimizedUrl = this.getOptimizedImageUrl(src, { width });
        return `${optimizedUrl} ${width}w`;
      })
      .join(', ');
  }
}

export const assetManager = new AssetManager();

// Optimized Image Component
export const OptimizedImage: React.FC<OptimizedImageProps> = ({ 
  src, 
  alt, 
  width, 
  height, 
  className = '', 
  lazy = true,
  fallbackSrc,
  onLoadingChange,
  onError,
  ...props 
}) => {
  const [imageSrc, setImageSrc] = useState<string>(src);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hasError, setHasError] = useState<boolean>(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!src) {
      setHasError(true);
      setIsLoading(false);
      return;
    }

    // Generate optimized image URL
    try {
      const optimizedSrc = assetManager.getOptimizedImageUrl(src, {
        width,
        height,
      });
      
      setImageSrc(optimizedSrc);
      setIsLoading(true);
      setHasError(false);
    } catch (error) {
      console.error('Error optimizing image:', error);
      setImageSrc(src);
    }
  }, [src, width, height]);

  useEffect(() => {
    onLoadingChange?.(isLoading);
  }, [isLoading, onLoadingChange]);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = (event: React.SyntheticEvent<HTMLImageElement, Event>) => {
    setHasError(true);
    setIsLoading(false);
    
    // Try fallback source if available
    if (fallbackSrc && imageSrc !== fallbackSrc) {
      setImageSrc(fallbackSrc);
      setHasError(false);
      setIsLoading(true);
      return;
    }

    // Try original source as last resort
    if (imageSrc !== src) {
      setImageSrc(src);
      setHasError(false);
      setIsLoading(true);
      return;
    }

    const error = new Error(`Failed to load image: ${src}`);
    onError?.(error);
  };

  if (!src) {
    return (
      <div className={`bg-gray-200 flex items-center justify-center text-gray-500 ${className}`}>
        No image
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse rounded" />
      )}
      <img
        ref={imgRef}
        src={imageSrc}
        alt={alt}
        width={width}
        height={height}
        loading={lazy ? 'lazy' : 'eager'}
        onLoad={handleLoad}
        onError={handleError}
        className={`${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
        {...props}
      />
      {hasError && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500 text-sm">
          Image not available
        </div>
      )}
    </div>
  );
};

// Hook for preloading assets
export const useAssetPreloader = (assets: Asset[]) => {
  const [loadingStates, setLoadingStates] = useState<Record<string, 'pending' | 'fulfilled' | 'rejected'>>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!assets.length) return;

    setIsLoading(true);
    const initialStates = assets.reduce((acc, asset) => {
      acc[asset.url] = 'pending';
      return acc;
    }, {} as Record<string, 'pending' | 'fulfilled' | 'rejected'>);
    
    setLoadingStates(initialStates);

    assetManager.preloadAssets(assets).then((results) => {
      const finalStates = results.reduce((acc, result, index) => {
        const asset = assets[index];
        acc[asset.url] = result.status;
        return acc;
      }, {} as Record<string, 'pending' | 'fulfilled' | 'rejected'>);

      setLoadingStates(finalStates);
      setIsLoading(false);
    });
  }, [assets]);

  return { loadingStates, isLoading };
};

export default assetManager;