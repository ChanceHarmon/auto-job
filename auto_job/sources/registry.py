from auto_job.sources.greenhouse import GreenhouseSource
from auto_job.sources.remoteok import RemoteOKSource
from auto_job.sources.rss import RSSSource
from auto_job.sources.lever import LeverSource
from auto_job.sources.ashby import AshbySource


# The search pipeline uses this registry to turn source names from config.yaml
# into concrete source adapter classes.
SOURCE_REGISTRY = {
    "remoteok": RemoteOKSource,
    "rss": RSSSource,
    "greenhouse": GreenhouseSource,
    "lever": LeverSource,
    "ashby": AshbySource
}
