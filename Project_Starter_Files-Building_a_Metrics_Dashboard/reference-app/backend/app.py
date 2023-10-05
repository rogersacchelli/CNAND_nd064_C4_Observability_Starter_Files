from flask import Flask, render_template, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory
from jaeger_client import Config
from flask_pymongo import PyMongo
from opentracing.ext import tags
from opentracing.propagation import Format
from os import getenv
import pymongo
import logging

JAEGER_HOST = getenv('JAEGER_HOST', 'localhost')


app = Flask(__name__)
metrics = PrometheusMetrics(app)

app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"

mongo = PyMongo(app)

def init_tracer(service):
    config = Config(
            {'sampler': {'type': 'const', 'param': 1},
                                'logging': True,
                                'local_agent':
                                # Also, provide a hostname of Jaeger instance to send traces to.
                                {'reporting_host': JAEGER_HOST}},
            service_name=service,
            validate=True,
            metrics_factory=PrometheusMetricsFactory(service_name_label=service),
    )
    tracer = config.initialize_tracer()
    # this call also sets opentracing.tracer
    return tracer

tracer = init_tracer('backend')

@app.route("/")
def homepage(): 
    return "Hello World"


@app.route("/api")
def my_api():
    with tracer.start_span('/api') as span:
        answer = "something"
        span.set_tag('api', answer)
    return jsonify(repsonse=answer)


@app.route("/star", methods=["POST"])
def add_star():
    with tracer.start_span('/star') as span:
        star = mongo.db.stars
        name = request.json["name"]
        distance = request.json["distance"]
        star_id = star.insert({"name": name, "distance": distance})
        new_star = star.find_one({"_id": star_id})
        output = {"name": new_star["name"], "distance": new_star["distance"]}
        span.set_tag('star', output)
    return jsonify({"result": output})

metrics.register_default(
    metrics.counter(
        'by_path_counter', 'Request count by request paths',
        labels={'path': lambda: request.path}
    )
)

if __name__ == "__main__":

    log_level = logging.DEBUG
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(asctime)s %(message)s', level=log_level)

    

    app.run(DEBUG_METRICS=True)

    tracer.close()