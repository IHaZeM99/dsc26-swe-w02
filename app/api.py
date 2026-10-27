"""HTTP layer for the Tawseel parcel service.

The HTTP layer translates requests into calls to app.domain; the domain decides.
See README.md for the four operations, their operationIds and their errors.
"""
from fastapi import FastAPI, Request, Response, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field
import itertools
import base64
from http import HTTPStatus

from app.domain import EventType, InvalidTransition, Parcel, ParcelState, apply_event  # noqa: F401


class ParcelIn(BaseModel):
    merchant_ref: str = Field(min_length=1, max_length=64)
    cod_amount_piastres: int = Field(ge=0, le=5_000_000, strict=True)
    address_text: str = Field(min_length=1, max_length=500)

class ParcelOut(BaseModel):
    id: str
    merchant_ref: str
    cod_amount_piastres: int
    address_text: str
    state: ParcelState
    attempts: int

class ParcelPage(BaseModel):
    items: list[ParcelOut]
    next_cursor: str | None

class EventIn(BaseModel):
    type: EventType

class ProblemError(Exception):
    def __init__(self, status: int, title: str, detail: str | None = None):
        self.status = status
        self.title = title
        self.detail = detail
    

def create_app() -> FastAPI:
    """Return a NEW FastAPI app with its own empty in-memory store.

    Tests call this once per test, so nothing may be shared between two apps
    (no module-level dicts or counters for parcels).
    """
    app = FastAPI(title = "Tawseel")
    store: dict[str, Parcel] = {}
    counter = itertools.count(1)

    @app.exception_handler(ProblemError)
    async def problem_handler(request: Request, exc: ProblemError):
        return JSONResponse(
            status_code=exc.status,
            content={
                "type": "about:blank",
                "title": exc.title,
                "status": exc.status,
                "detail": exc.detail,
            },
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        by_field = {}
        for err in exc.errors():
            loc = tuple(err["loc"])
            if loc not in by_field:
                by_field[loc] = {"loc": list(loc), "msg": err["msg"]}
        return JSONResponse(
            status_code=422,
            content={
                "type": "about:blank",
                "title": "Unprocessable Entity",
                "status": 422,
                "detail": "Request validation failed",
                "errors": list(by_field.values()),
            },
            media_type="application/problem+json",
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": "about:blank",
                "title": HTTPStatus(exc.status_code).phrase,
                "status": exc.status_code,
                "detail": str(exc.detail),
            },
            media_type="application/problem+json",
        )
    
    @app.post('/v1/parcels',
        operation_id="createParcel",
        status_code=201,
        response_model=ParcelOut,
        responses={
            409: {"description": "Duplicate merchant_ref"},
            422: {"description": "Invalid body"},
        },  
    )
    def create_parcel(body: ParcelIn, response: Response):
        for parcel_item in store.values():
            if parcel_item.merchant_ref == body.merchant_ref:
                raise ProblemError(409, "Conflict", "merchant_ref already exists")
        parcel_id = f"pcl_{next(counter)}"
        parcel = Parcel(
            id = parcel_id,
            merchant_ref=body.merchant_ref,
            cod_amount_piastres=body.cod_amount_piastres,
            address_text=body.address_text,
        )
        store[parcel_id] = parcel
        response.headers["Location"] = f"/v1/parcels/{parcel_id}"
        return parcel

    @app.get('/v1/parcels/{parcel_id}',
        operation_id="getParcel",
        response_model=ParcelOut,
        responses={
            404: {"description": "Parcel not found"},
        },
    )
    def get_parcel(parcel_id: str):
        parcel = store.get(parcel_id)
        if parcel is None:
            raise ProblemError(404, "Not Found", "Parcel not found")
        return parcel

    @app.get('/v1/parcels',
        operation_id="listParcels",
        response_model=ParcelPage,
        responses={
            400: {"description": "Invalid cursor"},
            422: {"description": "Invalid state or limit"},
        },
    )    
    def list_parcels(state: ParcelState | None = None, limit: int = Query(20, ge=1, le=100), cursor: str | None = None):
        ids = list(store)
        items = list(store.values())

        if cursor is not None:
            try:
                after_id = base64.urlsafe_b64decode(cursor.encode()).decode()
            except Exception:
                raise ProblemError(400, "Bad Request", "Invalid cursor")
            if after_id not in store:
                raise ProblemError(400, "Bad Request", "Invalid cursor")
            items = items[ids.index(after_id)+1:]
        
        if state is not None:
            items = [p for p in items if p.state == state]
        
        page = items[:limit]
        next_cursor = None
        if len(items) > limit:
            next_cursor = base64.urlsafe_b64encode(page[-1].id.encode()).decode()

        return {"items": page, "next_cursor": next_cursor}

    @app.post('/v1/parcels/{parcel_id}/events',
        operation_id="recordParcelEvent",
        response_model=ParcelOut,
        responses={
            404: {"description": "Parcel not found"},
            409: {"description": "Invalid transition"},
            422: {"description": "unknown or missing event type"},
        },
    )
    def record_parcel_event(parcel_id: str, body: EventIn):
        parcel = store.get(parcel_id)
        if parcel is None:
            raise ProblemError(404, "Not Found", "Parcel not found")
        try:
            new_parcel = apply_event(parcel, body.type)
        except InvalidTransition:
            raise ProblemError(409, "Conflict", "Event not allowed in current state")
        store[parcel_id] = new_parcel
        return new_parcel

    
    
    return app



# `uvicorn app.api:app` needs a module-level app. Once create_app() works,
# replace the line below with:  app = create_app()
app = create_app()
