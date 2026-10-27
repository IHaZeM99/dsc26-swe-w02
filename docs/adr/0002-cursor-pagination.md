# 2. The cursor points at the last parcel you saw

## Status

Accepted

## Context

To replace offset "skip the first N matching items" with cursor which the systems knows where is the last parcel the courier or merchant saw

## Decision

we will encode the cursor so no one tries to hack or know anything related to ids in our system, and the next page will be sent as usual.

## Consequences
Easier: no skipped or repeated items, because a parcel’s position in creation order never changes. There is also no empty page at the end.

Harder: clients can’t jump to “page 5”. The server must validate cursors and return 400 for ones it never issued. Clients must treat the cursor as opaque. It also relies on parcels staying in creation order, which would break if you ever allowed deleting them. Base64 only hides the id, it isn’t very secured.