# Integration-First Tenant Registration

## Overview

This document describes the new integration-first tenant registration workflow that requires users to connect at least one integration (Etsy or Shopify) during the registration process.

## Benefits

- **Reduced Abandonment**: Users have working integrations from day one
- **Better Onboarding**: Guided setup ensures proper configuration
- **Immediate Value**: Users can start importing products immediately after registration
- **Higher Engagement**: Active integrations lead to higher platform usage

## Registration Flow

### Step 1: Company and Admin Details
- Company name and subdomain selection
- Admin user account creation
- Integration platform selection (Etsy, Shopify, or both)
- Form validation and subdomain availability checking

### Step 2: OAuth Integration Connection
- OAuth URLs generated for selected platforms
- Users redirected to platform OAuth flows
- Secure state management with temporary registration sessions
- Real-time connection status updates

### Step 3: Registration Completion
- Verify all selected integrations are connected
- Create default subscription and complete tenant setup
- Generate login tokens and redirect to dashboard
- Show welcome banner with connected integrations

## API Endpoints

### Backend (FastAPI)
- `POST /api/v1/tenants/register/start` - Start multi-step registration
- `POST /api/v1/tenants/register/connect` - Connect integrations via OAuth
- `POST /api/v1/tenants/register/complete` - Complete registration and login
- `GET /api/v1/tenants/check-subdomain/{subdomain}` - Check subdomain availability

### Frontend Routes
- `/tenant-signup` - New integration-first registration (default)
- `/tenant-signup-old` - Simple registration without integrations (fallback)
- `/tenant-login` - Tenant admin login
- `/dashboard?welcome=true` - Dashboard with welcome banner for new users

## Technical Implementation

### Frontend Components
- **Multi-step progress indicator** - Visual progress through registration steps
- **Integration selection cards** - Visual platform selection with descriptions
- **OAuth callback handling** - Seamless integration connection within registration
- **Real-time validation** - Subdomain availability and form validation
- **Welcome banner** - Dashboard enhancement for newly registered tenants

### Backend Features
- **Session management** - Temporary registration sessions with 30-minute timeout
- **OAuth security** - Secure state management for OAuth flows
- **Automatic subscription creation** - Default "basic" plan setup
- **Integration tracking** - Monitor connected platforms during registration

### Security Features
- **CSRF protection** - OAuth state parameter validation
- **Session expiration** - 30-minute registration session timeout
- **Input validation** - Comprehensive Pydantic v2 validation
- **Error handling** - Graceful error handling with user feedback

## User Experience

### Primary Path (Integration-First)
1. User visits `/tenant-signup`
2. Fills out company and admin details
3. Selects desired integrations (Etsy, Shopify, or both)
4. Clicks "Continue to Integrations"
5. Redirected to OAuth flow for each selected platform
6. Returns to registration page after OAuth completion
7. Clicks "Complete Registration" when all integrations connected
8. Automatically logged in and redirected to dashboard with welcome banner

### Fallback Path (Simple Registration)
1. User visits `/tenant-signup-old` or clicks "Skip integrations setup"
2. Fills out company and admin details only
3. Clicks "Create Company Account"
4. Automatically logged in and redirected to dashboard
5. Can connect integrations later from dashboard

## Migration Strategy

- **Default route**: `/tenant-signup` now uses integration-first workflow
- **Backward compatibility**: Old workflow available at `/tenant-signup-old`
- **Progressive enhancement**: Links guide users to preferred workflow
- **Graceful fallback**: Simple registration still available for edge cases

## Configuration

### Environment Variables
```bash
# OAuth Redirect URIs (update for production)
ETSY_OAUTH_REDIRECT_URI=http://localhost:3000/tenant-signup?platform=etsy
SHOPIFY_OAUTH_REDIRECT_URI=http://localhost:3000/tenant-signup?platform=shopify

# OAuth Client IDs (configure with actual values)
ETSY_CLIENT_ID=your-etsy-client-id
SHOPIFY_CLIENT_ID=your-shopify-client-id
```

### Frontend Configuration
```typescript
// Frontend API calls use updated endpoints
apiService.startTenantRegistration(data)
apiService.connectIntegration(data) 
apiService.completeRegistration(data)
```

## Testing

### Manual Testing Steps
1. Navigate to `/tenant-signup`
2. Fill out registration form with valid data
3. Select integration platforms
4. Verify OAuth URLs are generated
5. Test OAuth callback handling (in production with real OAuth)
6. Confirm registration completion
7. Verify dashboard welcome banner appears
8. Test fallback registration at `/tenant-signup-old`

### Automated Testing
- Backend API endpoint tests
- Frontend component unit tests
- Integration OAuth flow tests
- End-to-end registration tests

## Deployment Notes

- Update OAuth redirect URIs in platform settings
- Configure environment variables for production
- Test OAuth flows with real platform credentials
- Monitor registration completion rates
- Update documentation and user guides