from fastapi import APIRouter

router = APIRouter()


@router.get("/live", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "alive"}
