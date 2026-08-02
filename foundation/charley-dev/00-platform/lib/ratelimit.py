"""A requests session that respects Procore's hourly quota.

WHY THIS EXISTS
---------------
Procore allows 600 requests per hour per client. A full portfolio pull needs far more:
36 endpoints across 19 active projects is ~680 project-scoped calls before pagination, so a
single unthrottled full run CANNOT finish inside the quota. Measured 2026-08-02 - the run
died mid-flight with:

    X-Rate-Limit-Limit: 600      X-Rate-Limit-Remaining: 0      Retry-After: (absent)

Two things go wrong without this wrapper:

1. **Procore does not send `Retry-After` on a 429.** It sends `X-Rate-Limit-Reset`, a Unix
   epoch. The shared extractor's retry honours `Retry-After` and otherwise backs off
   exponentially - 2s, 4s, 8s, 16s - which against a 35-minute window is five wasted
   attempts and then a crash.
2. **The crash loses the whole run.** Every endpoint already fetched is discarded because the
   exception unwinds past them.

So this wrapper does two things the generic retry cannot:

- Reads `X-Rate-Limit-Reset` and sleeps until the window actually rolls over, rather than
  guessing with exponential backoff.
- Tracks `X-Rate-Limit-Remaining` and refuses to start a request once a reserve is gone,
  raising `QuotaExhausted` instead. The caller catches it, keeps everything fetched so far,
  and lands a partial batch. A partial batch is re-runnable; a crashed run is not.

Injected rather than patched: `procore_extract` takes `session` as a parameter, so this
wraps it from the outside and `src/procore/` stays untouched.

ponytail: a reserve of 20 and a hard sleep cap. Both are single constants. The real fix is
incremental loading - full pulls of 36 endpoints do not belong on a nightly schedule - but
that is a scheduling decision, not a transport one.
"""

from __future__ import annotations

import time
from typing import Any

RESERVE = 20            # stop this many requests short, so a retry has room to land
MAX_SLEEP = 2400        # 40 min: longer than Procore's hour-long window can leave to run
LIMIT_HEADER = "X-Rate-Limit-Limit"
REMAINING_HEADER = "X-Rate-Limit-Remaining"
RESET_HEADER = "X-Rate-Limit-Reset"


class QuotaExhausted(RuntimeError):
    """Out of quota and unwilling to wait. Carries the reset time so the caller can report
    when a re-run becomes possible."""

    def __init__(self, reset_epoch: float, remaining: int) -> None:
        self.reset_epoch = reset_epoch
        self.remaining = remaining
        wait = max(0, reset_epoch - time.time())
        super().__init__(
            f"Procore quota exhausted ({remaining} left); resets in {wait / 60:.1f} min"
        )


class RateLimitedSession:
    """Wraps a requests.Session, gating on Procore's rate-limit headers.

    Proxies get/post rather than subclassing, so it works with any session-like object and
    stays obvious about what it intercepts.
    """

    def __init__(self, session: Any, *, reserve: int = RESERVE,
                 wait: bool = True, sleep: Any = time.sleep) -> None:
        self.session = session
        self.reserve = reserve
        self.wait = wait            # False = fail fast instead of sleeping out the window
        self._sleep = sleep
        self.remaining: int | None = None
        self.reset_epoch: float = 0.0
        self.waited_seconds = 0.0
        self.requests_made = 0

    # -- header bookkeeping ------------------------------------------------

    def _observe(self, response: Any) -> None:
        headers = getattr(response, "headers", {}) or {}
        raw_remaining = headers.get(REMAINING_HEADER)
        raw_reset = headers.get(RESET_HEADER)
        if raw_remaining is not None:
            try:
                self.remaining = int(raw_remaining)
            except (TypeError, ValueError):
                pass
        if raw_reset is not None:
            try:
                self.reset_epoch = float(raw_reset)
            except (TypeError, ValueError):
                pass

    def _seconds_until_reset(self, now: float | None = None) -> float:
        now = time.time() if now is None else now
        return max(0.0, self.reset_epoch - now)

    # -- the gate ----------------------------------------------------------

    def _gate(self) -> None:
        """Block or raise before spending a request we do not have."""
        if self.remaining is None or self.remaining > self.reserve:
            return

        wait_for = self._seconds_until_reset()
        if not self.wait or wait_for > MAX_SLEEP:
            raise QuotaExhausted(self.reset_epoch, self.remaining)

        if wait_for > 0:
            print(f"      rate limit: {self.remaining} left, sleeping "
                  f"{wait_for / 60:.1f} min until the window resets")
            self._sleep(wait_for + 1)
            self.waited_seconds += wait_for + 1
        # The next response refreshes the counters; assume the window rolled over.
        self.remaining = None

    def _send(self, method: str, url: str, **kwargs: Any) -> Any:
        self._gate()
        response = getattr(self.session, method)(url, **kwargs)
        self.requests_made += 1
        self._observe(response)

        # A 429 that slipped past the gate: honour the reset header, then retry once.
        if getattr(response, "status_code", None) == 429:
            wait_for = self._seconds_until_reset()
            if self.wait and 0 < wait_for <= MAX_SLEEP:
                print(f"      429: sleeping {wait_for / 60:.1f} min until reset")
                self._sleep(wait_for + 1)
                self.waited_seconds += wait_for + 1
                self.remaining = None
                response = getattr(self.session, method)(url, **kwargs)
                self.requests_made += 1
                self._observe(response)
            else:
                raise QuotaExhausted(self.reset_epoch, self.remaining or 0)
        return response

    def get(self, url: str, **kwargs: Any) -> Any:
        return self._send("get", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        # Token exchange is not rate-limited the same way and must never be gated - a
        # blocked token call cannot even report why.
        response = self.session.post(url, **kwargs)
        self.requests_made += 1
        self._observe(response)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self.session, name)


# --------------------------------------------------------------------------
# Self-check
# --------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, status: int = 200, **headers: str) -> None:
        self.status_code = status
        self.headers = headers


class _FakeSession:
    """Replays a scripted list of responses and records the URLs it was asked for."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []

    def get(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append(url)
        return self.responses.pop(0) if self.responses else _FakeResponse()

    post = get


def _selftest() -> None:
    slept: list[float] = []
    now = time.time()

    # 1. Plenty of quota -> no sleeping, no gating.
    s = RateLimitedSession(_FakeSession([
        _FakeResponse(200, **{REMAINING_HEADER: "599", RESET_HEADER: str(now + 3600)}),
        _FakeResponse(200, **{REMAINING_HEADER: "598", RESET_HEADER: str(now + 3600)}),
    ]), sleep=slept.append)
    s.get("/a")
    s.get("/b")
    assert not slept, "slept while quota was plentiful"
    assert s.remaining == 598

    # 2. Down to the reserve -> sleeps until the reset rather than backing off blindly.
    slept.clear()
    s = RateLimitedSession(_FakeSession([
        _FakeResponse(200, **{REMAINING_HEADER: "5", RESET_HEADER: str(now + 120)}),
        _FakeResponse(200, **{REMAINING_HEADER: "600", RESET_HEADER: str(now + 3720)}),
    ]), sleep=slept.append)
    s.get("/a")          # observes remaining=5
    s.get("/b")          # gate fires
    assert len(slept) == 1, slept
    assert 100 < slept[0] < 140, f"slept {slept[0]}s, expected ~121s to the reset"

    # 3. wait=False -> raises instead of blocking, and says when a re-run is possible.
    s = RateLimitedSession(_FakeSession([
        _FakeResponse(200, **{REMAINING_HEADER: "2", RESET_HEADER: str(now + 1800)}),
    ]), wait=False, sleep=slept.append)
    s.get("/a")
    try:
        s.get("/b")
        raise AssertionError("expected QuotaExhausted")
    except QuotaExhausted as exc:
        assert "resets in" in str(exc)
        assert 29 < (exc.reset_epoch - time.time()) / 60 < 31

    # 4. A reset further out than MAX_SLEEP raises rather than sleeping for an hour.
    s = RateLimitedSession(_FakeSession([
        _FakeResponse(200, **{REMAINING_HEADER: "1", RESET_HEADER: str(now + MAX_SLEEP + 600)}),
    ]), sleep=slept.append)
    s.get("/a")
    try:
        s.get("/b")
        raise AssertionError("expected QuotaExhausted for an over-long wait")
    except QuotaExhausted:
        pass

    # 5. A 429 that slips through is retried once after the reset, not abandoned.
    slept.clear()
    fake = _FakeSession([
        _FakeResponse(429, **{RESET_HEADER: str(now + 60)}),
        _FakeResponse(200, **{REMAINING_HEADER: "600", RESET_HEADER: str(now + 3660)}),
    ])
    s = RateLimitedSession(fake, sleep=slept.append)
    response = s.get("/a")
    assert response.status_code == 200, "429 was not retried"
    assert len(slept) == 1 and 55 < slept[0] < 65, slept
    assert fake.calls == ["/a", "/a"]

    # 6. Missing headers must not gate - a non-Procore response should pass straight through.
    s = RateLimitedSession(_FakeSession([_FakeResponse(200), _FakeResponse(200)]),
                           sleep=slept.append)
    s.get("/a")
    s.get("/b")
    assert s.remaining is None

    print("  ok  plentiful quota is never gated")
    print("  ok  at the reserve, sleeps to X-Rate-Limit-Reset (not exponential backoff)")
    print("  ok  wait=False raises QuotaExhausted carrying the reset time")
    print("  ok  a wait longer than MAX_SLEEP raises rather than blocking for an hour")
    print("  ok  a 429 is retried once after the reset window")
    print("  ok  responses without rate-limit headers pass through ungated")
    print("\nratelimit: 6 checks passed")


if __name__ == "__main__":
    _selftest()
