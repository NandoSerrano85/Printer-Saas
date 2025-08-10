// utils/assetManager.js
class AssetManager {
  constructor() {
    this.cdnBaseUrl = process.env.REACT_APP_CDN_BASE_URL || '';
    this.assetCache = new Map();
  }

  getTenantAssetUrl(tenant, assetPath) {
    const baseUrl = this.cdnBaseUrl || window.location.origin;
    return `${baseUrl}/tenant-assets/${tenant}/${assetPath}`;
  }

  getOptimizedImageUrl(src, options = {}) {
    const { width, height, quality = 80, format = 'webp' } = options;
    
    if (!this.cdnBaseUrl) {
      return src; // No CDN, return original
    }

    const params = new URLSearchParams();
    if (width) params.set('w', width);
    if (height) params.set('h', height);
    params.set('q', quality);
    params.set('f', format);

    return `${this.cdnBaseUrl}/optimize?url=${encodeURIComponent(src)}&${params}`;
  }

  async preloadAssets(assets) {
    const promises = assets.map(async (asset) => {
      if (this.assetCache.has(asset.url)) {
        return this.assetCache.get(asset.url);
      }

      const promise = new Promise((resolve, reject) => {
        if (asset.type === 'image') {
          const img = new Image();
          img.onload = () => resolve(asset.url);
          img.onerror = reject;
          img.src = asset.url;
        } else {
          // For other asset types, use fetch
          fetch(asset.url)
            .then(response => response.ok ? resolve(asset.url) : reject())
            .catch(reject);
        }
      });

      this.assetCache.set(asset.url, promise);
      return promise;
    });

    return Promise.allSettled(promises);
  }
}

export const assetManager = new AssetManager();

// Optimized Image Component
export const OptimizedImage = ({ 
  src, 
  alt, 
  width, 
  height, 
  className, 
  lazy = true,
  ...props 
}) => {
  const [imageSrc, setImageSrc] = useState(src);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef();

  useEffect(() => {
    // Generate optimized image URL
    const optimizedSrc = assetManager.getOptimizedImageUrl(src, {
      width,
      height,
    });
    
    setImageSrc(optimizedSrc);
  }, [src, width, height]);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
    // Fallback to original image
    setImageSrc(src);
  };

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse rounded" />
      )}
      <img
        ref={imgRef}
        src={imageSrc}
        alt={alt}
        loading={lazy ? 'lazy' : 'eager'}
        onLoad={handleLoad}
        onError={handleError}
        className={`${className} ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
        {...props}
      />
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500">
          Image not available
        </div>
      )}
    </div>
  );
};