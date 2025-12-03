from fastapi.middleware.cors import CORSMiddleware

from . import create_app

app = create_app()

# Allow local frontend(s) and future deployed origin.
# For simplicity in this assignment, we allow all origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


