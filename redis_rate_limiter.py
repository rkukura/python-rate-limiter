import redis

class RedisRateLimiter(object):
    def __init__(self, host='localhost', port=6379, db=0, username=None, password=None):
        self._redis = redis.Redis(host, port, db, username, password)
        self._expire_periods = 5

    def limit_rate(self, id, period, tokens_per_period, tokens_required=1.0):
        """Return a tuple indicating whether a call requiring
        ``tokens_required`` tokens on resource ``id`` is allowed and
        the time at which this was determined. The rate limit for the
        resource is defined as ``tokens_per_period`` tokens available
        per ``period`` microseconds.
        """

        period = int(period)
        tokens_per_period = float(tokens_per_period)
        tokens_required = float(tokens_required)

        # Use a pipeline to buffer calls within atomic transactions
        # using optimistic locking.
        with self._redis.pipeline() as pipe:
            # Loop to retry if our Redis key is updated by someone
            # else during our transaction. REVISIT: Limit number of
            # attempts?
            while True:
                try:
                    # Before starting the transaction, watch our Redis
                    # key for updates.
                    pipe.watch(id)

                    # Get the current Redis hash fields for our key.
                    tokens, updated = pipe.hmget(id, 'tokens', 'updated')

                    # Get the current time from the Redis server. This
                    # costs a round trip but avoids requiring clock
                    # synchronization among nodes using the same rate
                    # limit id.
                    seconds, microseconds = pipe.time()
                    when = seconds * 1000000 + microseconds

                    # Determine how many tokens are available for this
                    # call.
                    if tokens is None or updated is None:
                        tokens_available = tokens_per_period
                    else:
                        accumulated_tokens = tokens_per_period * (when - int(updated)) / period
                        tokens_available = min(float(tokens) + accumulated_tokens, tokens_per_period)

                    # See if the call is allowed.
                    new_tokens = tokens_available - tokens_required
                    if new_tokens < 0.0:
                        # Reject the call.
                        return False, when

                    # Atomically update the Redis hash fields and set
                    # the expiration time.
                    pipe.multi()
                    pipe.hset(id, mapping={'tokens': new_tokens, 'updated': when})
                    pipe.pexpire(id, int(self._expire_periods * period / 1000))
                    pipe.execute()

                    # Allow the call.
                    return True, when

                except redis.WatchError:
                    # Someone else updated our Redis key or it expired
                    # during the transaction, so try again.
                    continue
