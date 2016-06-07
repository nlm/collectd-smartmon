#!/usr/bin/env python
import re
import subprocess
import os
import time
import argparse
import sys


class SmartDevice(object):

    smartcmdfmt = ['sudo', 'smartctl', '-f', 'brief', '-A', '/dev/{dev}']

    def __init__(self, dev):
        self.dev = dev
        self.attrcmd = [x.format(dev=dev) for x in self.smartcmdfmt]

    def attributes(self):
        try:
            out = subprocess.check_output(self.attrcmd)
        except OSError as err:
            sys.exit('unable to run smartctl: {0}'.format(err))
        for line in out.split("\n"):
            res = re.match('(?P<id>\d+)\s+(?P<name>\w+)\s+'
                           '(?P<flags>[POSRCK-]{6})\s+'
                           '(?P<value>\d+)\s+(?P<worst>\d+)\s+'
                           '(?P<thres>\d+)\s+(?P<fail>[\w-]+)\s+'
                           '(?P<raw_value>\d+)', line)
            if not res:
                continue
            yield res.groupdict()


def check_dev(dev):
    if not os.path.exists('/dev/{0}'.format(dev)):
        raise argparse.ArgumentTypeError('/dev/{0} does not exists'.format(dev))
    return dev


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('DEV', nargs='+',
                        help='devices to check', type=check_dev)
    parser.add_argument('-H', '--hostname', type=str,
                        help='override hostname provided by collectd',
                        default=os.environ.get('COLLECTD_HOSTNAME'))
    parser.add_argument('-i', '--interval', type=int,
                        help='override interval provided by collectd',
                        default=int(float(os.environ.get('COLLECTD_INTERVAL', 300))))
    args = parser.parse_args()

    hostname = args.hostname or subprocess.check_output(['hostname', '-f']).strip()
    interval = max(args.interval, 5)
    while True:
        for dev in args.DEV:
            for attr in SmartDevice('sda').attributes():
                print('PUTVAL "{hostname}/smart-{dev}/absolute-{id}_{attr}"'
                      ' interval={interval} N:{value}'
                      .format(hostname=hostname, dev=dev, id=attr['id'],
                              attr=attr.get('name'), interval=interval,
                              value=attr['raw_value']))
        time.sleep(interval)


if __name__ == '__main__':
    main()
