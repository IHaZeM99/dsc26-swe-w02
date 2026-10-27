# 1. The lifecycle rules live in domain.py

## Status

Accepted

## Context

the lifecycle rules live in domain.py,away from FastAPI, so they can change without touching the HTTP code.
The HTTP layer deals with different things: status codes, JSON, validation.

## Decision

We will put the main rules in a pure Python module with no framework imports, the API only calls apply_event.

## Consequences

Easier: Changing framework will be much easier at anytime also changing a rule means editing one place.

Harder: we now have two classes for the same thing like Parcel and ParcelOut.