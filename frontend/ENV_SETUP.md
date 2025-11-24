# Frontend Environment Variables Setup

Create a `.env.local` file in the `frontend/` directory with the following variables:

```bash
# Backend API URL
# Default: http://localhost:8000
# Change this if your backend is running on a different host/port
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Quick Setup

1. Create the `.env.local` file:
```bash
cd frontend
touch .env.local
# Add: NEXT_PUBLIC_API_URL=http://localhost:8000
```

2. Or copy from this template:
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

## Notes

- Next.js requires the `NEXT_PUBLIC_` prefix for environment variables that should be accessible in the browser
- The default value is `http://localhost:8000` if the variable is not set
- Restart the Next.js dev server after changing environment variables

