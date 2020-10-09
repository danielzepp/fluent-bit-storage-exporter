import requests
import os
import logging
import traceback

from flask import Flask, request

app = Flask(__name__)

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 5))
METRIC_NAME_PREFIX = 'fluentbit'
BYTE_KEY = ['mem_size', 'mem_limit', 'busy_size']
# https://github.com/fluent/fluent-bit/blob/f4c92edfea0af469a8215693798df75de8c6d90b/src/flb_utils.c#L514
FLUENT_BIT_SIZE_UNIT = ["b", "K", "M", "G", "T", "P", "E", "Z", "Y"]


@app.route("/health")
def health():
    return "healthy"


def convert_bytes(size, unit):
    for num, name in enumerate(FLUENT_BIT_SIZE_UNIT[1:], start=1):
        if name == unit:
            return size * (1000 ** num)
    return size


def resolve_value(name, value):
    result = int(value) if isinstance(value, bool) else value
    if name in BYTE_KEY:
        unit, size = result[-1], result[:-1]
        result = convert_bytes(float(size), unit)
    return result


def get_metric(name, help_text, label, data):
    metric_name = f"{METRIC_NAME_PREFIX}_{name}"
    label_string = ",".join([f'{k}="{v}"' for k, v in label.items()])
    metrics = "\n".join([f"{metric_name}{{{label_string}}} {value}" for value in data])
    return (
        f'# TYPE {metric_name} gauge\n'
        f'# HELP {help_text}\n'
        f'{metrics}'
    )


@app.route("/parse/<path:target>")
def parse(target):
    try:
        response = requests.get(f"http://{target}/api/v1/storage", timeout=REQUEST_TIMEOUT)
    except Exception:
        msg = "Can not get fluent-bit metrics"
        app.logger.error(f"{msg} from {target}")
        app.logger.debug(traceback.format_stack())
        return msg, 500
    json_data = response.json()

    if not json_data.get('storage_layer') or not json_data.get('input_chunks'):
        msg = "fluent-bit storage metrics not found"
        app.logger.error(f"{msg} from {target}")
        app.logger.debug(json_data)
        return msg, 400

    metrics = []
    for metric_postfix, value in json_data['storage_layer']['chunks'].items():
        metric = get_metric(f'storage_layer_chunks_{metric_postfix}', '',
                            {}, [value])
        metrics.append(metric)

    for input_chunk, chunk_data in json_data['input_chunks'].items():
        for data_type, chunk in chunk_data.items():
            for metric_postfix, value in chunk.items():
                value = resolve_value(metric_postfix, value)
                metric = get_metric(f'input_chunks_{data_type}_{metric_postfix}', '',
                                    {"chunk": input_chunk}, [value])
                metrics.append(metric)
    return "\n".join(metrics)
