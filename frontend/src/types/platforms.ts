// Platform-specific field definitions based on their APIs

export interface PlatformFieldDefinition {
  name: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'multiselect' | 'boolean' | 'image' | 'price';
  required: boolean;
  label: string;
  placeholder?: string;
  helpText?: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    minLength?: number;
    maxLength?: number;
  };
  options?: Array<{ value: string; label: string }>;
  dependsOn?: string; // Field that this field depends on
  showWhen?: any; // Value that dependsOn field should have
}

export interface PlatformCategory {
  id: string;
  name: string;
  platform: 'shopify' | 'etsy';
  fields: PlatformFieldDefinition[];
  parentCategory?: string;
}

// Shopify Categories and Fields
export const SHOPIFY_CATEGORIES: PlatformCategory[] = [
  {
    id: 'apparel',
    name: 'Apparel & Accessories',
    platform: 'shopify',
    fields: [
      {
        name: 'title',
        type: 'text',
        required: true,
        label: 'Product Title',
        placeholder: 'Enter product title',
        validation: { minLength: 3, maxLength: 255 },
      },
      {
        name: 'description',
        type: 'textarea',
        required: true,
        label: 'Product Description',
        placeholder: 'Describe your product',
        validation: { minLength: 10, maxLength: 5000 },
      },
      {
        name: 'price',
        type: 'price',
        required: true,
        label: 'Price',
        placeholder: '0.00',
        validation: { min: 0.01 },
      },
      {
        name: 'compare_at_price',
        type: 'price',
        required: false,
        label: 'Compare at Price',
        placeholder: '0.00',
        helpText: 'Original price before discount',
      },
      {
        name: 'product_type',
        type: 'select',
        required: true,
        label: 'Product Type',
        options: [
          { value: 't-shirt', label: 'T-Shirt' },
          { value: 'hoodie', label: 'Hoodie' },
          { value: 'tank-top', label: 'Tank Top' },
          { value: 'long-sleeve', label: 'Long Sleeve' },
          { value: 'polo', label: 'Polo Shirt' },
          { value: 'jacket', label: 'Jacket' },
          { value: 'hat', label: 'Hat/Cap' },
          { value: 'bag', label: 'Bag' },
          { value: 'accessories', label: 'Accessories' },
        ],
      },
      {
        name: 'vendor',
        type: 'text',
        required: false,
        label: 'Vendor/Brand',
        placeholder: 'Brand name',
      },
      {
        name: 'tags',
        type: 'text',
        required: false,
        label: 'Tags',
        placeholder: 'shirt, cotton, casual (comma separated)',
        helpText: 'Comma-separated tags for better discoverability',
      },
      {
        name: 'weight',
        type: 'number',
        required: false,
        label: 'Weight (grams)',
        placeholder: '150',
        validation: { min: 1 },
      },
      {
        name: 'requires_shipping',
        type: 'boolean',
        required: false,
        label: 'Requires Shipping',
      },
      {
        name: 'variant_option1',
        type: 'select',
        required: false,
        label: 'Variant Option 1',
        options: [
          { value: 'Size', label: 'Size' },
          { value: 'Color', label: 'Color' },
          { value: 'Material', label: 'Material' },
          { value: 'Style', label: 'Style' },
        ],
      },
      {
        name: 'variant_values1',
        type: 'text',
        required: false,
        label: 'Variant Values 1',
        placeholder: 'S, M, L, XL (comma separated)',
        dependsOn: 'variant_option1',
        helpText: 'Comma-separated values for the first variant option',
      },
      {
        name: 'variant_option2',
        type: 'select',
        required: false,
        label: 'Variant Option 2',
        options: [
          { value: 'Size', label: 'Size' },
          { value: 'Color', label: 'Color' },
          { value: 'Material', label: 'Material' },
          { value: 'Style', label: 'Style' },
        ],
      },
      {
        name: 'variant_values2',
        type: 'text',
        required: false,
        label: 'Variant Values 2',
        placeholder: 'Red, Blue, Green (comma separated)',
        dependsOn: 'variant_option2',
        helpText: 'Comma-separated values for the second variant option',
      },
    ],
  },
  {
    id: 'home-living',
    name: 'Home & Living',
    platform: 'shopify',
    fields: [
      {
        name: 'title',
        type: 'text',
        required: true,
        label: 'Product Title',
        validation: { minLength: 3, maxLength: 255 },
      },
      {
        name: 'description',
        type: 'textarea',
        required: true,
        label: 'Product Description',
        validation: { minLength: 10, maxLength: 5000 },
      },
      {
        name: 'price',
        type: 'price',
        required: true,
        label: 'Price',
        validation: { min: 0.01 },
      },
      {
        name: 'product_type',
        type: 'select',
        required: true,
        label: 'Product Type',
        options: [
          { value: 'mug', label: 'Mug' },
          { value: 'pillow', label: 'Pillow' },
          { value: 'blanket', label: 'Blanket' },
          { value: 'poster', label: 'Poster' },
          { value: 'canvas', label: 'Canvas Print' },
          { value: 'coaster', label: 'Coaster' },
          { value: 'mousepad', label: 'Mouse Pad' },
          { value: 'phone-case', label: 'Phone Case' },
        ],
      },
      {
        name: 'material',
        type: 'select',
        required: false,
        label: 'Material',
        options: [
          { value: 'ceramic', label: 'Ceramic' },
          { value: 'cotton', label: 'Cotton' },
          { value: 'polyester', label: 'Polyester' },
          { value: 'canvas', label: 'Canvas' },
          { value: 'paper', label: 'Paper' },
          { value: 'plastic', label: 'Plastic' },
          { value: 'rubber', label: 'Rubber' },
        ],
      },
      {
        name: 'dimensions',
        type: 'text',
        required: false,
        label: 'Dimensions',
        placeholder: '11oz, 15oz or 8x10 inches',
        helpText: 'Product dimensions or size options',
      },
    ],
  },
];

// Etsy Categories and Fields
export const ETSY_CATEGORIES: PlatformCategory[] = [
  {
    id: 'art-collectibles',
    name: 'Art & Collectibles',
    platform: 'etsy',
    fields: [
      {
        name: 'title',
        type: 'text',
        required: true,
        label: 'Listing Title',
        validation: { minLength: 3, maxLength: 140 },
        helpText: 'Etsy titles are limited to 140 characters',
      },
      {
        name: 'description',
        type: 'textarea',
        required: true,
        label: 'Description',
        validation: { minLength: 10, maxLength: 13000 },
      },
      {
        name: 'price',
        type: 'price',
        required: true,
        label: 'Price',
        validation: { min: 0.20 }, // Etsy minimum
      },
      {
        name: 'who_made',
        type: 'select',
        required: true,
        label: 'Who Made It?',
        options: [
          { value: 'i_did', label: 'I did' },
          { value: 'collective', label: 'A member of my shop' },
          { value: 'someone_else', label: 'Another company or person' },
        ],
      },
      {
        name: 'when_made',
        type: 'select',
        required: true,
        label: 'When Was It Made?',
        options: [
          { value: 'made_to_order', label: 'Made to order' },
          { value: '2020_2023', label: '2020-2023' },
          { value: '2010_2019', label: '2010-2019' },
          { value: '2004_2009', label: '2004-2009' },
          { value: 'before_2004', label: 'Before 2004' },
          { value: '1990s', label: '1990s' },
          { value: '1980s', label: '1980s' },
          { value: '1970s', label: '1970s' },
          { value: '1960s', label: '1960s' },
          { value: '1950s', label: '1950s' },
          { value: '1940s', label: '1940s' },
          { value: 'before_1940', label: 'Before 1940' },
        ],
      },
      {
        name: 'category_id',
        type: 'select',
        required: true,
        label: 'Category',
        options: [
          { value: '69150467', label: 'Prints' },
          { value: '69150425', label: 'Digital Prints' },
          { value: '69150353', label: 'Drawings & Illustrations' },
          { value: '69150355', label: 'Mixed Media & Collage' },
          { value: '69150357', label: 'Painting' },
          { value: '69150359', label: 'Photography' },
        ],
      },
      {
        name: 'materials',
        type: 'text',
        required: true,
        label: 'Materials',
        placeholder: 'paper, ink, digital (comma separated)',
        validation: { minLength: 1, maxLength: 200 },
        helpText: 'List up to 13 materials, separated by commas',
      },
      {
        name: 'tags',
        type: 'text',
        required: true,
        label: 'Tags',
        placeholder: 'art, print, wall decor (comma separated)',
        validation: { minLength: 1, maxLength: 130 },
        helpText: 'Up to 13 tags, each 1-20 characters',
      },
      {
        name: 'processing_min',
        type: 'number',
        required: false,
        label: 'Processing Time (Min Days)',
        validation: { min: 1, max: 120 },
      },
      {
        name: 'processing_max',
        type: 'number',
        required: false,
        label: 'Processing Time (Max Days)',
        validation: { min: 1, max: 120 },
      },
    ],
  },
  {
    id: 'clothing',
    name: 'Clothing',
    platform: 'etsy',
    fields: [
      {
        name: 'title',
        type: 'text',
        required: true,
        label: 'Listing Title',
        validation: { minLength: 3, maxLength: 140 },
      },
      {
        name: 'description',
        type: 'textarea',
        required: true,
        label: 'Description',
        validation: { minLength: 10, maxLength: 13000 },
      },
      {
        name: 'price',
        type: 'price',
        required: true,
        label: 'Price',
        validation: { min: 0.20 },
      },
      {
        name: 'who_made',
        type: 'select',
        required: true,
        label: 'Who Made It?',
        options: [
          { value: 'i_did', label: 'I did' },
          { value: 'collective', label: 'A member of my shop' },
          { value: 'someone_else', label: 'Another company or person' },
        ],
      },
      {
        name: 'when_made',
        type: 'select',
        required: true,
        label: 'When Was It Made?',
        options: [
          { value: 'made_to_order', label: 'Made to order' },
          { value: '2020_2023', label: '2020-2023' },
          { value: '2010_2019', label: '2010-2019' },
        ],
      },
      {
        name: 'category_id',
        type: 'select',
        required: true,
        label: 'Category',
        options: [
          { value: '69152558', label: 'Unisex Adult Clothing' },
          { value: '69152560', label: 'Women\'s Clothing' },
          { value: '69152562', label: 'Men\'s Clothing' },
          { value: '69152564', label: 'Baby & Children\'s Clothing' },
        ],
      },
      {
        name: 'materials',
        type: 'text',
        required: true,
        label: 'Materials',
        placeholder: 'cotton, polyester (comma separated)',
        validation: { minLength: 1, maxLength: 200 },
      },
      {
        name: 'size_scale',
        type: 'select',
        required: false,
        label: 'Size Scale',
        options: [
          { value: 'us', label: 'US' },
          { value: 'uk', label: 'UK' },
          { value: 'eu', label: 'EU' },
          { value: 'custom', label: 'Custom' },
        ],
      },
      {
        name: 'size_options',
        type: 'text',
        required: false,
        label: 'Size Options',
        placeholder: 'XS, S, M, L, XL (comma separated)',
        helpText: 'Available sizes for this item',
      },
    ],
  },
  {
    id: 'home-living-etsy',
    name: 'Home & Living',
    platform: 'etsy',
    fields: [
      {
        name: 'title',
        type: 'text',
        required: true,
        label: 'Listing Title',
        validation: { minLength: 3, maxLength: 140 },
      },
      {
        name: 'description',
        type: 'textarea',
        required: true,
        label: 'Description',
        validation: { minLength: 10, maxLength: 13000 },
      },
      {
        name: 'price',
        type: 'price',
        required: true,
        label: 'Price',
        validation: { min: 0.20 },
      },
      {
        name: 'who_made',
        type: 'select',
        required: true,
        label: 'Who Made It?',
        options: [
          { value: 'i_did', label: 'I did' },
          { value: 'collective', label: 'A member of my shop' },
        ],
      },
      {
        name: 'when_made',
        type: 'select',
        required: true,
        label: 'When Was It Made?',
        options: [
          { value: 'made_to_order', label: 'Made to order' },
          { value: '2020_2023', label: '2020-2023' },
        ],
      },
      {
        name: 'category_id',
        type: 'select',
        required: true,
        label: 'Category',
        options: [
          { value: '69150425', label: 'Kitchen & Dining' },
          { value: '69150467', label: 'Home Decor' },
          { value: '69150353', label: 'Bedding' },
          { value: '69150355', label: 'Bathroom' },
        ],
      },
      {
        name: 'materials',
        type: 'text',
        required: true,
        label: 'Materials',
        placeholder: 'ceramic, vinyl, cotton (comma separated)',
        validation: { minLength: 1, maxLength: 200 },
      },
      {
        name: 'occasion',
        type: 'select',
        required: false,
        label: 'Occasion',
        options: [
          { value: 'anniversary', label: 'Anniversary' },
          { value: 'baptism', label: 'Baptism' },
          { value: 'bar_mitzvah', label: 'Bar/Bat Mitzvah' },
          { value: 'birthday', label: 'Birthday' },
          { value: 'christmas', label: 'Christmas' },
          { value: 'confirmation', label: 'Confirmation' },
          { value: 'easter', label: 'Easter' },
          { value: 'engagement', label: 'Engagement' },
          { value: 'fathers_day', label: 'Father\'s Day' },
          { value: 'graduation', label: 'Graduation' },
          { value: 'halloween', label: 'Halloween' },
          { value: 'hanukkah', label: 'Hanukkah' },
          { value: 'housewarming', label: 'Housewarming' },
          { value: 'kwanzaa', label: 'Kwanzaa' },
          { value: 'mothers_day', label: 'Mother\'s Day' },
          { value: 'new_baby', label: 'New Baby' },
          { value: 'new_years', label: 'New Year\'s' },
          { value: 'prom', label: 'Prom' },
          { value: 'quinceanera', label: 'Quinceañera' },
          { value: 'retirement', label: 'Retirement' },
          { value: 'sweet_16', label: 'Sweet 16' },
          { value: 'sympathy', label: 'Sympathy' },
          { value: 'thanksgiving', label: 'Thanksgiving' },
          { value: 'valentines', label: 'Valentine\'s Day' },
          { value: 'wedding', label: 'Wedding' },
        ],
      },
    ],
  },
];

// Helper function to get categories for a platform
export const getCategoriesForPlatform = (platform: 'shopify' | 'etsy'): PlatformCategory[] => {
  return platform === 'shopify' ? SHOPIFY_CATEGORIES : ETSY_CATEGORIES;
};

// Helper function to get all available platforms
export const getAvailablePlatforms = (): Array<{ value: 'shopify' | 'etsy'; label: string }> => [
  { value: 'shopify', label: 'Shopify' },
  { value: 'etsy', label: 'Etsy' },
];

// Helper function to merge field values with defaults
export const getDefaultFieldValues = (fields: PlatformFieldDefinition[]): Record<string, any> => {
  const defaults: Record<string, any> = {};
  
  fields.forEach(field => {
    switch (field.type) {
      case 'boolean':
        defaults[field.name] = false;
        break;
      case 'number':
      case 'price':
        defaults[field.name] = field.validation?.min || 0;
        break;
      case 'multiselect':
        defaults[field.name] = [];
        break;
      default:
        defaults[field.name] = '';
    }
  });
  
  return defaults;
};