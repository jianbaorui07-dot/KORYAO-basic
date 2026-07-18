# CreNexus Creative Workbench

This is the local frontend for the CreNexus software prototype. It connects to
the CreNexus backend, reads real capability and recipe data, and presents it as
an artistic control surface with a Three.js generative background.

The main flow is:

1. Choose a creative software bridge.
2. Choose a reviewed recipe.
3. Generate a dry-run plan.
4. Preview evidence.
5. Confirm the execution target.
6. Record the result and audit event.

## Run Locally

Start the backend from the repository root:

```powershell
npm.cmd run app:dev
```

Or start the backend and frontend separately:

```powershell
npm.cmd run starbridge:backend
```

Start the frontend:

```powershell
cd examples\starbridge_frontend
npm install --package-lock=false
npm run dev
```

Default URLs:

- Backend: `http://127.0.0.1:8765`
- Frontend: `http://127.0.0.1:5173`

If the backend is running on another port:

```powershell
$env:VITE_STARBRIDGE_API_URL="http://127.0.0.1:52420"
npm run dev
```

When the production build is served by `starbridge_mcp.backend`, the frontend
uses the current page origin automatically. No extra API URL setting is needed.

## Backend APIs Used

- `GET /api/bootstrap`
- `GET /api/catalog`
- `GET /api/tiers`
- `GET /api/hybrid`
- `GET /api/audit/history`
- `DELETE /api/audit/history`
- `POST /api/recipes/{recipe_id}/plan`
- `POST /api/recipes/{recipe_id}/evidence`
- `POST /api/recipes/{recipe_id}/run`

## Build

```powershell
npm run build
```

## Safety Boundary

- The frontend does not add new write powers.
- It calls the backend, and the backend reuses the existing MCP safety rules.
- Real local writes still require bridge-specific confirmation flags and safe roots.
- The Run button records a confirmed safe execution request; bridge-specific tools
  remain responsible for any real sandbox output.
