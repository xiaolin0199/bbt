#!/usr/bin/env python
# coding=utf-8

from netaddr import IPSet, IPAddress, IPNetwork, IPRange
from collections import Iterable


def generate_ips(cidr, ip_start, count=1, pools=None, gateway_ip=None, exclude=None):
    """生成 IP 地址列表

    :param cidr: string, 子网 CIDR, eg:'10.1.33.0/24'
    :param ip_start: string, 生成 IP 列表的起始 IP, eg:'10.1.33.240'
    :param count: interger, 生成 IP 的个数
    :param pools: list, IP 池, eg:[{'start': "10.1.33.240", 'end': "10.1.33.250"}]
    :param gateway_ip: string, 网关 IP, eg:'10.1.33.1'
    :param exclude: Iterable object, 排除的 IP, eg:["10.1.33.242", "10.1.33.246"]
    :return: IP 地址列表.返回 None 表示 ip_start 不在 CIDR 网段或者 IP 池内, 或者被排除了
    """
    ip = IPNetwork(cidr)
    ipset = IPSet()
    ipset.add(ip)
    ip_start = IPAddress(ip_start)

    if isinstance(pools, list):
        pool_set = IPSet()
        for p in pools:
            pool_set.add(IPRange(p['start'], p['end']))
        ipset &= pool_set

    implicit_exclude = IPSet()
    implicit_exclude.add(ip.network)
    implicit_exclude.add(ip.broadcast)
    if gateway_ip:
        implicit_exclude.add(IPAddress(gateway_ip))

    if isinstance(exclude, Iterable):
        exclude = [IPAddress(i) for i in exclude if i]
        exclude = IPSet(exclude)
        exclude |= implicit_exclude
    else:
        exclude = implicit_exclude

    if ip_start not in ipset or ip_start in exclude:
        return None
    else:
        ip_list = sorted(list(ipset))
        ip_list = ip_list[ip_list.index(ip_start):]
        ipset = IPSet(ip_list)

    ipset -= exclude
    ip_list = sorted(list(ipset))
    ip_list = ip_list[:count]
    ips = [str(i) for i in ip_list]
    return ips


def main():
    cidr = '10.1.33.0/23'
    ip_start = '10.1.32.253'
    count = 10
    exclude = ['10.1.32.254', '10.1.33.2', None, '']
    pools = [{'start': "10.1.32.240", 'end': "10.1.33.50"},
             {'start': "10.1.33.100", 'end': "10.1.33.200"}]
    print(generate_ips(cidr, ip_start, count=count, pools=pools, exclude=exclude))
    print(generate_ips(cidr, ip_start, count=count, pools=pools, gateway_ip='10.1.33.4'))

if __name__ == '__main__':
    main()
