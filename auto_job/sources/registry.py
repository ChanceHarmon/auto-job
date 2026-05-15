from auto_job.sources.greenhouse import GreenhouseSource
from auto_job.sources.remoteok import RemoteOKSource
from auto_job.sources.rss import RSSSource
from auto_job.sources.lever import LeverSource

SOURCE_REGISTRY = {
    "remoteok": RemoteOKSource,
    "rss": RSSSource,
    "greenhouse": GreenhouseSource,
    "lever": LeverSource
}