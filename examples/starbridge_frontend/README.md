# StarBridge Creative Workbench

This is the local frontend for the StarBridge software prototype. It connects to
the StarBridge backend, reads real capability and recipe data, and presents it as
an artistic control surface with a Three.js generative background.

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

## Backend APIs Used

- `GET /api/bootstrap`
- `POST /api/recipes/{recipe_id}/plan`
- `POST /api/recipes/{recipe_id}/evidence`

## Build

```powershell
npm run build
```

## Safety Boundary

- The frontend does not add new write powers.
- It calls the backend, and the backend reuses the existing MCP safety rules.
- Real local writes still require bridge-specific confirmation flags and safe roots.
