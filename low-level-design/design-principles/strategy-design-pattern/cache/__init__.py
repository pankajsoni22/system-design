from .cache import Cache, CacheStats, one_per_entry
from .policies import FifoPolicy, LfuPolicy, LruPolicy, UnknownPolicyError, make_policy
from .policy import EvictionPolicy

__all__ = [
    "Cache",
    "CacheStats",
    "EvictionPolicy",
    "FifoPolicy",
    "LfuPolicy",
    "LruPolicy",
    "UnknownPolicyError",
    "make_policy",
    "one_per_entry",
]
