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


def dev_exists(dev):
    return os.path.exists('/dev/{0}'.format(dev))

def get_filelist(dirname, pattern):
    return [f for f in os.listdir(dirname) if re.match(pattern, f)]

def expand_devices(devlist):
    expanded_devlist = []
    for dev in devlist:
        if dev == 'autodetect':
            expanded_devlist.extend(get_filelist('/dev', r'^sd[a-z]+$'))
        else:
            expanded_devlist.append(dev)
    return sorted(list(set(expanded_devlist)))

def smartmon_loop(devices, hostname, interval):
    while True:
        for dev in devices:
            if dev_exists(dev):
                for attr in SmartDevice(dev).attributes():
                    print('PUTVAL "{hostname}/smart-{dev}'
                          '/absolute-{id}_{attr}"'
                          ' interval={interval} N:{value}'
                          .format(hostname=hostname, dev=dev, id=attr['id'],
                                  attr=attr.get('name'), interval=interval,
                                  value=attr['raw_value']))
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dev', nargs='*',
                        help='devices to check (default: autodetect)')
    parser.add_argument('-H', '--hostname', type=str,
                        help='override hostname provided by collectd',
                        default=os.environ.get('COLLECTD_HOSTNAME'))
    parser.add_argument('-i', '--interval', type=int,
                        help='override interval provided by collectd',
                        default=int(float(os.environ.get('COLLECTD_INTERVAL', 300))))
    parser.add_argument('-c', '--dont-check-devs',
                        action='store_true', default=False,
                        help='do not check devices existence at startup')
    args = parser.parse_args()

    hostname = (args.hostname
                or subprocess.check_output(['hostname', '-f']).strip())
    if len(hostname) == 0:
        parser.error('unable to detect hostname')
    interval = max(args.interval, 5)
    if len(args.dev) == 0:
        devices = expand_devices(['autodetect'])
    else:
        devices = expand_devices(args.dev)

    if not args.dont_check_devs:
        for dev in devices:
            if not dev_exists(dev):
                parser.error('device "/dev/{0}" does not exist'.format(dev))

    try:
        smartmon_loop(devices, hostname, interval)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
