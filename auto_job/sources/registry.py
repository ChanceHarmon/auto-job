from auto_job.sources.greenhouse import GreenhouseSource
from auto_job.sources.remoteok import RemoteOKSource
from auto_job.sources.rss import RSSSource

SOURCE_REGISTRY = {
    "remoteok": RemoteOKSource,
    "rss": RSSSource,
    "greenhouse": GreenhouseSource,
}