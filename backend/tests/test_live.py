import asyncio

from app.core.events import MAX_PER_USER, hub
from tests.conftest import login


def test_events_need_sign_in(client):
    assert client.get("/api/events").status_code == 401


def test_commit_tells_open_pages_and_a_read_does_not(client, admin):
    async def go():
        sub = hub.join(1)
        try:
            await asyncio.to_thread(client.post, "/api/customers", json={"name": "Live Co"}, headers=admin)
            await asyncio.wait_for(sub.flag.wait(), 2)          # a saved change wakes the page
            sub.flag.clear()
            await asyncio.to_thread(client.get, "/api/items", headers=admin)
            await asyncio.to_thread(client.get, "/api/customers", headers=admin)
            try:
                await asyncio.wait_for(sub.flag.wait(), 0.4)     # reading changes nothing
                return False
            except asyncio.TimeoutError:
                return True
        finally:
            hub.leave(sub)
    assert asyncio.run(go())
    assert hub.count() == 0


def test_a_failed_request_does_not_announce_anything(client, admin):
    async def go():
        sub = hub.join(1)
        try:
            await asyncio.to_thread(client.post, "/api/customers", json={"name": ""}, headers=admin)   # rejected as invalid
            try:
                await asyncio.wait_for(sub.flag.wait(), 0.4)
                return False
            except asyncio.TimeoutError:
                return True
        finally:
            hub.leave(sub)
    assert asyncio.run(go())


def test_one_user_cannot_hold_unlimited_connections():
    async def go():
        subs = [hub.join(7) for _ in range(MAX_PER_USER)]
        extra = hub.join(7)
        other = hub.join(8)
        for s in (*subs, other):
            if s:
                hub.leave(s)
        return all(subs), extra, other is not None
    ok, extra, other_ok = asyncio.run(go())
    assert ok and extra is None and other_ok
