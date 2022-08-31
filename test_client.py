import redis_rate_limiter as rrl

import os
import time

def run_test(id, period, tokens_per_period, tokens_required, calls, delay, log=None, host='localhost', port=6379, db=0, username=None, password=None):
    """The period and delay areguments are in microseconds.
    """

    rl = rrl.RedisRateLimiter(host=args.host, port=args.port, db=args.db, username=args.username, password=args.password)

    calls_allowed = 0
    calls_rejected = 0
    sleep_time = float(delay) / 1000000
    pid = str(os.getpid())

    for x in range(calls):
        result, when = rl.allow_call(id, period, tokens_per_period, tokens_required)
        if result:
            calls_allowed = calls_allowed + 1
        else:
            calls_rejected = calls_rejected + 1
        if log:
            log.write(pid + ' ' + id + ' ' + str(when) + ' ' + str(result) + '\n')

        time.sleep(sleep_time)

    return calls_allowed, calls_rejected

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost', help='redis hostname')
    parser.add_argument('--port', type=int, default=6379, help='redis port')
    parser.add_argument('--db', type=int, default=0, help='redis DB')
    parser.add_argument('--username', default=None, help='redis username')
    parser.add_argument('--password', default=None, help='redis password')
    parser.add_argument('--logfile', default=None, help='file in which to log result of each call')
    parser.add_argument('id', help='string identifying the resource being rate limited')
    parser.add_argument('period', help='rate limit period in microseconds')
    parser.add_argument('tokens_per_period', help='tokens accumulated per period')
    parser.add_argument('tokens_required', help='tokens required each call')
    parser.add_argument('calls', help='number of calls to attempt')
    parser.add_argument('delay', help='delay between calls in microseconds')
    args = parser.parse_args()

    log = None
    if args.logfile:
        log = open(args.logfile, 'w')

    allowed, rejected = run_test(args.id, int(args.period), int(args.tokens_per_period), int(args.tokens_required), int(args.calls), int(args.delay), log, args.host, args.port, args.db, args.username, args.password)

    if log:
        log.close()

    print("out of " + str(args.calls) + " calls attempted, " + str(allowed) + " were allowed and " + str(rejected) + " were rejected")
