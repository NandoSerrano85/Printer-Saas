Etsy Seller Automater Frontend Architecture
Multi-Tenant SaaS Deep Dive for QNAP NAS Deployment
1. Overview
This document provides a comprehensive technical deep dive into the React.js frontend architecture
for the Etsy Seller Automater, specifically designed to integrate with the multi-tenant SaaS backend
deployed on your QNAP TBS-464 NAS. The frontend architecture emphasizes scalability, tenant
isolation, and optimal performance within the Docker containerized environment.
2. Frontend Technology Stack
Core Technologies:
React 18+: Modern functional components with hooks
JavaScript/TypeScript: TypeScript recommended for production builds
Tailwind CSS: Utility-first CSS framework for responsive design
Vite: Fast build tool and development server
Docker: Containerized deployment matching backend architecture
Key Libraries & Dependencies:
Axios/Fetch API: HTTP client for backend communication
React Router v6: Client-side routing and navigation
React Query/TanStack Query: Server state management and caching
Zustand: Lightweight client-side state management
React Hook Form: Form validation and handling
Framer Motion: UI animations and transitions
Chart.js/Recharts: Analytics dashboard visualizations
3. Multi-Tenant Frontend Architecture
## 3.1 Tenant Context System
```javascript
// contexts/TenantContext.js // contexts/TenantContext.js
importimport{{ createContext  createContext,, useContext  useContext,, useState useState,, useEffect  useEffect }}fromfrom'react''react';;
constconstTenantContext TenantContext==createContext createContext(());;
exportexportconstconstTenantProvider TenantProvider==(({{ children  children }}))=>=>{{
constconst[[tenanttenant,, setTenant setTenant]]==useStateuseState((nullnull));;
constconst[[isLoadingisLoading,, setIsLoading  setIsLoading]]==useStateuseState((truetrue));;
useEffectuseEffect(((())=>=>{{
// Extract tenant from subdomain or path // Extract tenant from subdomain or path
constconstdetectTenant detectTenant==(())=>=>{{
constconst hostname  hostname ==windowwindow..locationlocation..hostnamehostname;;
constconst subdomain  subdomain == hostname hostname..splitsplit(('.''.'))[[00]];;
// tenant1.localhost, tenant2.localhost for local dev // tenant1.localhost, tenant2.localhost for local dev
// tenant1.yourdomain.com for production // tenant1.yourdomain.com for production
ifif((subdomain subdomain !==!=='localhost''localhost'&&&& subdomain  subdomain !==!=='www''www')){{
returnreturn subdomain  subdomain;;
}}
// Fallback to path-based routing: /tenant1/dashboard // Fallback to path-based routing: /tenant1/dashboard
constconst pathSegments  pathSegments ==windowwindow..locationlocation..pathnamepathname..splitsplit(('/''/'));;
returnreturn pathSegments  pathSegments[[11]]||||'default''default';;
}};;
constconst tenantId  tenantId ==detectTenant detectTenant(());;
setTenantsetTenant(({{
idid:: tenantId tenantId,,
namename:: tenantId tenantId,,
themetheme::getTenantTheme getTenantTheme((tenantIdtenantId)),,
configconfig::getTenantConfig getTenantConfig((tenantIdtenantId))
}}));;
setIsLoading setIsLoading((falsefalse));;
}},,[[]]));;
returnreturn((
<<TenantContext TenantContext..ProviderProvider value value=={{{{ tenant tenant,, setTenant setTenant,, isLoading  isLoading }}}}>>
{{childrenchildren}}
<<//TenantContext TenantContext..ProviderProvider>>
));;
}};;
## 3.2 Dynamic Theming & BrandingexportexportconstconstuseTenantuseTenant==(())=>=>{{
constconst context  context ==useContext useContext((TenantContext TenantContext));;
ifif((!!contextcontext)){{
throwthrownewnewErrorError(('useTenant must be used within TenantProvider' 'useTenant must be used within TenantProvider'));;
}}
returnreturn context context;;
}};;
```
```javascript
// utils/tenantThemes.js // utils/tenantThemes.js
exportexportconstconstgetTenantTheme getTenantTheme==((tenantIdtenantId))=>=>{{
constconst themes  themes =={{
tenant1tenant1::{{
primaryprimary::'#3B82F6''#3B82F6',,// Blue// Blue
secondarysecondary::'#10B981''#10B981',,// Green// Green
accentaccent::'#F59E0B''#F59E0B',,// Amber// Amber
logologo::'/logos/tenant1-logo.svg' '/logos/tenant1-logo.svg',,
faviconfavicon::'/favicons/tenant1.ico' '/favicons/tenant1.ico'
}},,
tenant2tenant2::{{
primaryprimary::'#EF4444''#EF4444',,// Red// Red
secondarysecondary::'#8B5CF6''#8B5CF6',,// Purple// Purple
accentaccent::'#F97316''#F97316',,// Orange// Orange
logologo::'/logos/tenant2-logo.svg' '/logos/tenant2-logo.svg',,
faviconfavicon::'/favicons/tenant2.ico' '/favicons/tenant2.ico'
}},,
defaultdefault::{{
primaryprimary::'#6B7280''#6B7280',,// Gray// Gray
secondarysecondary::'#374151''#374151',,
accentaccent::'#9CA3AF''#9CA3AF',,
logologo::'/logos/default-logo.svg' '/logos/default-logo.svg',,
faviconfavicon::'/favicon.ico''/favicon.ico'
}}
}};;
returnreturn themes themes[[tenantIdtenantId]]|||| themes themes..defaultdefault;;
}};;
// components/ThemeProvider.jsx // components/ThemeProvider.jsx
importimport{{ useTenant  useTenant }}fromfrom'../contexts/TenantContext' '../contexts/TenantContext';;
exportexportconstconstThemeProvider ThemeProvider==(({{ children  children }}))=>=>{{
constconst{{ tenant  tenant }}==useTenantuseTenant(());;
useEffectuseEffect(((())=>=>{{
ifif((tenanttenant?.?.themetheme)){{
document document..documentElement documentElement..stylestyle..setProperty setProperty(('--primary-color''--primary-color',, tenant tenant..themetheme..primaryprimary));;
document document..documentElement documentElement..stylestyle..setProperty setProperty(('--secondary-color''--secondary-color',, tenant tenant..themetheme..secondarysecondary));;
document document..documentElement documentElement..stylestyle..setProperty setProperty(('--accent-color''--accent-color',, tenant tenant..themetheme..accentaccent));;
// Update favicon dynamically // Update favicon dynamically
constconst favicon  favicon ==document document..querySelector querySelector(('link[rel="icon"]''link[rel="icon"]'));;
4. Component Architecture
## 4.1 Feature-Based Structure
## 4.2 Core Componentsifif((faviconfavicon)){{
favicon         favicon..hrefhref== tenant tenant..themetheme..faviconfavicon;;
}}
}}
}},,[[tenanttenant]]));;
returnreturn<<div className div className=="theme-container""theme-container">>{{childrenchildren}}<<//divdiv>>;;
}};;
frontend/frontend/
├── src/ ├── src/
│   ├── components/ │   ├── components/
│   │   ├──  common/           # Shared UI components │   │   ├──  common/           # Shared UI components
│   │   │   ├ ──  Layout/│   │   │   ├ ──  Layout/
│   │   │   ├ ──  Forms/│   │   │   ├ ──  Forms/
│   │   │   ├ ──  Navigation/ │   │   │   ├ ──  Navigation/
│   │   │   └──  UI/│   │   │   └──  UI/
│   │   ├──  features/         # Feature-specific components │   │   ├──  features/         # Feature-specific components
│   │   │   ├ ──  Analytics/ │   │   │   ├ ──  Analytics/
│   │   │   ├ ──  Designs/ │   │   │   ├ ──  Designs/
│   │   │   ├ ──  MaskCreator/ │   │   │   ├ ──  MaskCreator/
│   │   │   ├ ──  OAuth/│   │   │   ├ ──  OAuth/
│   │   │   └──  ShopManagement/ │   │   │   └──  ShopManagement/
│   │   └──  tenant/           # Tenant-specific overrides │   │   └──  tenant/           # Tenant-specific overrides
│   │       ├ ──  tenant1/ │   │       ├ ──  tenant1/
│   │       └──  tenant2/ │   │       └──  tenant2/
│   ├── hooks/                # Custom React hooks │   ├── hooks/                # Custom React hooks
│   ├── services/            # API services and utilities │   ├── services/            # API services and utilities
│   ├── stores/              # State management │   ├── stores/              # State management
│   ├── utils/               # Utility functions │   ├── utils/               # Utility functions
│   ├── contexts/            # React contexts │   ├── contexts/            # React contexts
│   └── pages/               # Page components │   └── pages/               # Page components
└── public/ └── public/
├── logos/               # Tenant logos ├── logos/               # Tenant logos
├── favicons/           # Tenant favicons ├── favicons/           # Tenant favicons
└── tenant-assets/       # Tenant-specific assets └── tenant-assets/       # Tenant-specific assets
Layout Component with Multi-Tenant Support:
Tenant-Aware API Service:javascript
// components/common/Layout/AppLayout.jsx // components/common/Layout/AppLayout.jsx
importimport{{ useTenant  useTenant }}fromfrom'../../../contexts/TenantContext' '../../../contexts/TenantContext';;
importimport{{NavigationNavigation}}fromfrom'./Navigation''./Navigation';;
importimport{{SidebarSidebar}}fromfrom'./Sidebar''./Sidebar';;
importimport{{HeaderHeader}}fromfrom'./Header''./Header';;
exportexportconstconstAppLayoutAppLayout==(({{ children  children }}))=>=>{{
constconst{{ tenant tenant,, isLoading  isLoading }}==useTenantuseTenant(());;
ifif((isLoadingisLoading)){{
returnreturn<<LoadingSpinner LoadingSpinner//>>;;
}}
returnreturn((
<<div className div className=="min-h-screen bg-gray-50" "min-h-screen bg-gray-50">>
<<HeaderHeader tenant tenant=={{tenanttenant}}//>>
<<div className div className=="flex""flex">>
<<SidebarSidebar tenant tenant=={{tenanttenant}}//>>
<<main className main className=="flex-1 p-6""flex-1 p-6">>
<<div className div className=="max-w-7xl mx-auto""max-w-7xl mx-auto">>
{{childrenchildren}}
<<//divdiv>>
<<//mainmain>>
<<//divdiv>>
<<//divdiv>>
));;
}};;
```
```javascript
// services/apiService.js // services/apiService.js
importimportaxiosaxiosfromfrom'axios''axios';;
classclassApiServiceApiService{{
constructor constructor(()){{
thisthis..baseURLbaseURL== process process..envenv..REACT_APP_API_BASE_URL REACT_APP_API_BASE_URL||||'http://localhost:3003' 'http://localhost:3003';;
thisthis..clientclient== axios axios..createcreate(({{
baseURLbaseURL::thisthis..baseURLbaseURL,,
timeouttimeout::1000010000,,
}}));;
// Add tenant header to all requests // Add tenant header to all requests
thisthis..clientclient..interceptors interceptors..requestrequest..useuse((((configconfig))=>=>{{
constconst tenant  tenant ==thisthis..getCurrentTenant getCurrentTenant(());;
ifif((tenanttenant)){{
config        config..headersheaders[['X-Tenant-ID''X-Tenant-ID']]== tenant tenant..idid;;
}}
constconst token  token ==localStorage localStorage..getItemgetItem(('auth_token''auth_token'));;
ifif((tokentoken)){{
config        config..headersheaders..Authorization Authorization==``Bearer Bearer ${${tokentoken}}``;;
}}
returnreturn config config;;
}}));;
// Handle tenant-specific errors // Handle tenant-specific errors
thisthis..clientclient..interceptors interceptors..responseresponse..useuse((
((responseresponse))=>=> response response,,
((errorerror))=>=>{{
ifif((errorerror..responseresponse?.?.status status ======403403)){{
// Tenant access denied // Tenant access denied
windowwindow..locationlocation..hrefhref=='/unauthorized''/unauthorized';;
}}
returnreturnPromisePromise..rejectreject((errorerror));;
}}
));;
}}
getCurrentTenant getCurrentTenant(()){{
// Extract from URL or context // Extract from URL or context
constconst hostname  hostname ==windowwindow..locationlocation..hostnamehostname;;
constconst subdomain  subdomain == hostname hostname..splitsplit(('.''.'))[[00]];;
5. Feature Implementation
## 5.1 OAuth Integration Componentreturnreturn{{idid:: subdomain  subdomain }};;
}}
// Etsy-specific API methods // Etsy-specific API methods
asyncasyncgetShopAnalytics getShopAnalytics((params params =={{}})){{
constconst response  response ==awaitawaitthisthis..clientclient..getget(('/api/shop-analytics''/api/shop-analytics',,{{ params  params }}));;
returnreturn response response..datadata;;
}}
asyncasyncgetTopSellers getTopSellers((yearyear)){{
constconst response  response ==awaitawaitthisthis..clientclient..getget((``/api/top-sellers?year=/api/top-sellers?year=${${yearyear}}``));;
returnreturn response response..datadata;;
}}
asyncasyncgetLocalImages getLocalImages(()){{
constconst response  response ==awaitawaitthisthis..clientclient..getget(('/api/local-images''/api/local-images'));;
returnreturn response response..datadata;;
}}
asyncasyncsaveMaskData saveMaskData((maskDatamaskData)){{
constconst response  response ==awaitawaitthisthis..clientclient..postpost(('/api/masks''/api/masks',, maskData maskData));;
returnreturn response response..datadata;;
}}
}}
exportexportconstconst apiService  apiService ==newnewApiServiceApiService(());;
```
```javascript
// components/features/OAuth/EtsyOAuthConnect.jsx // components/features/OAuth/EtsyOAuthConnect.jsx
importimport{{ useState useState,, useEffect  useEffect }}fromfrom'react''react';;
importimport{{ useTenant  useTenant }}fromfrom'../../../contexts/TenantContext' '../../../contexts/TenantContext';;
importimport{{ apiService  apiService }}fromfrom'../../../services/apiService' '../../../services/apiService';;
exportexportconstconstEtsyOAuthConnect EtsyOAuthConnect==(())=>=>{{
constconst{{ tenant  tenant }}==useTenantuseTenant(());;
constconst[[isConnected isConnected,, setIsConnected  setIsConnected]]==useStateuseState((falsefalse));;
constconst[[isLoadingisLoading,, setIsLoading  setIsLoading]]==useStateuseState((falsefalse));;
constconsthandleConnect handleConnect==asyncasync(())=>=>{{
setIsLoading setIsLoading((truetrue));;
trytry{{
constconst oauthData  oauthData ==awaitawait apiService  apiService..getOAuthConfig getOAuthConfig(());;
// Build OAuth URL with tenant-specific redirect // Build OAuth URL with tenant-specific redirect
constconst params  params ==newnewURLSearchParams URLSearchParams(({{
client_idclient_id:: oauthData  oauthData..client_idclient_id,,
redirect_uri redirect_uri::``${${windowwindow..locationlocation..originorigin}}/oauth/redirect/oauth/redirect``,,
scopescope:: oauthData  oauthData..scopescope,,
statestate:: tenant tenant..idid,,// Include tenant ID in state // Include tenant ID in state
response_type response_type::'code''code',,
code_challenge_method code_challenge_method::'S256''S256',,
code_challenge code_challenge:: oauthData  oauthData..code_challenge code_challenge,,
}}));;
windowwindow..locationlocation..hrefhref==``https://www.etsy.com/oauth/connect? https://www.etsy.com/oauth/connect?${${paramsparams}}``;;
}}catchcatch((errorerror)){{
consoleconsole..errorerror(('OAuth connection failed:' 'OAuth connection failed:',, error error));;
}}finallyfinally{{
setIsLoading setIsLoading((falsefalse));;
}}
}};;
returnreturn((
<<div className div className=="bg-white rounded-lg shadow-md p-6" "bg-white rounded-lg shadow-md p-6">>
<<h2 className h2 className=="text-2xl font-bold mb-4" "text-2xl font-bold mb-4">>ConnectConnectYourYourEtsyEtsyShopShop<<//h2h2>>
{{!!isConnected isConnected ??((
<<buttonbutton
onClick           onClick=={{handleConnect handleConnect}}
disabled           disabled=={{isLoadingisLoading}}
className           className=="bg-primary text-white px-6 py-3 rounded-lg hover:bg-primary-dark disabled:opacity-50" "bg-primary text-white px-6 py-3 rounded-lg hover:bg-primary-dark disabled:opacity-50"
>>
## 5.2 Analytics Dashboard{{isLoading isLoading ??'Connecting...''Connecting...'::'Connect to Etsy''Connect to Etsy'}}
<<//buttonbutton>>
))::((
<<div className div className=="text-green-600""text-green-600">>
✅           ✅ Successfully Successfully connected to  connected to EtsyEtsy!!
<<//divdiv>>
))}}
<<//divdiv>>
));;
}};;
```
```javascript
// components/features/Analytics/AnalyticsDashboard.jsx // components/features/Analytics/AnalyticsDashboard.jsx
importimport{{ useState useState,, useEffect  useEffect }}fromfrom'react''react';;
importimport{{LineChartLineChart,,LineLine,,XAxisXAxis,,YAxisYAxis,,CartesianGrid CartesianGrid,,TooltipTooltip,,ResponsiveContainer ResponsiveContainer}}fromfrom'recharts''recharts';;
importimport{{ apiService  apiService }}fromfrom'../../../services/apiService' '../../../services/apiService';;
exportexportconstconstAnalyticsDashboard AnalyticsDashboard==(())=>=>{{
constconst[[analyticsanalytics,, setAnalytics  setAnalytics]]==useStateuseState((nullnull));;
constconst[[selectedYear selectedYear,, setSelectedYear  setSelectedYear]]==useStateuseState((newnewDateDate(())..getFullYear getFullYear(())));;
constconst[[isLoadingisLoading,, setIsLoading  setIsLoading]]==useStateuseState((truetrue));;
useEffectuseEffect(((())=>=>{{
fetchAnalytics fetchAnalytics(());;
}},,[[selectedYear selectedYear]]));;
constconstfetchAnalytics fetchAnalytics==asyncasync(())=>=>{{
trytry{{
setIsLoading setIsLoading((truetrue));;
constconst[[topSellerstopSellers,, monthlyData  monthlyData]]==awaitawaitPromisePromise..allall(([[
apiService         apiService..getTopSellers getTopSellers((selectedYear selectedYear)),,
apiService         apiService..getMonthlyAnalytics getMonthlyAnalytics((selectedYear selectedYear))
]]));;
setAnalytics setAnalytics(({{
topSellers         topSellers,,
monthlyData monthlyData:: monthlyData  monthlyData..mapmap((itemitem=>=>(({{
monthmonth:: item item..monthmonth,,
salessales:: item item..total_salestotal_sales,,
ordersorders:: item item..total_orders total_orders,,
revenuerevenue:: item item..total_revenue total_revenue
}}))))
}}));;
}}catchcatch((errorerror)){{
consoleconsole..errorerror(('Failed to fetch analytics:' 'Failed to fetch analytics:',, error error));;
}}finallyfinally{{
setIsLoading setIsLoading((falsefalse));;
}}
}};;
ifif((isLoadingisLoading)){{
returnreturn<<div className div className=="animate-pulse""animate-pulse">>LoadingLoading analytics analytics......<<//divdiv>>;;
}}
returnreturn((
<<div className div className=="space-y-6""space-y-6">>
<<div className div className=="flex justify-between items-center" "flex justify-between items-center">>
<<h1 className h1 className=="text-3xl font-bold""text-3xl font-bold">>ShopShopAnalyticsAnalytics<<//h1h1>>
<<selectselect
value           value=={{selectedYear selectedYear}}
onChange           onChange=={{((ee))=>=>setSelectedYear setSelectedYear((parseIntparseInt((ee..targettarget..valuevalue))))}}
className           className=="border rounded-lg px-4 py-2" "border rounded-lg px-4 py-2"
>>
{{[[20242024,,20232023,,20222022]]..mapmap((yearyear=>=>((
<<option keyoption key=={{yearyear}} value value=={{yearyear}}>>{{yearyear}}<<//optionoption>>
))))}}
<<//selectselect>>
<<//divdiv>>
{{/* Revenue Chart */ /* Revenue Chart */}}
<<div className div className=="bg-white rounded-lg shadow-md p-6" "bg-white rounded-lg shadow-md p-6">>
<<h2 className h2 className=="text-xl font-semibold mb-4" "text-xl font-semibold mb-4">>MonthlyMonthlyRevenueRevenue<<//h2h2>>
<<ResponsiveContainer ResponsiveContainer width width=="100%""100%" height height=={{300300}}>>
<<LineChartLineChart data data=={{analyticsanalytics?.?.monthlyData monthlyData}}>>
<<CartesianGrid CartesianGrid strokeDasharray  strokeDasharray=="3 3""3 3"//>>
<<XAxisXAxis dataKey dataKey=="month""month"//>>
<<YAxisYAxis//>>
<<TooltipTooltip//>>
<<LineLine type type=="monotone""monotone" dataKey dataKey=="revenue""revenue" stroke stroke=="#3B82F6""#3B82F6" strokeWidth  strokeWidth=={{22}}//>>
<<//LineChartLineChart>>
<<//ResponsiveContainer ResponsiveContainer>>
<<//divdiv>>
{{/* Top Sellers Grid */ /* Top Sellers Grid */}}
<<div className div className=="bg-white rounded-lg shadow-md p-6" "bg-white rounded-lg shadow-md p-6">>
<<h2 className h2 className=="text-xl font-semibold mb-4" "text-xl font-semibold mb-4">>TopTopSellingSellingItemsItems<<//h2h2>>
<<div className div className=="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">>
{{analyticsanalytics?.?.topSellerstopSellers?.?.mapmap((((itemitem,, index index))=>=>((
<<div keydiv key=={{itemitem..listing_idlisting_id}} className  className=="border rounded-lg p-4" "border rounded-lg p-4">>
<<img img
src                 src=={{itemitem..image_urlimage_url}}
alt                 alt=={{itemitem..titletitle}}
className                 className=="w-full h-32 object-cover rounded mb-2" "w-full h-32 object-cover rounded mb-2"
//>>
<<h3 className h3 className=="font-medium truncate" "font-medium truncate">>{{itemitem..titletitle}}<<//h3h3>>
<<p className p className=="text-gray-600""text-gray-600">>$${{itemitem..priceprice}}<<//pp>>
<<p className p className=="text-sm text-green-600" "text-sm text-green-600">>{{itemitem..total_salestotal_sales}} sales sales<<//pp>>
<<//divdiv>>
))))}}
## 5.3 Mask Creator Tool<<//divdiv>>
<<//divdiv>>
<<//divdiv>>
));;
}};;
```
```javascript
// components/features/MaskCreator/MaskCreator.jsx // components/features/MaskCreator/MaskCreator.jsx
importimport{{ useState useState,, useRef useRef,, useCallback  useCallback }}fromfrom'react''react';;
importimport{{ apiService  apiService }}fromfrom'../../../services/apiService' '../../../services/apiService';;
exportexportconstconstMaskCreator MaskCreator==(())=>=>{{
constconst canvasRef  canvasRef ==useRefuseRef((nullnull));;
constconst[[imageimage,, setImage setImage]]==useStateuseState((nullnull));;
constconst[[masksmasks,, setMasks setMasks]]==useStateuseState(([[]]));;
constconst[[isDrawingisDrawing,, setIsDrawing  setIsDrawing]]==useStateuseState((falsefalse));;
constconst[[drawMode drawMode,, setDrawMode  setDrawMode]]==useStateuseState(('point''point'));;// 'point' or 'rectangle' // 'point' or 'rectangle'
constconsthandleImageUpload handleImageUpload==((eventevent))=>=>{{
constconst file  file == event event..targettarget..filesfiles[[00]];;
ifif((filefile)){{
constconst reader  reader ==newnewFileReaderFileReader(());;
reader      reader..onloadonload==((ee))=>=>{{
constconst img  img ==newnewImageImage(());;
img        img..onloadonload==(())=>=>{{
constconst canvas  canvas == canvasRef  canvasRef..currentcurrent;;
constconst ctx  ctx == canvas canvas..getContext getContext(('2d''2d'));;
canvas           canvas..widthwidth== img img..widthwidth;;
canvas           canvas..heightheight== img img..heightheight;;
ctx          ctx..drawImage drawImage((imgimg,,00,,00));;
setImagesetImage((imgimg));;
}};;
img        img..srcsrc== e e..targettarget..resultresult;;
}};;
reader      reader..readAsDataURL readAsDataURL((filefile));;
}}
}};;
constconst handleCanvasClick  handleCanvasClick ==useCallback useCallback((((eventevent))=>=>{{
ifif((!!imageimage))returnreturn;;
constconst canvas  canvas == canvasRef  canvasRef..currentcurrent;;
constconst rect  rect == canvas canvas..getBoundingClientRect getBoundingClientRect(());;
constconst x  x == event event..clientXclientX-- rect rect..leftleft;;
constconst y  y == event event..clientYclientY-- rect rect..toptop;;
ifif((drawMode drawMode ======'point''point')){{
constconst newMask  newMask =={{typetype::'point''point',, x x,, y y,,idid::DateDate..nownow(())}};;
setMaskssetMasks((prevprev=>=>[[......prevprev,, newMask newMask]]));;
// Draw point on canvas // Draw point on canvas
constconst ctx  ctx == canvas canvas..getContext getContext(('2d''2d'));;
ctx      ctx..fillStylefillStyle=='rgba(255, 0, 0, 0.7)''rgba(255, 0, 0, 0.7)';;
ctx      ctx..beginPathbeginPath(());;
ctx      ctx..arcarc((xx,, y y,,55,,00,,22**MathMath..PIPI));;
ctx      ctx..fillfill(());;
}}
}},,[[imageimage,, drawMode  drawMode]]));;
constconstsaveMaskssaveMasks==asyncasync(())=>=>{{
ifif((masksmasks..lengthlength======00))returnreturn;;
trytry{{
constconst canvas  canvas == canvasRef  canvasRef..currentcurrent;;
constconst imageData  imageData == canvas canvas..toDataURLtoDataURL(());;
awaitawait apiService  apiService..saveMaskData saveMaskData(({{
image_data image_data:: imageData  imageData,,
masksmasks:: masks masks,,
timestamptimestamp::newnewDateDate(())..toISOString toISOString(())
}}));;
alertalert(('Masks saved successfully!' 'Masks saved successfully!'));;
}}catchcatch((errorerror)){{
consoleconsole..errorerror(('Failed to save masks:' 'Failed to save masks:',, error error));;
alertalert(('Failed to save masks' 'Failed to save masks'));;
}}
}};;
returnreturn((
<<div className div className=="bg-white rounded-lg shadow-md p-6" "bg-white rounded-lg shadow-md p-6">>
<<h2 className h2 className=="text-2xl font-bold mb-4" "text-2xl font-bold mb-4">>MaskMaskCreatorCreator<<//h2h2>>
<<div className div className=="mb-4""mb-4">>
<<inputinput
type          type=="file""file"
accept           accept=="image/*""image/*"
onChange           onChange=={{handleImageUpload handleImageUpload}}
className           className=="mb-4""mb-4"
//>>
<<div className div className=="flex gap-4 mb-4""flex gap-4 mb-4">>
<<buttonbutton
onClick             onClick=={{(())=>=>setDrawMode setDrawMode(('point''point'))}}
className             className=={{``px-4 py-2 rounded px-4 py-2 rounded ${${
drawMode               drawMode ======'point''point'
??'bg-primary text-white' 'bg-primary text-white'
::'bg-gray-200 text-gray-700' 'bg-gray-200 text-gray-700'
}}``}}
>>
PointPointModeMode
<<//buttonbutton>>
<<buttonbutton
onClick             onClick=={{(())=>=>setDrawMode setDrawMode(('rectangle''rectangle'))}}
className             className=={{``px-4 py-2 rounded px-4 py-2 rounded ${${
drawMode               drawMode ======'rectangle''rectangle'
??'bg-primary text-white' 'bg-primary text-white'
::'bg-gray-200 text-gray-700' 'bg-gray-200 text-gray-700'
}}``}}
>>
RectangleRectangleModeMode
<<//buttonbutton>>
<<//divdiv>>
<<//divdiv>>
<<div className div className=="border-2 border-dashed border-gray-300 rounded-lg p-4" "border-2 border-dashed border-gray-300 rounded-lg p-4">>
<<canvascanvas
ref          ref=={{canvasRef canvasRef}}
onClick           onClick=={{handleCanvasClick handleCanvasClick}}
className           className=="max-w-full h-auto cursor-crosshair" "max-w-full h-auto cursor-crosshair"
style          style=={{{{maxHeight maxHeight::'500px''500px'}}}}
//>>
<<//divdiv>>
<<div className div className=="mt-4 flex gap-4""mt-4 flex gap-4">>
<<buttonbutton
onClick           onClick=={{(())=>=>setMaskssetMasks(([[]]))}}
className           className=="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600" "px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
>>
ClearClearMasksMasks
<<//buttonbutton>>
<<buttonbutton
onClick           onClick=={{saveMaskssaveMasks}}
disabled           disabled=={{masksmasks..lengthlength======00}}
className           className=="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50" "px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
>>
SaveSaveMasksMasks(({{masksmasks..lengthlength}}))
<<//buttonbutton>>
6. State Management
## 6.1 Zustand Store Configuration<<//divdiv>>
<<//divdiv>>
));;
}};;
```
```javascript
// stores/appStore.js // stores/appStore.js
importimport{{ create  create }}fromfrom'zustand''zustand';;
importimport{{ persist  persist }}fromfrom'zustand/middleware''zustand/middleware';;
exportexportconstconst useAppStore  useAppStore ==createcreate((
persistpersist((
((setset,,getget))=>=>(({{
// User state // User state
useruser::nullnull,,
isAuthenticated isAuthenticated::falsefalse,,
// Shop data // Shop data
shopDatashopData::nullnull,,
listingslistings::[[]],,
// UI state// UI state
sidebarOpen sidebarOpen::truetrue,,
currentPage currentPage::'dashboard''dashboard',,
// Actions// Actions
setUsersetUser::((useruser))=>=>setset(({{ user user,,isAuthenticated isAuthenticated::!!!!user user }})),,
setShopData setShopData::((shopDatashopData))=>=>setset(({{ shopData  shopData }})),,
setListingssetListings::((listingslistings))=>=>setset(({{ listings  listings }})),,
toggleSidebar toggleSidebar::(())=>=>setset((((statestate))=>=>(({{sidebarOpen sidebarOpen::!!statestate..sidebarOpen sidebarOpen}})))),,
setCurrentPage setCurrentPage::((pagepage))=>=>setset(({{currentPage currentPage:: page  page }})),,
// Reset state on logout // Reset state on logout
logoutlogout::(())=>=>setset(({{
useruser::nullnull,,
isAuthenticated isAuthenticated::falsefalse,,
shopDatashopData::nullnull,,
listingslistings::[[]],,
}})),,
}})),,
{{
namename::'etsy-automater-storage' 'etsy-automater-storage',,
partializepartialize::((statestate))=>=>(({{
useruser:: state state..useruser,,
isAuthenticated isAuthenticated:: state state..isAuthenticated isAuthenticated,,
sidebarOpen sidebarOpen:: state state..sidebarOpen sidebarOpen,,
}})),,
}}
7. Docker Integration & Multi-Tenant Deployment
## 7.1 Dockerfile for Production
## 7.2 Nginx Configuration for Multi-Tenant Routing))
));;
```
```dockerfile
# Dockerfile.frontend # Dockerfile.frontend
FROMFROM node:18-alpine  node:18-alpine asas build build
WORKDIRWORKDIR /app /app
# Copy package files # Copy package files
COPYCOPY package*.json ./  package*.json ./
RUNRUN npm ci --only=production  npm ci --only=production
# Copy source code # Copy source code
COPYCOPY . . . .
# Build for production # Build for production
ARGARG REACT_APP_API_BASE_URL  REACT_APP_API_BASE_URL
ARGARG REACT_APP_TENANT_MODE=multi  REACT_APP_TENANT_MODE=multi
ENVENV REACT_APP_API_BASE_URL=  REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL $REACT_APP_API_BASE_URL
ENVENV REACT_APP_TENANT_MODE=  REACT_APP_TENANT_MODE=$REACT_APP_TENANT_MODE $REACT_APP_TENANT_MODE
RUNRUN npm run build  npm run build
# Production stage # Production stage
FROMFROM nginx:alpine  nginx:alpine
# Copy custom nginx config for multi-tenant routing # Copy custom nginx config for multi-tenant routing
COPYCOPY nginx.conf /etc/nginx/conf.d/default.conf  nginx.conf /etc/nginx/conf.d/default.conf
COPYCOPY--from--from==buildbuild /app/dist /usr/share/nginx/html  /app/dist /usr/share/nginx/html
EXPOSEEXPOSE 80 80
CMDCMD [ ["nginx""nginx", , "-g""-g", , "daemon off;""daemon off;"]]
nginx
## 7.3 Docker Compose Integration# nginx.conf # nginx.conf
serverserver{{
listenlisten8080;;
server_name server_name ~^(?<tenant>.+)\.localhost$ localhost  ~^(?<tenant>.+)\.localhost$ localhost;;
rootroot /usr/share/nginx/html  /usr/share/nginx/html;;
indexindex index.html index.htm  index.html index.htm;;
# Add tenant header # Add tenant header
add_header add_header X-Tenant-ID  X-Tenant-ID $tenant$tenant always always;;
# Handle React Router # Handle React Router
locationlocation / /{{
try_filestry_files$uri$uri$uri$uri/ /index.html/ /index.html;;
# Pass tenant info to frontend # Pass tenant info to frontend
add_header add_header X-Tenant-ID  X-Tenant-ID $tenant$tenant always always;;
}}
# API proxy to backend # API proxy to backend
locationlocation /api/ /api/{{
proxy_pass proxy_pass http://backend:3003  http://backend:3003;;
proxy_set_header proxy_set_header Host  Host $host$host;;
proxy_set_header proxy_set_header X-Real-IP  X-Real-IP $remote_addr$remote_addr;;
proxy_set_header proxy_set_header X-Forwarded-For  X-Forwarded-For $proxy_add_x_forwarded_for $proxy_add_x_forwarded_for;;
proxy_set_header proxy_set_header X-Tenant-ID  X-Tenant-ID $tenant$tenant;;
}}
# OAuth callback handling # OAuth callback handling
locationlocation /oauth/ /oauth/{{
proxy_pass proxy_pass http://backend:3003  http://backend:3003;;
proxy_set_header proxy_set_header Host  Host $host$host;;
proxy_set_header proxy_set_header X-Real-IP  X-Real-IP $remote_addr$remote_addr;;
proxy_set_header proxy_set_header X-Forwarded-For  X-Forwarded-For $proxy_add_x_forwarded_for $proxy_add_x_forwarded_for;;
proxy_set_header proxy_set_header X-Tenant-ID  X-Tenant-ID $tenant$tenant;;
}}
}}
```
```yaml
8. Performance Optimization
## 8.1 Code Splitting & Lazy Loading# docker-compose.yml (frontend section) # docker-compose.yml (frontend section)
versionversion::'3.9''3.9'
servicesservices::
frontendfrontend::
buildbuild::
contextcontext:: ./frontend ./frontend
dockerfiledockerfile:: Dockerfile.frontend  Dockerfile.frontend
argsargs::
REACT_APP_API_BASE_URL REACT_APP_API_BASE_URL:: http http:://localhost//localhost::30033003
REACT_APP_TENANT_MODE REACT_APP_TENANT_MODE:: multi multi
portsports::
--"3000:80""3000:80"
depends_on depends_on::
-- backend backend
environment environment::
-- NGINX_HOST=localhost  NGINX_HOST=localhost
-- NGINX_PORT=80  NGINX_PORT=80
volumesvolumes::
-- ./tenant ./tenant--assetsassets::/usr/share/nginx/html/tenant /usr/share/nginx/html/tenant--assetsassets::roro
networksnetworks::
-- app app--networknetwork
labelslabels::
--"traefik.enable=true""traefik.enable=true"
--"traefik.http.routers.frontend.rule=HostRegexp(`{subdomain:[a-zA-Z0-9-]+}.localhost`)" "traefik.http.routers.frontend.rule=HostRegexp(`{subdomain:[a-zA-Z0-9-]+}.localhost`)"
--"traefik.http.services.frontend.loadbalancer.server.port=80" "traefik.http.services.frontend.loadbalancer.server.port=80"
networksnetworks::
app-network app-network::
driverdriver:: bridge bridge
```
```javascript
## 8.2 Caching Strategy// App.js// App.js
importimport{{ lazy lazy,,SuspenseSuspense}}fromfrom'react''react';;
importimport{{BrowserRouter BrowserRouterasasRouterRouter,,RoutesRoutes,,RouteRoute}}fromfrom'react-router-dom''react-router-dom';;
// Lazy load components // Lazy load components
constconstDashboardDashboard==lazylazy(((())=>=>importimport(('./pages/Dashboard''./pages/Dashboard'))));;
constconstAnalyticsAnalytics==lazylazy(((())=>=>importimport(('./pages/Analytics''./pages/Analytics'))));;
constconstDesignsDesigns==lazylazy(((())=>=>importimport(('./pages/Designs''./pages/Designs'))));;
constconstMaskCreator MaskCreator==lazylazy(((())=>=>importimport(('./pages/MaskCreator' './pages/MaskCreator'))));;
exportexportdefaultdefaultfunctionfunctionAppApp(()){{
returnreturn((
<<TenantProvider TenantProvider>>
<<ThemeProvider ThemeProvider>>
<<RouterRouter>>
<<AppLayout AppLayout>>
<<SuspenseSuspense fallback fallback=={{<<LoadingSpinner LoadingSpinner//>>}}>>
<<RoutesRoutes>>
<<RouteRoute path path=="/""/" element element=={{<<DashboardDashboard//>>}}//>>
<<RouteRoute path path=="/analytics""/analytics" element element=={{<<AnalyticsAnalytics//>>}}//>>
<<RouteRoute path path=="/designs""/designs" element element=={{<<DesignsDesigns//>>}}//>>
<<RouteRoute path path=="/tools/mask-creator""/tools/mask-creator" element element=={{<<MaskCreator MaskCreator//>>}}//>>
<<//RoutesRoutes>>
<<//SuspenseSuspense>>
<<//AppLayout AppLayout>>
<<//RouterRouter>>
<<//ThemeProvider ThemeProvider>>
<<//TenantProvider TenantProvider>>
));;
}}
```
```javascript
9. Testing Strategy
## 9.1 Component Testing// hooks/useApiQuery.js // hooks/useApiQuery.js
importimport{{ useQuery  useQuery }}fromfrom'@tanstack/react-query' '@tanstack/react-query';;
importimport{{ apiService  apiService }}fromfrom'../services/apiService' '../services/apiService';;
exportexportconstconstuseShopAnalytics useShopAnalytics==((params params =={{}}))=>=>{{
returnreturnuseQueryuseQuery(({{
queryKeyqueryKey::[['shopAnalytics''shopAnalytics',, params params]],,
queryFnqueryFn::(())=>=> apiService  apiService..getShopAnalytics getShopAnalytics((paramsparams)),,
staleTimestaleTime::55**6060**10001000,,// 5 minutes // 5 minutes
cacheTimecacheTime::1010**6060**10001000,,// 10 minutes // 10 minutes
refetchOnWindowFocus refetchOnWindowFocus::falsefalse,,
}}));;
}};;
exportexportconstconstuseTopSellers useTopSellers==((yearyear))=>=>{{
returnreturnuseQueryuseQuery(({{
queryKeyqueryKey::[['topSellers''topSellers',, year year]],,
queryFnqueryFn::(())=>=> apiService  apiService..getTopSellers getTopSellers((yearyear)),,
staleTimestaleTime::6060**6060**10001000,,// 1 hour// 1 hour
enabledenabled::!!!!yearyear,,
}}));;
}};;
```
```javascript
10. Security Considerations// __tests__/components/Analytics/AnalyticsDashboard.test.jsx // __tests__/components/Analytics/AnalyticsDashboard.test.jsx
importimport{{ render render,, screen screen,, waitFor  waitFor }}fromfrom'@testing-library/react' '@testing-library/react';;
importimport{{QueryClient QueryClient,,QueryClientProvider QueryClientProvider}}fromfrom'@tanstack/react-query' '@tanstack/react-query';;
importimport{{AnalyticsDashboard AnalyticsDashboard}}fromfrom'../../../src/components/features/Analytics/AnalyticsDashboard' '../../../src/components/features/Analytics/AnalyticsDashboard';;
importimport{{TenantProvider TenantProvider}}fromfrom'../../../src/contexts/TenantContext' '../../../src/contexts/TenantContext';;
constconst queryClient  queryClient ==newnewQueryClientQueryClient(({{
defaultOptions defaultOptions::{{queriesqueries::{{retryretry::falsefalse}}}}
}}));;
constconstrenderWithProviders renderWithProviders==((component component))=>=>{{
returnreturnrenderrender((
<<QueryClientProvider QueryClientProvider client client=={{queryClient queryClient}}>>
<<TenantProvider TenantProvider>>
{{component component}}
<<//TenantProvider TenantProvider>>
<<//QueryClientProvider QueryClientProvider>>
));;
}};;
describedescribe(('AnalyticsDashboard''AnalyticsDashboard',,(())=>=>{{
testtest(('renders analytics dashboard with loading state' 'renders analytics dashboard with loading state',,(())=>=>{{
renderWithProviders renderWithProviders((<<AnalyticsDashboard AnalyticsDashboard//>>));;
expectexpect((screenscreen..getByTextgetByText(('Loading analytics...''Loading analytics...'))))..toBeInTheDocument toBeInTheDocument(());;
}}));;
testtest(('displays analytics data after loading' 'displays analytics data after loading',,asyncasync(())=>=>{{
// Mock API response // Mock API response
jest    jest..spyOnspyOn((requirerequire(('../../../src/services/apiService' '../../../src/services/apiService')),,'getTopSellers''getTopSellers'))
..mockResolvedValue mockResolvedValue(([[
{{listing_idlisting_id::'1''1',,titletitle::'Test Product''Test Product',,priceprice::'29.99''29.99',,total_salestotal_sales::1010}}
]]));;
renderWithProviders renderWithProviders((<<AnalyticsDashboard AnalyticsDashboard//>>));;
awaitawaitwaitForwaitFor(((())=>=>{{
expectexpect((screenscreen..getByTextgetByText(('Test Product''Test Product'))))..toBeInTheDocument toBeInTheDocument(());;
}}));;
}}));;
}}));;
## 10.1 Tenant Data Isolation
```
```javascript
// utils/tenantSecurity.js // utils/tenantSecurity.js
exportexportconstconstvalidateTenantAccess validateTenantAccess==((requestedTenant requestedTenant,, userTenant  userTenant))=>=>{{
ifif((!!userTenant userTenant ||||!!requestedTenant requestedTenant)){{
throwthrownewnewErrorError(('Tenant information missing' 'Tenant information missing'));;
}}
ifif((userTenant userTenant !==!== requestedTenant  requestedTenant)){{
throwthrownewnewErrorError(('Access denied: Tenant mismatch' 'Access denied: Tenant mismatch'));;
}}
returnreturntruetrue;;
}};;
// Enhanced API service with security // Enhanced API service with security
exportexportclassclassSecureApiService SecureApiServiceextendsextendsApiServiceApiService{{
asyncasyncmakeRequest makeRequest((endpointendpoint,, options  options =={{}})){{
constconst tenant  tenant ==thisthis..getCurrentTenant getCurrentTenant(());;
// Validate tenant access before making request // Validate tenant access before making request
ifif((!!tenanttenant?.?.idid)){{
throwthrownewnewErrorError(('No tenant context available' 'No tenant context available'));;
}}
returnreturnsupersuper..makeRequest makeRequest((endpointendpoint,,{{
......optionsoptions,,
headersheaders::{{
......optionsoptions..headersheaders,,
'X-Tenant-ID''X-Tenant-ID':: tenant tenant..idid,,
'X-Tenant-Signature''X-Tenant-Signature'::thisthis..generateTenantSignature generateTenantSignature((tenanttenant..idid)),,
}}
}}));;
}}
generateTenantSignature generateTenantSignature((tenantIdtenantId)){{
// Generate HMAC signature for tenant validation // Generate HMAC signature for tenant validation
constconst timestamp  timestamp ==DateDate..nownow(());;
constconst payload  payload ==``${${tenantIdtenantId}}::${${timestamptimestamp}}``;;
// In production, use proper HMAC with secret key // In production, use proper HMAC with secret key
returnreturnbtoabtoa((payloadpayload));;
}}
}}
11. Deployment & Monitoring
## 11.1 QNAP NAS Deployment Configuration
## 11.2 Environment Configurationbash
# deploy-frontend.sh # deploy-frontend.sh
#!/bin/bash #!/bin/bash
# QNAP Container Station deployment script # QNAP Container Station deployment script
echoecho"Deploying Etsy Seller Automater Frontend to QNAP NAS..." "Deploying Etsy Seller Automater Frontend to QNAP NAS..."
# Build production image # Build production image
dockerdocker build -t etsy-frontend:latest  build -t etsy-frontend:latest \\
--build-arg   --build-arg REACT_APP_API_BASE_URL REACT_APP_API_BASE_URL==http://your-qnap-ip:3003 http://your-qnap-ip:3003 \\
--build-arg   --build-arg REACT_APP_TENANT_MODE REACT_APP_TENANT_MODE==multi multi \\
-f Dockerfile.frontend   -f Dockerfile.frontend ..
# Create tenant-specific volumes # Create tenant-specific volumes
dockerdocker volume create etsy_tenant_assets  volume create etsy_tenant_assets
dockerdocker volume create etsy_nginx_config  volume create etsy_nginx_config
# Deploy with Container Station # Deploy with Container Station
dockerdocker run -d  run -d \\
--name etsy-frontend-prod   --name etsy-frontend-prod \\
--restart unless-stopped   --restart unless-stopped \\
-p   -p 8080:80 :80 \\
-p   -p 443443:443 :443 \\
-v etsy_tenant_assets:/usr/share/nginx/html/tenant-assets   -v etsy_tenant_assets:/usr/share/nginx/html/tenant-assets \\
-v etsy_nginx_config:/etc/nginx/conf.d   -v etsy_nginx_config:/etc/nginx/conf.d \\
--network etsy-network   --network etsy-network \\
etsy-frontend:latest   etsy-frontend:latest
echoecho"Frontend deployed successfully!" "Frontend deployed successfully!"
echoecho"Access at: http://tenant1.your-qnap-ip or http://your-qnap-ip" "Access at: http://tenant1.your-qnap-ip or http://your-qnap-ip"
```
```javascript
## 11.3 Health Monitoring & Diagnostics// config/environment.js // config/environment.js
constconst environments  environments =={{
development development::{{
API_BASE_URL API_BASE_URL::'http://localhost:3003' 'http://localhost:3003',,
TENANT_MODE TENANT_MODE::'single''single',,
DEBUGDEBUG::truetrue,,
CACHE_TTLCACHE_TTL::6000060000,,// 1 minute// 1 minute
}},,
productionproduction::{{
API_BASE_URL API_BASE_URL:: process process..envenv..REACT_APP_API_BASE_URL REACT_APP_API_BASE_URL||||'http://your-qnap-ip:3003' 'http://your-qnap-ip:3003',,
TENANT_MODE TENANT_MODE::'multi''multi',,
DEBUGDEBUG::falsefalse,,
CACHE_TTLCACHE_TTL::300000300000,,// 5 minutes // 5 minutes
}},,
qnapqnap::{{
API_BASE_URL API_BASE_URL::'http://192.168.1.100:3003' 'http://192.168.1.100:3003',,// Your QNAP IP // Your QNAP IP
TENANT_MODE TENANT_MODE::'multi''multi',,
DEBUGDEBUG::falsefalse,,
CACHE_TTLCACHE_TTL::600000600000,,// 10 minutes // 10 minutes
ENABLE_ANALYTICS ENABLE_ANALYTICS::truetrue,,
}}
}};;
exportexportconstconst config  config == environments  environments[[processprocess..envenv..NODE_ENVNODE_ENV]]|||| environments  environments..development development;;
```
```javascript
// utils/healthMonitor.js // utils/healthMonitor.js
classclassHealthMonitor HealthMonitor{{
constructor constructor(()){{
thisthis..checkschecks==newnewMapMap(());;
thisthis..startMonitoring startMonitoring(());;
}}
asyncasynccheckApiHealth checkApiHealth(()){{
trytry{{
constconst response  response ==awaitawaitfetchfetch((``${${configconfig..API_BASE_URL API_BASE_URL}}/health/health``,,{{
methodmethod::'GET''GET',,
timeouttimeout::50005000,,
}}));;
returnreturn response response..okok;;
}}catchcatch((errorerror)){{
consoleconsole..errorerror(('API health check failed:' 'API health check failed:',, error error));;
returnreturnfalsefalse;;
}}
}}
asyncasynccheckTenantConfig checkTenantConfig(()){{
constconst tenant  tenant ==thisthis..getCurrentTenant getCurrentTenant(());;
returnreturn!!!!((tenanttenant?.?.id id &&&& tenant tenant?.?.configconfig));;
}}
asyncasyncperformHealthChecks performHealthChecks(()){{
constconst results  results =={{
apiapi::awaitawaitthisthis..checkApiHealth checkApiHealth(()),,
tenanttenant::awaitawaitthisthis..checkTenantConfig checkTenantConfig(()),,
storagestorage::thisthis..checkLocalStorage checkLocalStorage(()),,
timestamptimestamp::newnewDateDate(())..toISOString toISOString(()),,
}};;
thisthis..checkschecks..setset(('latest''latest',, results results));;
returnreturn results results;;
}}
checkLocalStorage checkLocalStorage(()){{
trytry{{
constconst testKey  testKey =='__storage_test__''__storage_test__';;
localStorage localStorage..setItemsetItem((testKeytestKey,,'test''test'));;
localStorage localStorage..removeItemremoveItem((testKeytestKey));;
returnreturntruetrue;;
}}catchcatch((errorerror)){{
returnreturnfalsefalse;;
}}
}}
startMonitoring startMonitoring(()){{
// Perform health checks every 2 minutes // Perform health checks every 2 minutes
setIntervalsetInterval(((())=>=>{{
thisthis..performHealthChecks performHealthChecks(());;
}},,120000120000));;
}}
getHealthStatus getHealthStatus(()){{
returnreturnthisthis..checkschecks..getget(('latest''latest'))||||nullnull;;
}}
}}
exportexportconstconst healthMonitor  healthMonitor ==newnewHealthMonitor HealthMonitor(());;
// Health Status Component // Health Status Component
exportexportconstconstHealthStatus HealthStatus==(())=>=>{{
constconst[[healthhealth,, setHealth setHealth]]==useStateuseState((nullnull));;
useEffectuseEffect(((())=>=>{{
constconstupdateHealth updateHealth==(())=>=>{{
setHealthsetHealth((healthMonitor healthMonitor..getHealthStatus getHealthStatus(())));;
}};;
updateHealth updateHealth(());;
constconst interval  interval ==setIntervalsetInterval((updateHealth updateHealth,,3000030000));;// Update every 30s // Update every 30s
returnreturn(())=>=>clearInterval clearInterval((intervalinterval));;
}},,[[]]));;
ifif((!!healthhealth))returnreturnnullnull;;
constconst allHealthy  allHealthy ==ObjectObject..valuesvalues((healthhealth))..everyevery((statusstatus=>=>
typeoftypeof status  status ======'boolean''boolean'?? status  status ::truetrue
));;
returnreturn((
<<div className div className=={{``fixed bottom-4 right-4 p-2 rounded-lg text-sm fixed bottom-4 right-4 p-2 rounded-lg text-sm ${${
allHealthy       allHealthy ??'bg-green-100 text-green-800' 'bg-green-100 text-green-800'::'bg-red-100 text-red-800' 'bg-red-100 text-red-800'
}}``}}>>
12. Advanced Features
## 12.1 Real-time Updates with WebSocket<<div className div className=="flex items-center gap-2" "flex items-center gap-2">>
<<div className div className=={{``w-2 h-2 rounded-full w-2 h-2 rounded-full ${${
allHealthy           allHealthy ??'bg-green-500''bg-green-500'::'bg-red-500''bg-red-500'
}}``}}//>>
SystemSystemStatusStatus::{{allHealthy allHealthy ??'Healthy''Healthy'::'Issues Detected''Issues Detected'}}
<<//divdiv>>
<<//divdiv>>
));;
}};;
```
```javascript
// services/websocketService.js // services/websocketService.js
classclassWebSocketService WebSocketService{{
constructor constructor(()){{
thisthis..wsws==nullnull;;
thisthis..reconnectAttempts reconnectAttempts==00;;
thisthis..maxReconnectAttempts maxReconnectAttempts==55;;
thisthis..listenerslisteners==newnewMapMap(());;
}}
connectconnect((tenantIdtenantId)){{
constconst wsUrl  wsUrl ==``ws://ws://${${windowwindow..locationlocation..hosthost}}/ws?tenant=/ws?tenant=${${tenantIdtenantId}}``;;
thisthis..wsws==newnewWebSocketWebSocket((wsUrlwsUrl));;
thisthis..wsws..onopenonopen==(())=>=>{{
consoleconsole..loglog(('WebSocket connected' 'WebSocket connected'));;
thisthis..reconnectAttempts reconnectAttempts==00;;
}};;
thisthis..wsws..onmessage onmessage==((eventevent))=>=>{{
constconst data  data ==JSONJSON..parseparse((eventevent..datadata));;
thisthis..handleMessage handleMessage((datadata));;
}};;
thisthis..wsws..oncloseonclose==(())=>=>{{
consoleconsole..loglog(('WebSocket disconnected' 'WebSocket disconnected'));;
thisthis..attemptReconnect attemptReconnect((tenantIdtenantId));;
}};;
thisthis..wsws..onerroronerror==((errorerror))=>=>{{
consoleconsole..errorerror(('WebSocket error:''WebSocket error:',, error error));;
}};;
}}
handleMessage handleMessage((datadata)){{
constconst{{ type type,, payload  payload }}== data data;;
constconst listeners  listeners ==thisthis..listenerslisteners..getget((typetype))||||[[]];;
listeners    listeners..forEachforEach((callbackcallback=>=>callbackcallback((payloadpayload))));;
}}
subscribesubscribe((eventTypeeventType,, callback callback)){{
ifif((!!thisthis..listenerslisteners..hashas((eventTypeeventType)))){{
thisthis..listenerslisteners..setset((eventTypeeventType,,[[]]));;
}}
thisthis..listenerslisteners..getget((eventTypeeventType))..pushpush((callbackcallback));;
returnreturn(())=>=>{{
constconst listeners  listeners ==thisthis..listenerslisteners..getget((eventTypeeventType));;
constconst index  index == listeners listeners..indexOfindexOf((callbackcallback));;
ifif((index index >>--11)){{
listeners         listeners..splicesplice((indexindex,,11));;
}}
}};;
}}
attemptReconnect attemptReconnect((tenantIdtenantId)){{
ifif((thisthis..reconnectAttempts reconnectAttempts<<thisthis..maxReconnectAttempts maxReconnectAttempts)){{
thisthis..reconnectAttempts reconnectAttempts++++;;
setTimeout setTimeout(((())=>=>{{
consoleconsole..loglog((``Reconnecting... ( Reconnecting... (${${thisthis..reconnectAttempts reconnectAttempts}}//${${thisthis..maxReconnectAttempts maxReconnectAttempts}}))``));;
thisthis..connectconnect((tenantIdtenantId));;
}},,20002000**thisthis..reconnectAttempts reconnectAttempts));;
}}
}}
}}
exportexportconstconst wsService  wsService ==newnewWebSocketService WebSocketService(());;
// Real-time Analytics Hook // Real-time Analytics Hook
exportexportconstconstuseRealTimeAnalytics useRealTimeAnalytics==(())=>=>{{
constconst[[liveDataliveData,, setLiveData  setLiveData]]==useStateuseState((nullnull));;
constconst{{ tenant  tenant }}==useTenantuseTenant(());;
useEffectuseEffect(((())=>=>{{
ifif((!!tenanttenant?.?.idid))returnreturn;;
wsService     wsService..connectconnect((tenanttenant..idid));;
constconst unsubscribe  unsubscribe == wsService wsService..subscribesubscribe(('analytics_update''analytics_update',,((datadata))=>=>{{
setLiveData setLiveData((datadata));;
}}));;
returnreturn(())=>=>{{
unsubscribe unsubscribe(());;
}};;
}},,[[tenanttenant?.?.idid]]));;
## 12.2 Advanced Caching with Service Workerreturnreturn liveData liveData;;
}};;
```
```javascript
// public/sw.js - Service Worker for advanced caching // public/sw.js - Service Worker for advanced caching
constconstCACHE_NAME CACHE_NAME=='etsy-automater-v1''etsy-automater-v1';;
constconstTENANT_CACHE_PREFIX TENANT_CACHE_PREFIX=='tenant-''tenant-';;
// Cache strategies for different resource types // Cache strategies for different resource types
constconstCACHE_STRATEGIES CACHE_STRATEGIES=={{
tenant_assets tenant_assets::'cache-first''cache-first',,
api_dataapi_data::'network-first''network-first',,
static_assets static_assets::'cache-first''cache-first',,
}};;
selfself..addEventListener addEventListener(('install''install',,((eventevent))=>=>{{
event  event..waitUntilwaitUntil((
caches    caches..openopen((CACHE_NAME CACHE_NAME))..thenthen((((cachecache))=>=>{{
returnreturn cache cache..addAlladdAll(([[
'/''/',,
'/static/css/main.css''/static/css/main.css',,
'/static/js/main.js''/static/js/main.js',,
'/static/media/logo.svg' '/static/media/logo.svg',,
]]));;
}}))
));;
}}));;
selfself..addEventListener addEventListener(('fetch''fetch',,((eventevent))=>=>{{
constconst{{ request  request }}== event event;;
constconst url  url ==newnewURLURL((requestrequest..urlurl));;
// Handle tenant-specific caching // Handle tenant-specific caching
ifif((urlurl..pathnamepathname..startsWithstartsWith(('/tenant-assets/''/tenant-assets/')))){{
event    event..respondWith respondWith((cacheFirstStrategy cacheFirstStrategy((requestrequest))));;
}}
// Handle API requests // Handle API requests
elseelseifif((urlurl..pathnamepathname..startsWithstartsWith(('/api/''/api/')))){{
event    event..respondWith respondWith((networkFirstStrategy networkFirstStrategy((requestrequest))));;
}}
// Handle static assets // Handle static assets
elseelse{{
event    event..respondWith respondWith((cacheFirstStrategy cacheFirstStrategy((requestrequest))));;
}}
}}));;
## 12.3 Progressive Web App FeaturesasyncasyncfunctionfunctioncacheFirstStrategy cacheFirstStrategy((requestrequest)){{
constconst cache  cache ==awaitawait caches caches..openopen((CACHE_NAME CACHE_NAME));;
constconst cachedResponse  cachedResponse ==awaitawait cache cache..matchmatch((requestrequest));;
ifif((cachedResponse cachedResponse)){{
// Update cache in background // Update cache in background
fetchfetch((requestrequest))..thenthen((responseresponse=>=>{{
ifif((responseresponse..okok)){{
cache        cache..putput((requestrequest,, response response..cloneclone(())));;
}}
}}));;
returnreturn cachedResponse  cachedResponse;;
}}
constconst response  response ==awaitawaitfetchfetch((requestrequest));;
ifif((responseresponse..okok)){{
cache    cache..putput((requestrequest,, response response..cloneclone(())));;
}}
returnreturn response response;;
}}
asyncasyncfunctionfunctionnetworkFirstStrategy networkFirstStrategy((requestrequest)){{
trytry{{
constconst response  response ==awaitawaitfetchfetch((requestrequest));;
ifif((responseresponse..okok)){{
constconst cache  cache ==awaitawait caches caches..openopen((CACHE_NAME CACHE_NAME));;
cache      cache..putput((requestrequest,, response response..cloneclone(())));;
}}
returnreturn response response;;
}}catchcatch((errorerror)){{
constconst cache  cache ==awaitawait caches caches..openopen((CACHE_NAME CACHE_NAME));;
constconst cachedResponse  cachedResponse ==awaitawait cache cache..matchmatch((requestrequest));;
returnreturn cachedResponse  cachedResponse ||||newnewResponseResponse(('Offline''Offline',,{{statusstatus::503503}}));;
}}
}}
```
```javascript
// hooks/usePWA.js // hooks/usePWA.js
importimport{{ useState useState,, useEffect  useEffect }}fromfrom'react''react';;
exportexportconstconstusePWAusePWA==(())=>=>{{
constconst[[isInstallable isInstallable,, setIsInstallable  setIsInstallable]]==useStateuseState((falsefalse));;
constconst[[installPrompt installPrompt,, setInstallPrompt  setInstallPrompt]]==useStateuseState((nullnull));;
constconst[[isOnlineisOnline,, setIsOnline  setIsOnline]]==useStateuseState((navigatornavigator..onLineonLine));;
useEffectuseEffect(((())=>=>{{
// PWA install prompt // PWA install prompt
constconsthandleBeforeInstallPrompt handleBeforeInstallPrompt==((ee))=>=>{{
e      e..preventDefault preventDefault(());;
setInstallPrompt setInstallPrompt((ee));;
setIsInstallable setIsInstallable((truetrue));;
}};;
// Online/offline status // Online/offline status
constconsthandleOnline handleOnline==(())=>=>setIsOnlinesetIsOnline((truetrue));;
constconsthandleOffline handleOffline==(())=>=>setIsOnlinesetIsOnline((falsefalse));;
windowwindow..addEventListener addEventListener(('beforeinstallprompt''beforeinstallprompt',, handleBeforeInstallPrompt  handleBeforeInstallPrompt));;
windowwindow..addEventListener addEventListener(('online''online',, handleOnline  handleOnline));;
windowwindow..addEventListener addEventListener(('offline''offline',, handleOffline  handleOffline));;
returnreturn(())=>=>{{
windowwindow..removeEventListener removeEventListener(('beforeinstallprompt''beforeinstallprompt',, handleBeforeInstallPrompt  handleBeforeInstallPrompt));;
windowwindow..removeEventListener removeEventListener(('online''online',, handleOnline  handleOnline));;
windowwindow..removeEventListener removeEventListener(('offline''offline',, handleOffline  handleOffline));;
}};;
}},,[[]]));;
constconstinstallAppinstallApp==asyncasync(())=>=>{{
ifif((installPrompt installPrompt)){{
installPrompt       installPrompt..promptprompt(());;
constconst result  result ==awaitawait installPrompt  installPrompt..userChoice userChoice;;
ifif((resultresult..outcomeoutcome======'accepted''accepted')){{
setIsInstallable setIsInstallable((falsefalse));;
setInstallPrompt setInstallPrompt((nullnull));;
}}
}}
}};;
returnreturn{{
isInstallable     isInstallable,,
installApp     installApp,,
isOnline    isOnline,,
}};;
}};;
// PWA Install Banner Component // PWA Install Banner Component
exportexportconstconstPWAInstallBanner PWAInstallBanner==(())=>=>{{
constconst{{ isInstallable  isInstallable,, installApp  installApp }}==usePWAusePWA(());;
constconst[[dismisseddismissed,, setDismissed  setDismissed]]==useStateuseState((
localStorage localStorage..getItemgetItem(('pwa-banner-dismissed' 'pwa-banner-dismissed'))======'true''true'
));;
ifif((!!isInstallable isInstallable |||| dismissed dismissed))returnreturnnullnull;;
constconsthandleDismiss handleDismiss==(())=>=>{{
setDismissed setDismissed((truetrue));;
localStorage localStorage..setItemsetItem(('pwa-banner-dismissed' 'pwa-banner-dismissed',,'true''true'));;
}};;
returnreturn((
<<div className div className=="fixed top-0 left-0 right-0 bg-blue-600 text-white p-4 z-50" "fixed top-0 left-0 right-0 bg-blue-600 text-white p-4 z-50">>
<<div className div className=="flex items-center justify-between max-w-4xl mx-auto" "flex items-center justify-between max-w-4xl mx-auto">>
<<div className div className=="flex items-center gap-3" "flex items-center gap-3">>
<<spanspan>>📱📱<<//spanspan>>
<<spanspan>>InstallInstallEtsyEtsyAutomaterAutomaterforfor quick access  quick access!!<<//spanspan>>
<<//divdiv>>
<<div className div className=="flex gap-2""flex gap-2">>
<<buttonbutton
onClick             onClick=={{installAppinstallApp}}
className             className=="bg-blue-700 px-4 py-2 rounded hover:bg-blue-800" "bg-blue-700 px-4 py-2 rounded hover:bg-blue-800"
>>
InstallInstall
<<//buttonbutton>>
<<buttonbutton
onClick             onClick=={{handleDismiss handleDismiss}}
className             className=="bg-blue-700 px-4 py-2 rounded hover:bg-blue-800" "bg-blue-700 px-4 py-2 rounded hover:bg-blue-800"
>>
✕            ✕
<<//buttonbutton>>
<<//divdiv>>
<<//divdiv>>
<<//divdiv>>
13. Analytics & Performance Tracking
## 13.1 Custom Analytics Hook));;
}};;
```
```javascript
// hooks/useAnalytics.js // hooks/useAnalytics.js
importimport{{ useEffect  useEffect }}fromfrom'react''react';;
importimport{{ useTenant  useTenant }}fromfrom'../contexts/TenantContext' '../contexts/TenantContext';;
classclassAnalyticsService AnalyticsService{{
constructor constructor(()){{
thisthis..eventsevents==[[]];;
thisthis..sessionIdsessionId==thisthis..generateSessionId generateSessionId(());;
}}
generateSessionId generateSessionId(()){{
returnreturn``session_session_${${DateDate..nownow(())}}__${${MathMath..randomrandom(())..toStringtoString((3636))..substrsubstr((22,,99))}}``;;
}}
tracktrack((eventevent,, properties  properties =={{}})){{
constconst eventData  eventData =={{
event      event,,
propertiesproperties::{{
......propertiesproperties,,
timestamptimestamp::newnewDateDate(())..toISOString toISOString(()),,
sessionIdsessionId::thisthis..sessionIdsessionId,,
urlurl::windowwindow..locationlocation..hrefhref,,
userAgentuserAgent::navigatornavigator..userAgentuserAgent,,
}},,
}};;
thisthis..eventsevents..pushpush((eventDataeventData));;
// Send to analytics endpoint // Send to analytics endpoint
thisthis..sendToAnalytics sendToAnalytics((eventDataeventData));;
}}
asyncasyncsendToAnalytics sendToAnalytics((eventDataeventData)){{
trytry{{
awaitawaitfetchfetch(('/api/analytics''/api/analytics',,{{
methodmethod::'POST''POST',,
headersheaders::{{
'Content-Type''Content-Type'::'application/json''application/json',,
}},,
bodybody::JSONJSON..stringifystringify((eventDataeventData)),,
}}));;
}}catchcatch((errorerror)){{
consoleconsole..errorerror(('Analytics tracking failed:' 'Analytics tracking failed:',, error error));;
}}
}}
trackPageView trackPageView((pagepage,, tenant tenant)){{
thisthis..tracktrack(('page_view''page_view',,{{
page      page,,
tenanttenant:: tenant tenant?.?.idid,,
}}));;
}}
trackUserAction trackUserAction((actionaction,, data  data =={{}})){{
thisthis..tracktrack(('user_action''user_action',,{{
action      action,,
......datadata,,
}}));;
}}
trackPerformance trackPerformance((metricmetric,, value value,, tenant tenant)){{
thisthis..tracktrack(('performance''performance',,{{
metric      metric,,
value      value,,
tenanttenant:: tenant tenant?.?.idid,,
}}));;
}}
}}
constconst analytics  analytics ==newnewAnalyticsService AnalyticsService(());;
exportexportconstconstuseAnalytics useAnalytics==(())=>=>{{
constconst{{ tenant  tenant }}==useTenantuseTenant(());;
constconsttrackEventtrackEvent==((eventevent,, properties  properties =={{}}))=>=>{{
analytics     analytics..tracktrack((eventevent,,{{
......propertiesproperties,,
tenanttenant:: tenant tenant?.?.idid,,
}}));;
}};;
constconsttrackPageView trackPageView==((pagepage))=>=>{{
analytics     analytics..trackPageView trackPageView((pagepage,, tenant tenant));;
}};;
constconsttrackUserAction trackUserAction==((actionaction,, data  data =={{}}))=>=>{{
analytics     analytics..trackUserAction trackUserAction((actionaction,,{{
......datadata,,
tenanttenant:: tenant tenant?.?.idid,,
}}));;
}};;
returnreturn{{
trackEvent     trackEvent,,
trackPageView     trackPageView,,
trackUserAction     trackUserAction,,
}};;
}};;
// Performance monitoring hook // Performance monitoring hook
exportexportconstconstusePerformanceMonitoring usePerformanceMonitoring==(())=>=>{{
constconst{{ tenant  tenant }}==useTenantuseTenant(());;
useEffectuseEffect(((())=>=>{{
// Track Core Web Vitals // Track Core Web Vitals
importimport(('web-vitals''web-vitals'))..thenthen(((({{ getCLS getCLS,, getFID getFID,, getFCP getFCP,, getLCP getLCP,, getTTFB  getTTFB }}))=>=>{{
getCLSgetCLS((((metricmetric))=>=>{{
analytics         analytics..trackPerformance trackPerformance(('CLS''CLS',, metric metric..valuevalue,, tenant tenant));;
}}));;
getFIDgetFID((((metricmetric))=>=>{{
analytics         analytics..trackPerformance trackPerformance(('FID''FID',, metric metric..valuevalue,, tenant tenant));;
}}));;
getFCPgetFCP((((metricmetric))=>=>{{
analytics         analytics..trackPerformance trackPerformance(('FCP''FCP',, metric metric..valuevalue,, tenant tenant));;
}}));;
getLCPgetLCP((((metricmetric))=>=>{{
analytics         analytics..trackPerformance trackPerformance(('LCP''LCP',, metric metric..valuevalue,, tenant tenant));;
}}));;
getTTFBgetTTFB((((metricmetric))=>=>{{
analytics         analytics..trackPerformance trackPerformance(('TTFB''TTFB',, metric metric..valuevalue,, tenant tenant));;
}}));;
}}));;
// Track custom performance metrics // Track custom performance metrics
constconst navigationStart  navigationStart ==performance performance..timingtiming..navigationStart navigationStart;;
constconst domContentLoaded  domContentLoaded ==performance performance..timingtiming..domContentLoadedEventEnd domContentLoadedEventEnd;;
constconst loadTime  loadTime == domContentLoaded  domContentLoaded -- navigationStart  navigationStart;;
14. Error Handling & Logging
## 14.1 Global Error Boundary    analytics     analytics..trackPerformance trackPerformance(('page_load_time''page_load_time',, loadTime loadTime,, tenant tenant));;
}},,[[tenanttenant]]));;
}};;
```
```javascript
// components/common/ErrorBoundary.jsx // components/common/ErrorBoundary.jsx
importimport{{Component Component}}fromfrom'react''react';;
classclassErrorBoundary ErrorBoundaryextendsextendsComponentComponent{{
constructor constructor((propsprops)){{
supersuper((propsprops));;
thisthis..statestate=={{hasErrorhasError::falsefalse,,errorerror::nullnull,,errorInfoerrorInfo::nullnull}};;
}}
staticstaticgetDerivedStateFromError getDerivedStateFromError((errorerror)){{
returnreturn{{hasErrorhasError::truetrue}};;
}}
componentDidCatch componentDidCatch((errorerror,, errorInfo errorInfo)){{
thisthis..setStatesetState(({{
error      error,,
errorInfo       errorInfo,,
}}));;
// Log error to monitoring service // Log error to monitoring service
thisthis..logErrorlogError((errorerror,, errorInfo errorInfo));;
}}
logErrorlogError((errorerror,, errorInfo errorInfo)){{
constconst errorData  errorData =={{
messagemessage:: error error..messagemessage,,
stackstack:: error error..stackstack,,
componentStack componentStack:: errorInfo errorInfo..componentStack componentStack,,
timestamptimestamp::newnewDateDate(())..toISOString toISOString(()),,
urlurl::windowwindow..locationlocation..hrefhref,,
userAgentuserAgent::navigatornavigator..userAgentuserAgent,,
tenanttenant::thisthis..getTenantFromContext getTenantFromContext(()),,
}};;
// Send to error logging service // Send to error logging service
fetchfetch(('/api/errors''/api/errors',,{{
methodmethod::'POST''POST',,
headersheaders::{{
'Content-Type''Content-Type'::'application/json''application/json',,
}},,
bodybody::JSONJSON..stringifystringify((errorDataerrorData)),,
}}))..catchcatch((consoleconsole..errorerror));;
}}
getTenantFromContext getTenantFromContext(()){{
// Extract tenant from URL or context // Extract tenant from URL or context
constconst hostname  hostname ==windowwindow..locationlocation..hostnamehostname;;
returnreturn hostname hostname..splitsplit(('.''.'))[[00]];;
}}
renderrender(()){{
ifif((thisthis..statestate..hasErrorhasError)){{
returnreturn((
<<div className div className=="min-h-screen flex items-center justify-center bg-gray-50" "min-h-screen flex items-center justify-center bg-gray-50">>
<<div className div className=="max-w-md w-full bg-white rounded-lg shadow-md p-6" "max-w-md w-full bg-white rounded-lg shadow-md p-6">>
<<div className div className=="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4" "flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">>
<<span className span className=="text-red-600 text-xl" "text-red-600 text-xl">>⚠⚠<<//spanspan>>
<<//divdiv>>
<<h1 className h1 className=="text-xl font-semibold text-center text-gray-900 mb-2" "text-xl font-semibold text-center text-gray-900 mb-2">>
SomethingSomething went wrong  went wrong
<<//h1h1>>
<<p className p className=="text-gray-600 text-center mb-4" "text-gray-600 text-center mb-4">>
WeWe're sorry for the inconvenience. The error has been logged and we' 're sorry for the inconvenience. The error has been logged and we'll look into it ll look into it..
<<//pp>>
<<buttonbutton
onClick               onClick=={{(())=>=>windowwindow..locationlocation..reloadreload(())}}
className               className=="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700" "w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
>>
ReloadReloadPagePage
<<//buttonbutton>>
{{processprocess..envenv..NODE_ENVNODE_ENV======'development''development'&&&&((
<<details className details className=="mt-4""mt-4">>
<<summary className summary className=="cursor-pointer text-sm text-gray-500" "cursor-pointer text-sm text-gray-500">>
ErrorErrorDetailsDetails((DevDevModeMode))
<<//summarysummary>>
<<pre className pre className=="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto" "mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">>
{{thisthis..statestate..errorerror&&&&thisthis..statestate..errorerror..toStringtoString(())}}
<<//prepre>>
<<//detailsdetails>>
))}}
<<//divdiv>>
<<//divdiv>>
));;
}}
returnreturnthisthis..propsprops..childrenchildren;;
}}
## 14.2 Centralized Logging Service}}
exportexportdefaultdefaultErrorBoundary ErrorBoundary;;
```
```javascript
// utils/logger.js // utils/logger.js
classclassLoggerLogger{{
constructor constructor(()){{
thisthis..logslogs==[[]];;
thisthis..maxLogsmaxLogs==10001000;;
}}
loglog((levellevel,, message message,, data  data =={{}})){{
constconst logEntry  logEntry =={{
level      level,,
message       message,,
data      data,,
timestamptimestamp::newnewDateDate(())..toISOString toISOString(()),,
tenanttenant::thisthis..getCurrentTenant getCurrentTenant(()),,
urlurl::windowwindow..locationlocation..hrefhref,,
}};;
thisthis..logslogs..pushpush((logEntrylogEntry));;
// Keep only the last N logs // Keep only the last N logs
ifif((thisthis..logslogs..lengthlength>>thisthis..maxLogsmaxLogs)){{
thisthis..logslogs..shiftshift(());;
}}
// Console output for development // Console output for development
ifif((processprocess..envenv..NODE_ENVNODE_ENV======'development''development')){{
console       console[[levellevel]]((messagemessage,, data data));;
}}
// Send critical errors to server // Send critical errors to server
ifif((level level ======'error''error')){{
thisthis..sendToServer sendToServer((logEntrylogEntry));;
}}
}}
getCurrentTenant getCurrentTenant(()){{
constconst hostname  hostname ==windowwindow..locationlocation..hostnamehostname;;
returnreturn hostname hostname..splitsplit(('.''.'))[[00]];;
}}
asyncasyncsendToServer sendToServer((logEntrylogEntry)){{
trytry{{
awaitawaitfetchfetch(('/api/logs''/api/logs',,{{
15. Future Enhancements & Scalability
## 15.1 Micro-Frontend Architecture Preparationmethodmethod::'POST''POST',,
headersheaders::{{
'Content-Type''Content-Type'::'application/json''application/json',,
}},,
bodybody::JSONJSON..stringifystringify((logEntrylogEntry)),,
}}));;
}}catchcatch((errorerror)){{
consoleconsole..errorerror(('Failed to send log to server:' 'Failed to send log to server:',, error error));;
}}
}}
infoinfo((messagemessage,, data data)){{
thisthis..loglog(('info''info',, message message,, data data));;
}}
warnwarn((messagemessage,, data data)){{
thisthis..loglog(('warn''warn',, message message,, data data));;
}}
errorerror((messagemessage,, data data)){{
thisthis..loglog(('error''error',, message message,, data data));;
}}
debugdebug((messagemessage,, data data)){{
thisthis..loglog(('debug''debug',, message message,, data data));;
}}
getLogsgetLogs(()){{
returnreturnthisthis..logslogs;;
}}
clearLogsclearLogs(()){{
thisthis..logslogs==[[]];;
}}
}}
exportexportconstconst logger  logger ==newnewLoggerLogger(());;
```
```javascript
// utils/microfrontendLoader.js // utils/microfrontendLoader.js
classclassMicrofrontendLoader MicrofrontendLoader{{
constructor constructor(()){{
thisthis..loadedMicrofrontends loadedMicrofrontends==newnewMapMap(());;
}}
asyncasyncloadMicrofrontend loadMicrofrontend((namename,, url url,, tenant tenant)){{
constconst key  key ==``${${namename}}--${${tenanttenant}}``;;
ifif((thisthis..loadedMicrofrontends loadedMicrofrontends..hashas((keykey)))){{
returnreturnthisthis..loadedMicrofrontends loadedMicrofrontends..getget((keykey));;
}}
trytry{{
constconst module  module ==awaitawaitimportimport((/* @vite-ignore */ /* @vite-ignore */``${${urlurl}}//${${namename}}.js.js``));;
thisthis..loadedMicrofrontends loadedMicrofrontends..setset((keykey,, module module));;
returnreturn module module;;
}}catchcatch((errorerror)){{
logger      logger..errorerror((``Failed to load microfrontend: Failed to load microfrontend: ${${namename}}``,,{{ error error,, tenant  tenant }}));;
throwthrow error error;;
}}
}}
asyncasyncloadTenantSpecificComponent loadTenantSpecificComponent((componentName componentName,, tenant tenant)){{
constconst tenantComponentUrl  tenantComponentUrl ==``/tenant-components//tenant-components/${${tenanttenant}}``;;
trytry{{
returnreturnawaitawaitthisthis..loadMicrofrontend loadMicrofrontend((componentName componentName,, tenantComponentUrl  tenantComponentUrl,, tenant tenant));;
}}catchcatch((errorerror)){{
// Fallback to default component // Fallback to default component
logger      logger..warnwarn((``Tenant-specific component not found, using default Tenant-specific component not found, using default``,,{{
component component:: componentName  componentName,,
tenant         tenant
}}));;
returnreturnawaitawaitthisthis..loadMicrofrontend loadMicrofrontend((componentName componentName,,'/default-components' '/default-components',, tenant tenant));;
}}
}}
}}
exportexportconstconst microfrontendLoader  microfrontendLoader ==newnewMicrofrontendLoader MicrofrontendLoader(());;
// Dynamic Component Loader Hook // Dynamic Component Loader Hook
exportexportconstconstuseDynamicComponent useDynamicComponent==((componentName componentName))=>=>{{
constconst{{ tenant  tenant }}==useTenantuseTenant(());;
constconst[[Component Component,, setComponent  setComponent]]==useStateuseState((nullnull));;
constconst[[loadingloading,, setLoading  setLoading]]==useStateuseState((truetrue));;
constconst[[errorerror,, setError setError]]==useStateuseState((nullnull));;
useEffectuseEffect(((())=>=>{{
letlet mounted  mounted ==truetrue;;
constconstloadComponent loadComponent==asyncasync(())=>=>{{
trytry{{
setLoadingsetLoading((truetrue));;
constconst module  module ==awaitawait microfrontendLoader  microfrontendLoader..loadTenantSpecificComponent loadTenantSpecificComponent((
componentName           componentName,,
tenant           tenant?.?.idid
));;
ifif((mountedmounted)){{
setComponent setComponent(((())=>=> module module..defaultdefault));;
setErrorsetError((nullnull));;
}}
}}catchcatch((errerr)){{
ifif((mountedmounted)){{
setErrorsetError((errerr));;
logger           logger..errorerror(('Failed to load dynamic component' 'Failed to load dynamic component',,{{
component component:: componentName  componentName,,
tenanttenant:: tenant tenant?.?.idid,,
errorerror:: err  err
}}));;
}}
}}finallyfinally{{
ifif((mountedmounted)){{
setLoadingsetLoading((falsefalse));;
}}
}}
}};;
ifif((tenanttenant?.?.idid)){{
loadComponent loadComponent(());;
}}
returnreturn(())=>=>{{
mounted       mounted ==falsefalse;;
}};;
}},,[[componentName componentName,, tenant tenant?.?.idid]]));;
## 15.2 CDN Integration for Assetsreturnreturn{{Component Component,, loading loading,, error  error }};;
}};;
```
```javascript
// utils/assetManager.js // utils/assetManager.js
classclassAssetManager AssetManager{{
constructor constructor(()){{
thisthis..cdnBaseUrl cdnBaseUrl== process process..envenv..REACT_APP_CDN_BASE_URL REACT_APP_CDN_BASE_URL||||'''';;
thisthis..assetCache assetCache==newnewMapMap(());;
}}
getTenantAssetUrl getTenantAssetUrl((tenanttenant,, assetPath assetPath)){{
constconst baseUrl  baseUrl ==thisthis..cdnBaseUrl cdnBaseUrl||||windowwindow..locationlocation..originorigin;;
returnreturn``${${baseUrlbaseUrl}}/tenant-assets//tenant-assets/${${tenanttenant}}//${${assetPathassetPath}}``;;
}}
getOptimizedImageUrl getOptimizedImageUrl((srcsrc,, options  options =={{}})){{
constconst{{ width width,, height height,, quality  quality ==8080,, format  format =='webp''webp'}}== options options;;
ifif((!!thisthis..cdnBaseUrl cdnBaseUrl)){{
returnreturn src src;;// No CDN, return original // No CDN, return original
}}
constconst params  params ==newnewURLSearchParams URLSearchParams(());;
ifif((widthwidth)) params params..setset(('w''w',, width width));;
ifif((heightheight)) params params..setset(('h''h',, height height));;
params    params..setset(('q''q',, quality quality));;
params    params..setset(('f''f',, format format));;
returnreturn``${${thisthis..cdnBaseUrl cdnBaseUrl}}/optimize?url=/optimize?url=${${encodeURIComponent encodeURIComponent((srcsrc))}}&&${${paramsparams}}``;;
}}
asyncasyncpreloadAssets preloadAssets((assetsassets)){{
constconst promises  promises == assets assets..mapmap((asyncasync((assetasset))=>=>{{
ifif((thisthis..assetCache assetCache..hashas((assetasset..urlurl)))){{
returnreturnthisthis..assetCache assetCache..getget((assetasset..urlurl));;
}}
constconst promise  promise ==newnewPromisePromise((((resolveresolve,, reject reject))=>=>{{
ifif((assetasset..typetype======'image''image')){{
constconst img  img ==newnewImageImage(());;
img          img..onloadonload==(())=>=>resolveresolve((assetasset..urlurl));;
img          img..onerroronerror== reject reject;;
img          img..srcsrc== asset asset..urlurl;;
}}elseelse{{
// For other asset types, use fetch // For other asset types, use fetch
fetchfetch((assetasset..urlurl))
..thenthen((responseresponse=>=> response response..okok??resolveresolve((assetasset..urlurl))::rejectreject(())))
..catchcatch((rejectreject));;
}}
}}));;
thisthis..assetCache assetCache..setset((assetasset..urlurl,, promise promise));;
returnreturn promise promise;;
}}));;
returnreturnPromisePromise..allSettledallSettled((promisespromises));;
}}
}}
exportexportconstconst assetManager  assetManager ==newnewAssetManager AssetManager(());;
// Optimized Image Component // Optimized Image Component
exportexportconstconstOptimizedImage OptimizedImage==(({{
src  src,,
alt  alt,,
width  width,,
height  height,,
className   className,,
lazy   lazy ==truetrue,,
......props props
}}))=>=>{{
constconst[[imageSrcimageSrc,, setImageSrc  setImageSrc]]==useStateuseState((srcsrc));;
constconst[[isLoadingisLoading,, setIsLoading  setIsLoading]]==useStateuseState((truetrue));;
constconst[[hasErrorhasError,, setHasError  setHasError]]==useStateuseState((falsefalse));;
constconst imgRef  imgRef ==useRefuseRef(());;
useEffectuseEffect(((())=>=>{{
// Generate optimized image URL // Generate optimized image URL
constconst optimizedSrc  optimizedSrc == assetManager  assetManager..getOptimizedImageUrl getOptimizedImageUrl((srcsrc,,{{
width      width,,
height      height,,
}}));;
setImageSrc setImageSrc((optimizedSrc optimizedSrc));;
}},,[[srcsrc,, width width,, height height]]));;
constconsthandleLoad handleLoad==(())=>=>{{
setIsLoading setIsLoading((falsefalse));;
}};;
16. Summary & Best Practices
This comprehensive frontend architecture provides:
✅ Multi-Tenant Capabilities:
Dynamic tenant detection and routing
Isolated tenant contexts and theming
Tenant-specific asset management
✅ Performance Optimization:
Code splitting and lazy loadingconstconsthandleError handleError==(())=>=>{{
setHasError setHasError((truetrue));;
setIsLoading setIsLoading((falsefalse));;
// Fallback to original image // Fallback to original image
setImageSrc setImageSrc((srcsrc));;
}};;
returnreturn((
<<div className div className=={{``relative relative ${${className className}}``}}>>
{{isLoading isLoading &&&&((
<<div className div className=="absolute inset-0 bg-gray-200 animate-pulse rounded" "absolute inset-0 bg-gray-200 animate-pulse rounded"//>>
))}}
<<imgimg
ref        ref=={{imgRefimgRef}}
src        src=={{imageSrcimageSrc}}
alt        alt=={{altalt}}
loading         loading=={{lazy lazy ??'lazy''lazy'::'eager''eager'}}
onLoad         onLoad=={{handleLoad handleLoad}}
onError         onError=={{handleError handleError}}
className         className=={{``${${className className}}${${isLoading isLoading ??'opacity-0''opacity-0'::'opacity-100''opacity-100'}} transition-opacity duration-300  transition-opacity duration-300``}}
{{......propsprops}}
//>>
{{hasError hasError &&&&((
<<div className div className=="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500" "absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500">>
ImageImage not available  not available
<<//divdiv>>
))}}
<<//divdiv>>
));;
}};;
Advanced caching strategies
Service Worker implementation
Optimized asset delivery
✅ Scalability Features:
Micro-frontend ready architecture
CDN integration support
Progressive Web App capabilities
Real-time updates via WebSocket
✅ Production Readiness:
Comprehensive error handling
Monitoring and analytics
Health checks and diagnostics
Security best practices
✅ QNAP Integration:
Docker containerization
Nginx configuration for multi-tenant routing
Resource optimization for NAS deployment
Easy migration path to cloud platforms
This architecture ensures your Etsy Seller Automater frontend can scale from a local QNAP
deployment to a full cloud-based multi-tenant SaaS platform while maintaining excellent performance
and user experience.
```