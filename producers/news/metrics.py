 
import time
from collections import defaultdict
 
 
class NewsMetrics:
 
    def __init__(self):
        self.counters = defaultdict(int)
        self.start_time = time.time()
 
    def increment(self, metric, amount=1):
        self.counters[metric] += amount
 
    def record_feed_fetch(self, source, duration, status):
        self.increment("feeds_fetched")
 
        if status == "success":
            self.increment("feeds_success")
        else:
            self.increment("feeds_failed")
 
        print(
            f"[FEED] {source} | "
            f"Status: {status} | "
            f"Duration: {duration:.2f}s"
        )
 
    def report(self):
        print("\n========== FINTEL NEWS METRICS ==========")
 
        for metric, value in sorted(self.counters.items()):
            print(f"{metric}: {value}")
 
        print(f"Uptime: {time.time() - self.start_time:.2f}s")
        print("=========================================\n")
 