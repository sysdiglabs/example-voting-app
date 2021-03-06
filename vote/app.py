from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import statsd
import time

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()
statsdclient = statsd.StatsClient('localhost', 8125)
vote_votes_count = 0

app = Flask(__name__)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    global vote_votes_count
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    methodtimer = statsdclient.timer('response_time')
    methodtimer.start()
    vote = None

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        if vote == "a":
		statsdclient.incr('cats')
        else:
		statsdclient.incr('dogs')
        vote_votes_count += 1
        statsdclient.gauge('vote_votes_count', vote_votes_count)
        data = json.dumps({'voter_id': voter_id, 'vote': vote})
        redis.rpush('votes', data)

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    statsdclient.incr('votes')
    methodtimer.stop()
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
