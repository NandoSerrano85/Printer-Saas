// Base types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Tenant {
  id: string;
  subdomain: string;
  company_name: string;
  subscription_tier: string;
  database_schema: string;
  custom_domain?: string;
  settings: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Dashboard types
export interface DashboardStats {
  total_orders: number;
  total_revenue: number;
  active_templates: number;
  integration_status: {
    shopify: boolean;
    etsy: boolean;
  };
  recent_orders: Order[];
}

export interface AnalyticsData {
  revenue: {
    labels: string[];
    data: number[];
  };
  orders: {
    labels: string[];
    data: number[];
  };
  top_products: {
    name: string;
    sales: number;
  }[];
}

// Integration types
export interface IntegrationStatus {
  platform: 'shopify' | 'etsy';
  connected: boolean;
  shop_name?: string;
  last_sync?: string;
  error_message?: string;
}

// Shopify types
export interface ShopifyProduct {
  id: string;
  title: string;
  body_html: string;
  vendor: string;
  product_type: string;
  handle: string;
  status: 'active' | 'archived' | 'draft';
  images: ShopifyImage[];
  variants: ShopifyVariant[];
  created_at: string;
  updated_at: string;
}

export interface ShopifyImage {
  id: string;
  src: string;
  alt?: string;
  position: number;
}

export interface ShopifyVariant {
  id: string;
  title: string;
  price: string;
  sku?: string;
  inventory_quantity?: number;
  weight?: number;
}

export interface ShopifyOrder {
  id: string;
  name: string;
  email: string;
  total_price: string;
  subtotal_price: string;
  currency: string;
  financial_status: string;
  fulfillment_status?: string;
  line_items: ShopifyLineItem[];
  shipping_address: ShopifyAddress;
  billing_address: ShopifyAddress;
  created_at: string;
  updated_at: string;
}

export interface ShopifyLineItem {
  id: string;
  title: string;
  quantity: number;
  price: string;
  product_id: string;
  variant_id: string;
}

export interface ShopifyAddress {
  first_name: string;
  last_name: string;
  address1: string;
  address2?: string;
  city: string;
  province: string;
  country: string;
  zip: string;
  phone?: string;
}

export interface ShopifyCollection {
  id: string;
  title: string;
  body_html: string;
  handle: string;
  image?: ShopifyImage;
  products_count: number;
  created_at: string;
  updated_at: string;
}

// Etsy types
export interface EtsyListing {
  listing_id: string;
  title: string;
  description: string;
  price: string;
  currency_code: string;
  quantity: number;
  state: string;
  creation_timestamp: number;
  ending_timestamp: number;
  images: EtsyImage[];
}

export interface EtsyImage {
  listing_image_id: string;
  hex_code: string;
  red: number;
  green: number;
  blue: number;
  hue: number;
  saturation: number;
  brightness: number;
  is_black_and_white: boolean;
  creation_tsz: number;
  listing_id: string;
  rank: number;
  url_75x75: string;
  url_170x135: string;
  url_570xN: string;
  url_fullxfull: string;
  full_height: number;
  full_width: number;
}

export interface EtsyOrder {
  receipt_id: string;
  receipt_type: number;
  seller_user_id: number;
  seller_email: string;
  buyer_user_id: number;
  buyer_email: string;
  name: string;
  first_line: string;
  second_line?: string;
  city: string;
  state?: string;
  zip: string;
  country_id: number;
  payment_method: string;
  payment_email: string;
  message_from_seller?: string;
  message_from_buyer?: string;
  was_paid: boolean;
  total_tax_cost: string;
  total_vat_cost: string;
  total_price: string;
  total_shipping_cost: string;
  currency_code: string;
  message_from_payment?: string;
  shipped: boolean;
  creation_tsz: number;
  last_modified_tsz: number;
}

// Template types
export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  thumbnail_url?: string;
  design_data: any; // JSON object for design configuration
  is_public: boolean;
  created_by: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateCategory {
  id: string;
  name: string;
  description: string;
  templates_count: number;
}

// Order types
export interface Order {
  id: string;
  order_number: string;
  platform: 'shopify' | 'etsy' | 'manual';
  platform_order_id?: string;
  customer_email: string;
  customer_name: string;
  total_amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  items: OrderItem[];
  shipping_address: Address;
  billing_address: Address;
  tracking_numbers: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  product_name: string;
  product_id?: string;
  variant_id?: string;
  quantity: number;
  unit_price: number;
  template_id?: string;
  customization_data?: any;
  upload_urls?: string[];
  preview_image_url?: string;
  processing_status: 'pending' | 'processing' | 'ready' | 'printed' | 'shipped';
}

export interface Address {
  first_name: string;
  last_name: string;
  company?: string;
  address1: string;
  address2?: string;
  city: string;
  province: string;
  country: string;
  zip: string;
  phone?: string;
}

// Form types
export interface LoginForm {
  email: string;
  password: string;
}

export interface TenantForm {
  subdomain: string;
  company_name: string;
  subscription_tier: string;
  custom_domain?: string;
  settings?: Record<string, any>;
}

export interface TemplateForm {
  name: string;
  description: string;
  category: string;
  design_data: any;
  is_public: boolean;
}

export interface BatchUpdateForm {
  product_ids: string[];
  updates: {
    title?: string;
    price?: string;
    inventory_quantity?: number;
    status?: string;
  };
}

// UI State types
export interface LoadingState {
  [key: string]: boolean;
}

export interface ErrorState {
  [key: string]: string | null;
}

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

// Additional TypeScript conversion types
export interface ComponentProps {
  children?: React.ReactNode;
  className?: string;
}

export interface ThemeConfig {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    text: string;
  };
  fonts: {
    primary: string;
    secondary: string;
  };
}

export interface TenantContextValue {
  tenantId: string | null;
  tenantData: Tenant | null;
  isLoading: boolean;
  error: string | null;
  refreshTenant: () => Promise<void>;
}

export interface AppStoreState {
  user: User | null;
  tenant: Tenant | null;
  loading: LoadingState;
  errors: ErrorState;
  setUser: (user: User | null) => void;
  setTenant: (tenant: Tenant | null) => void;
  setLoading: (key: string, loading: boolean) => void;
  setError: (key: string, error: string | null) => void;
  clearErrors: () => void;
}

export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, any>;
  timestamp?: number;
}

export interface PWAInstallPrompt {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export interface ApiQueryOptions {
  enabled?: boolean;
  refetchOnWindowFocus?: boolean;
  retry?: number;
  retryDelay?: number;
}

export interface ApiQueryResult<T> {
  data: T | undefined;
  error: Error | null;
  isLoading: boolean;
  isError: boolean;
  refetch: () => Promise<void>;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
}

export interface HealthMetrics {
  responseTime: number;
  status: 'healthy' | 'degraded' | 'down';
  lastCheck: number;
}

export interface AssetConfig {
  baseUrl: string;
  version: string;
  cacheDuration: number;
}

export interface MicrofrontendConfig {
  name: string;
  url: string;
  scope: string;
  module: string;
}

export interface SecurityConfig {
  encryptionKey: string;
  tokenExpiry: number;
  maxAttempts: number;
}

export interface LogLevel {
  DEBUG: 'debug';
  INFO: 'info';
  WARN: 'warn';
  ERROR: 'error';
}

export interface LogEntry {
  level: keyof LogLevel;
  message: string;
  timestamp: number;
  metadata?: Record<string, any>;
}