from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import crear_token, hash_password, verificar_password
from app.dependencies import get_current_user, get_db
from app.models import Usuario
from app.schemas import Token, UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post(
    "/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED
)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Validación estricta de consentimiento (Ley 25.326)
    if not usuario.acepta_politica_privacidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe aceptar la Política de Privacidad y Tratamiento de Datos Personales para registrarse"
        )

    db_user = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado"
        )

    try:
        nuevo_usuario = Usuario(
            nombre=usuario.nombre,
            email=usuario.email,
            password_hash=hash_password(usuario.password),
            acepto_tratamiento=bool(usuario.acepto_tratamiento if usuario.acepto_tratamiento is not None else True),
            acepta_politica_privacidad=True,
            rol="customer",
            is_admin=False,
            activo=True,
        )
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la base de datos al registrar usuario: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    usuario = (
        db.query(Usuario).filter(Usuario.email == form_data.username).first()
    )
    if not usuario or not verificar_password(
        form_data.password, usuario.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esta cuenta ha sido dada de baja",
            headers={"WWW-Authenticate": "Bearer"},
        )

    is_user_admin = bool(getattr(usuario, "is_admin", False) or usuario.rol == "admin")

    access_token = crear_token(
        data={
            "sub": usuario.email,
            "rol": usuario.rol,
            "is_admin": is_user_admin,
            "tipo": "access"
        },
        expires_delta=timedelta(minutes=settings.ACCESS_MIN),
    )
    refresh_token = crear_token(
        data={
            "sub": usuario.email,
            "rol": usuario.rol,
            "is_admin": is_user_admin,
            "tipo": "refresh"
        },
        expires_delta=timedelta(minutes=settings.REFRESH_MIN),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UsuarioOut)
def obtener_perfil(current_user: Usuario = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=Token)
def renovar_token(payload_req: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(
            payload_req.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("tipo") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token provisto no es un refresh token válido",
            )

        email: str = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.activo == True).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo o no encontrado",
            )

        is_user_admin = bool(getattr(usuario, "is_admin", False) or usuario.rol == "admin")

        nuevo_access_token = crear_token(
            data={"sub": usuario.email, "rol": usuario.rol, "is_admin": is_user_admin, "tipo": "access"},
            expires_delta=timedelta(minutes=settings.ACCESS_MIN),
        )
        nuevo_refresh_token = crear_token(
            data={"sub": usuario.email, "rol": usuario.rol, "is_admin": is_user_admin, "tipo": "refresh"},
            expires_delta=timedelta(minutes=settings.REFRESH_MIN),
        )

        return {
            "access_token": nuevo_access_token,
            "refresh_token": nuevo_refresh_token,
            "token_type": "bearer",
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
