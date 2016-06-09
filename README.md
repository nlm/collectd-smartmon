collectd-smartmon
=================
a tool to report smart attributes raw values from collectd

requirements
------------

- python
- smartmontools
- sudo

install
-------

clone repo and copy script:

    git clone https://github.com/nlm/collectd-smartmon.git
    cd collectd-smartmon
    cp collectd-smartmon.py /usr/local/bin

add new system user for privilege separation:

    useradd -r collectd-smartmon

add to sudoers file:

    collectd-smartmon  ALL = (ALL) NOPASSWD: /usr/sbin/smartctl -f brief -A /dev/sd[a-z]

add snippet to collectd config file:

    LoadPlugin exec
    <Plugin exec>
      Exec "collectd-smartmon" "/usr/local/bin/collectd-smartmon.py" "sda" "sdb" "sdc" "sdd"
    </Plugin>

restart collectd
