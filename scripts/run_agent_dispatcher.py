"""Standalone durable outbox dispatcher. Restarting resumes pending events."""

import argparse
import asyncio

from backend.app.agent.events import EventDispatcher
from backend.app.scientific.research_store import connect


async def run(poll_seconds: float):
    dispatcher = EventDispatcher(connect)
    while True:
        dispatched = await asyncio.to_thread(dispatcher.dispatch_once)
        if dispatched is None:
            await asyncio.sleep(poll_seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    args = parser.parse_args()
    if args.poll_seconds <= 0:
        parser.error("poll interval must be positive")
    try:
        asyncio.run(run(args.poll_seconds))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
