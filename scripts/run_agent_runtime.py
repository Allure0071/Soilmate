"""Phase 3 separate background process: events, Manager and bounded Test Workers."""
import argparse
import time
from backend.app.agent.events import EventDispatcher
from backend.app.agent.manager import TaskManager
from backend.app.agent.runtime import WorkerRuntime
from backend.app.agent.artifact_store import ArtifactStore
from backend.app.scientific.research_store import connect,ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    dispatcher=EventDispatcher(connect)
    manager=TaskManager()
    runtime=WorkerRuntime(connect,ArtifactStore(ROOT/'data'/'agent_artifacts'))
    while True:
        for _ in range(100):
            if dispatcher.dispatch_once() is None: break
        for _ in range(100):
            if dispatcher.consume_once('manager',manager.handle) is None: break
        for _ in range(100):
            if dispatcher.consume_once('runtime',runtime.handle) is None: break
        dispatcher.consume_once('audit',lambda con,event: None)
        count=runtime.tick()
        if args.once: break
        if not count: time.sleep(.25)


if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: pass
