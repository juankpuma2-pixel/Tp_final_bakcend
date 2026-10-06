from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.core.config import settings
from app.routers import productos, auth, pedidos, usuarios
# Creamos las tablas en la base de datos al arrancar
Base.metadata.create_all(bind=engine)

# Instanciamos la app con el título del .env
app = FastAPI(title=settings.PROJECT_NAME)

# Middleware CORS cargado dinámicamente desde .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API Backend Ecommerce activa", "docs": "/docs"}

# Parte 3: Incluimos las rutas de productos
app.include_router(productos.router)

# Clase 7: Incluimos las rutas de autenticación
app.include_router(auth.router)

# Clase 8: Incluimos las rutas de pedidos y checkout
app.include_router(pedidos.router)

# Incluimos las rutas de usuarios
app.include_router(usuarios.router)