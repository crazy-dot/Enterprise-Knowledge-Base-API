from fastapi import FastAPI


from router import users, auth, workspace, documents
import uvicorn

app = FastAPI(
    title="My Production API",
    version="1.0.0",
    description="Secure API with JWT and User Management"
)

# The order here defines the order in the UI

app.include_router(auth.api)
app.include_router(users.app)
app.include_router(workspace.router)
app.include_router(documents.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)