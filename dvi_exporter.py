#!/usr/bin/env python
""" DVI API exporter """

import json
import sys
import argparse
import time
from datetime import datetime
import requests
import prometheus_client
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY


class DVICollector:
    """ Class for collecting and exporting DVI heatpump metrics """

    base_url = 'https://ws.dvienergi.com/API/'

    def __init__(self, args):
        """Construct the object and parse the arguments."""
        self.args = self._parse_args(args)

        self.payload = self.create_payload(self.args)

    @staticmethod
    def _parse_args(args):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-l',
            '--listen',
            dest='listen',
            default='0.0.0.0:9555',
            help='Listen host:port, i.e. 0.0.0.0:9417'
        )
        parser.add_argument(
            '-u',
            '--username',
            required=True,
            dest='username',
            help='Username usually an email address'
        )
        parser.add_argument(
            '-p',
            '--password',
            required=True,
            dest='password',
            help='password for the self-service portal'
        )
        parser.add_argument(
            '-d',
            '--device',
            required=True,
            dest='device',
            help='device id of the heatpump like 15xxxx'
        )
        arguments = parser.parse_args(args)
        return arguments

    def create_payload(self, args):

        payload = {
            "usermail": args.username,
            "userpassword": args.password,
            "fabnr": args.device,
            "get": {
              "bestgreen": 1,
              "sensor": 1,
              "relay": 1,
              "timer": 1,
              "userSettings": 1
            }
        }

        return payload

    def api_read_request(self):
        """ Make API request with payload """

        try:
            api_r = requests.post(self.base_url, data=json.dumps(self.payload), timeout=(5, 30))
            response = api_r.json()
        except Exception as err:
            print(f'API request failed or invalid response ({err})')
            return None

        return response

    def convert_data_type(self, value, convert, convert_format):

        if convert == 'timestamp':
            ts = datetime.strptime(value, convert_format)
            return ts.strftime('%s')

    def validate_response(self, data):
        """ Validate data received """

        if not isinstance(data, dict):
            raise RuntimeError('Resonse data type invalid')

        access = data.get('Access', False)
        if access != 'Granted':
            print(f'Access not granted ({access})')
            raise RuntimeError('Acess denied')

        if 'output' not in data:
            raise RuntimeError('Output not found in response')

        if 'bestgreen' not in data.get('output', False):
            raise RuntimeError('bestgreen not found in output')

        if 'Sensor.Date' not in data['output'].get('bestgreen', False):
            raise RuntimeError('Sensor.Date not found in bestgreen')

        print(f"Last data from {data['output']['bestgreen']['Sensor.Date']}")
        return True

    def parse_output_mapping(self):
        """ Read file with expected metrics based on API response """

        with open('./output_mapping.json', 'r', encoding='utf-8') as mapping_fp:
            mapping = json.load(mapping_fp)

        return mapping

    def collect(self):
        """ Create dynamic list of metrics base on mapping file """
        data = self.api_read_request()

        if not data or not self.validate_response(data):
            return

        for cat, metrics in self.parse_output_mapping().items():
            for metric, info in metrics.items():

                try:
                    if 'convert' in info:
                        value = self.convert_data_type(
                            data['output'][cat][metric],
                            info['convert'],
                            info['convert_format'])
                    else:
                        value = data['output'][cat][metric]
                except Exception as err:
                    print(f'Unable to convert og get value ({err}) - skipping')
                    continue

                if info['type'] == 'counter':
                    counter = CounterMetricFamily(info['name'], info['description'])
                    counter.add_metric(labels=['foo'], value=value)
                    yield counter

                elif info['type'] in ['gauge', 'enum']:
                    gauge = GaugeMetricFamily(info['name'], info['description'])
                    gauge.add_metric(labels=['bar'], value=value)
                    yield gauge

                else:
                    print(f"Unknown type at {cat} {info['name']}")
                    continue


def run():
    """ Run the main loop """

    collector = DVICollector(sys.argv[1:])
    args = collector.args

    REGISTRY.register(collector)

    (ip_addr, port) = args.listen.split(':')
    print(f'Starting listener on {ip_addr}:{port}')
    prometheus_client.start_http_server(port=int(port),
                                        addr=ip_addr)
    print('Starting main loop')
    while True:
        time.sleep(15)


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Caught keyboard interrupt - exiting')
    except Exception as main_err:
        print(f'Caught unknown exception ({main_err})')
        raise
