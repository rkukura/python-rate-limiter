# python-redis-rate-limiter
Python client for distributed rate limiting using Redis.

USAGE

The redis_rate_limiter.py module provides a simple rate limiting API
for distributd Python applications to use:

class RedisRateLimiter(object):
    def __init__(self, host='localhost', port=6379, db=0,
                 username=None, password=None):
        # …

    def allow_call(self, id, period, tokens_per_period,
                   tokens_required=1.0):
        # …

An application instantiates the RedisRateLimiter class passing the
parameter values required to connect to the Redis server. See the
redis-py documentation for details on the parameters. The default
parameter values will work for a local Redis deployment with the
default (unsecure) configuration for testing or development purposes,
but any production deployment requires non-default parameters. An
instance can be shared across threads within the application.

REVISIT: Parameters for TLS are also likely needed.

To determine whether a call should be allowed or denied due to a rate
limit, the application calls the allow_call() method of the
RedisRateLimiter instance. The following parameters control the rate
limiting algorithm:

id - A string identifying the resource for which the rate is being
limited. This typically is composed of something identifying the
resource type and something, such as an API key or source IP address,
identifying the client accessing the resource.

period - An integer specifying the time period over which the rate is
limited, in microseconds.

tokens_per_period - A float indicating how many tokens are available
for the resource during each period.

tokens_required - A float indicating how many tokens are required for
the call. The default is 1.0, but other values might be used depending
on the cost of the call.

The allow_call() method returns a tuple containing a boolean and an
integer. The boolean is True if the application call should be allowed
and False if it should be rejected due to the rate limit. The integer
indicates the time in microseconds since the Redis server’s epoch at
which the decision was made, which can be useful when logging the rate
limit decisions to validate that the rate limiter is operating as
expected.

All application replicas concurrently processing calls for a resource
should pass consistent values for period and tokens_per_period. But
these values can vary dynamically without causing significant problems
as long as there is minimal lag in replicas becoming consistent again.


TESTS

No unit tests currently exist.

The test_client.py module can be executed to exercise the
implementation. It requires a running Redis server.

To see the command line options, run:

python test_cleint.py -h

Assuming a Redis server is running locally with the default (unsecure)
configuration, an example test can be run with:

python test_client.py myresource:someclient 1000000 10 1 500 10000

This makes 500 calls to allow_call() with a delay of 10000
microseconds between calls, using a rate limit of 10 calls per 1000000
microseconds. It reports how many calls were attempted, allowed, and
rejected.

The --logfile option can be used to record the result of each call in
a file. Files generated by concurrent runs can be concatenated and
sorted on the timestamp field to see exactly which calls were allowed
and which were rejected, and at what times.


NOTES

This is just a proof-of-concept implementation, is not supported in
any way, and should not be used for any sort of production use case.
