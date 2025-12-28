# Finance Tracking App - Frontend

Frontend Next.js for personal finance management application.

## Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local

# Start dev server
npm run dev
```

Application will be available at http://localhost:3000

## Structure

- `src/app/` - Pages and layouts
- `src/components/` - Reusable components
- `src/hooks/` - Custom hooks (useAuth, useAPI)
- `src/lib/` - Utilities (API client, auth, formatting)

## Scripts

```bash
# Development
npm run dev

# Build
npm run build

# Production
npm run start

# Type check
npm run type-check

# Lint
npm run lint
```

## Architecture

- **App Router** (Next.js 14+) for routing
- **TypeScript** for type safety
- **TailwindCSS** for styling
- **SWR** for data fetching
- **Recharts** for charts

## Environment Variables

See `.env.example` for all available variables.

### Important keys:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_APP_URL` - Application URL (for links)

## Pages

- `/` - Redirect to dashboard
- `/login` - Login
- `/register` - Registration
- `/dashboard` - Dashboard
- `/transactions` - Transaction management
- `/budgets` - Budget management
- `/net-worth` - Net worth
- `/accounts` - Account management

## Components

- `useAuth` - Authentication management and user state
- `useAPI` - Data fetching with SWR
- `apiClient` - Axios client with interceptors
