from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def test_v1():
    return {"message": "Hello World from v1!"}
