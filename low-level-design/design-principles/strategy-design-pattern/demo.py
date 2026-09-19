from cache import Cache, make_policy

WORKLOADS = {
    "hot keys, then a scan": list("AABBAB") + list("CDEFGH") + list("ABAB"),
    "popular set changes": list("XYXYXYXY") + list("PQR") * 4,
    "one favourite among newcomers": list("ABC") + list("ADAEAFAGAHA"),
}
POLICY_NAMES = ["fifo", "lru", "lfu"]


def hit_rate(policy_name: str, keys: list[str]) -> float:
    cache = Cache[str, int](capacity=3, policy=make_policy(policy_name))
    for key in keys:  # the classic cache-aside loop: read, and store on a miss
        if cache.get(key) is None:
            cache.put(key, 1)
    return cache.stats.hit_rate


def compare_policies() -> None:
    print("Hit rate for a cache of 3 entries")
    print(f"{'workload':<32}" + "".join(f"{name.upper():>8}" for name in POLICY_NAMES))
    for workload, keys in WORKLOADS.items():
        rates = "".join(f"{hit_rate(name, keys):>8.0%}" for name in POLICY_NAMES)
        print(f"{workload:<32}{rates}")


def weigh_by_size() -> None:
    # A stateless strategy is just a function: here, "an entry costs its text length".
    notes = Cache[str, str](
        capacity=10, policy=make_policy("lru"), weigher=lambda k, v: len(v)
    )
    notes.put("a", "hello")  # weighs 5
    notes.put("b", "world")  # weighs 5, so the cache is full
    notes.put("c", "hi")  # weighs 2, so the least recently used entry goes
    kept = [key for key in "abc" if key in notes]
    print(f"weigher: kept {kept}, weight used {notes.used} of 10")


def swap_strategy_at_run_time() -> None:
    cache = Cache[str, int](capacity=3, policy=make_policy("lru"))
    for key in "ABC":
        cache.put(key, 1)
    cache.get("A")  # under LRU, B is now the least recently used
    cache.set_policy(make_policy("fifo"))  # history restarts in storage order: A, B, C
    cache.put("D", 1)
    evicted = [key for key in "ABC" if key not in cache]
    print(f"swap: after switching to FIFO, evicted {evicted}")


if __name__ == "__main__":
    compare_policies()
    weigh_by_size()
    swap_strategy_at_run_time()
