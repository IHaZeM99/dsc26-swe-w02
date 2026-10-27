# AI usage

Keep all three headings exactly as they are. If this file is missing or any heading is
missing, the grader stops and gives 0 ("AI_USAGE.md missing or incomplete"). The content
is not scored, but your Track Mentor reads it and the W8 defence can ask about it.

## Tools

Claude
Used for some help in api.py, it helped me with syntax as i was using django all the time but i'm a little new to fastApi.
Also it gave me the idea of putting table in domain.py instead of a pail of if state == and event ==

## What AI got wrong

In api.py it skip this rule:
Every error, including 422 validation errors and 422s for query parameters, is application/problem+json (RFC 9457) with at least type, title and status (the same number as the HTTP status).
so when i tried it with pytest -q it passed however when i checked the rules i didn't see that i implemented it.

## In my own words


1. Why does `listParcels` need a cursor rather than an offset?
Because offset has a problem that if my filter is state=created and it's the page 1 which is first 20 item, if those 20 get dispatched, now the next page (20 to 40) have moved up to positions (1 to 20), so if i search for the next page which is 2 it will skip them. So a cursor can avoid this problem by getting a cursor on the last item i saw not just ids.
2. Which of your four operations would break the courier app if you renamed one field, and who would have to approve that change?
I think it would be recordParcelEvent as if the courier can't change the state of the parcel it will be a big problem
we first need to approve it with the courier app team and also we can use /v2/ so we don't ruin everything
