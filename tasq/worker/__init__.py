from ..actors.actorsystem import get_actorsystem
from .actors import WorkerActor
from .executor import ProcessQueueExecutor
from .jobqueue import JobQueue


def build_worker_actor_router(router_class, num_workers, ctx=None):
    if ctx is None:
        ctx = get_actorsystem("")
    return ctx.router_of(
        num_workers=num_workers,
        actor_class=WorkerActor,
        router_class=router_class,
    )


def build_jobqueue(num_workers):
    return JobQueue(num_workers=num_workers, worker_class=ProcessQueueExecutor)
