"""Parcel lifecycle rules for Tawseel.

Pure Python: do not import fastapi, starlette, pydantic or sqlalchemy here
(a hidden test checks). Keep the names below exactly as they are.
"""
from dataclasses import dataclass
from enum import StrEnum
from dataclasses import dataclass, replace

MAX_ATTEMPTS = 3


class ParcelState(StrEnum):
    CREATED = "created"
    OUT_FOR_DELIVERY = "out_for_delivery"
    FAILED_ATTEMPT = "failed_attempt"
    DELIVERED = "delivered"
    RETURNED = "returned"


class EventType(StrEnum):
    DISPATCH = "dispatch"
    DELIVER = "deliver"
    FAIL = "fail"
    RETURN = "return"


class InvalidTransition(Exception): ...


@dataclass(frozen=True)
class Parcel:
    id: str
    merchant_ref: str
    cod_amount_piastres: int
    address_text: str
    state: ParcelState = ParcelState.CREATED
    attempts: int = 0

TABLE = {
    (ParcelState.CREATED, EventType.DISPATCH): ParcelState.OUT_FOR_DELIVERY,
    (ParcelState.OUT_FOR_DELIVERY, EventType.DELIVER): ParcelState.DELIVERED,
    (ParcelState.OUT_FOR_DELIVERY, EventType.FAIL): ParcelState.FAILED_ATTEMPT,
    (ParcelState.FAILED_ATTEMPT, EventType.DISPATCH): ParcelState.OUT_FOR_DELIVERY,
    (ParcelState.FAILED_ATTEMPT, EventType.RETURN): ParcelState.RETURNED,
}

def apply_event(parcel: Parcel, event: EventType) -> Parcel:
    """Return a new Parcel. Raise InvalidTransition if the event is not allowed.

    - created + dispatch -> out_for_delivery, attempts + 1
    - out_for_delivery + deliver -> delivered
    - out_for_delivery + fail -> failed_attempt
    - failed_attempt + dispatch -> out_for_delivery, attempts + 1, only if attempts < MAX_ATTEMPTS
    - failed_attempt + return -> returned
    - delivered and returned are final; every other combination raises InvalidTransition.
    Never mutate the input parcel.
    """
    new_state = TABLE.get((parcel.state, event))
    if new_state is None:
        raise InvalidTransition(f"Cannot apply {event} to {parcel.state}")
    new_attempts = parcel.attempts
    if event == EventType.DISPATCH:
        new_attempts += 1
        if new_attempts > MAX_ATTEMPTS:
            raise InvalidTransition(f"Cannot dispatch parcel with {new_attempts} attempts")
    return replace(parcel, state=new_state, attempts=new_attempts)

