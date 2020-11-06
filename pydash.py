#!flask/bin/python
#  -*- coding: UTF-8 -*-
import psutil
import os
import datetime
import platform
import humanfriendly
import time
import netifaces
from flask import Flask

app = Flask(__name__)

def sectotime(time):
        mm, ss = divmod(time, 60)
        hh, mm = divmod(mm, 60)
        return "{}:{}:{}".format(hh, mm, ss)

@app.route('/')
def index():
        return "Hello World!"

def date():
        now = datetime.datetime.now()
        today = datetime.datetime.ctime(now)
        return today
@app.route('/home')
def home():
        return {
        'date' : date()
        }

@app.route('/cpu')
def cpu_info():
        return {
        'CPU num' : psutil.cpu_count(),
        'CPU time' : psutil.cpu_times(),
        'Load Avg' : psutil.getloadavg(),
        'CPU Percentage' : psutil.cpu_percent(),
        'CPU times information of each CPU' : psutil.cpu_times_percent(percpu=True)
        }

@app.route('/sysinfo')
def user_info():
        user_inf = psutil.users()
        first_user = user_inf[0]
        return {
        "System" : platform.system(),
        "OS" : platform.platform(),
        "Python Version" : platform.python_version(),
        "User name" : first_user.name,
        "Terminal" : first_user.terminal,
        "Hostname" : first_user.host,
        "Machine" : platform.machine(),
        "Start Time" : datetime.datetime.fromtimestamp(first_user.started),
        "Uptime" :  sectotime(int(time.time() - psutil.boot_time()))
        }

@app.route('/ssh')
def ssh_list():
        pipe = os.popen("ss | grep -i ssh | awk '{print $5, $6}'")
        data = pipe.read().strip().split('\n')
        pipe.close()
        if data == []:
            return "SSH baglantisi yok."
        else:
                usage = [i.split(None,1) for i in data]
                for element in usage:
                        local_add = element[0]
                        peer_add = element [1]
                        return {
                                "Local Address:Port" : local_add,
                                "Peer Address:Port" : peer_add
                        }
@app.route('/process')
def process_list():
        proc_list = []
        for proc in psutil.process_iter():
                proc_info = proc.as_dict(attrs=['pid', 'name', 'username'])
                proc_list.append(proc_info)
        return {
                "Process List" : proc_list
        }

@app.route('/process/zombie')
def zombie():
        i = 0
        pids = []
        proces = []
        totalcpu = 0
        for proc in psutil.process_iter(attrs=['pid']):
                pids.append(proc.pid)
        for x in pids:
                p = psutil.Process(x)
                cpu = psutil.Process(x).cpu_percent(interval=None)
                totalcpu = totalcpu + cpu
                if(p.status() == psutil.STATUS_ZOMBIE):
                        proces = p.name()
                        return {
                                "Zombie Process name" : process
                        }
        if proces == []:
                return "There is no zombie process."
@app.route('/process/jobs')
def jobs():
        jobs = []
        pipe = os.popen("systemctl list-jobs")
        jobs = pipe.read()
        pipe.close()
        if jobs == []:
                return "No jobs runnning!"
        else:
                return jobs
@app.route('/services')
def service():
        count1 = 0
        count2 = 0
        count3 = 0
        pipe1 = os.popen("systemctl list-unit-files --type service | grep disabled | awk '{print $1}'")
        disabled = pipe1.read()
        pipe1.close()
        pipe2 = os.popen("systemctl list-unit-files --type service| grep enabled | awk '{print $1}'")
        enabled = pipe2.read()
        pipe2.close()
        pipe3 = os.popen("systemctl list-unit-files --type service | grep static | awk '{print $1}'")
        static = pipe3.read()
        pipe3.close()
        return {
        "Disabled Service Num" : len(disabled),
        "Disabled" : disabled,
        "Enabled Service Num" : len(enabled),
        "Enabled" : enabled,
        "Static Service Num" : len(static),
        "Static" : static
}

def disk_usage():
        diskusage = psutil.disk_usage('/').percent
        if diskusage > 90:
                return '{}  Warning! Your disk is almost full'.format(diskusage)
        else:
                return diskusage
@app.route('/disk')
def disk_info():
        disks = []
        for i in psutil.disk_partitions(all=True):
                disk_info = psutil.disk_usage(i.mountpoint)
                disk = {
                        'Device' : i.device,
                        'Mountpoint' : i.mountpoint,
                        'Total Space' : humanfriendly.format_size(disk_info.total),
                        'Usage Space' : humanfriendly.format_size(disk_info.used),
                        'Free Space' : humanfriendly.format_size(disk_info.free)
                        }
                disks.append(disk)
        return {
        "Disks" : disks,
        "Total Disk Usage Percentage" : disk_usage()
        }

@app.route('/memory')
def memory():
        swap = psutil.virtual_memory()
        return {
                'Total Memory' : humanfriendly.format_size(swap.total),
                'Available Memory' : humanfriendly.format_size(swap.available),
                'Memory Percentage' : swap.percent
                }

def get_battery_plugge():
        plugge = psutil.sensors_battery().power_plugged
        if plugge == "true":
                plugged = "Battery is plugged to power."
        else:
                plugged = "Battery is not plugged to power."
        return plugged

def get_battery_percent():
        percent = psutil.sensors_battery().percent
        if percent == 100:
                return percent, "Battery is Full."
        elif percent <=20:
                return percent, "You should charge the Battery."
        else:
                return percent

@app.route('/battery')
def get_battery():
        return {
        "Power Plugged" : get_battery_plugge(),
        "Battery Percent" : get_battery_percent(),
        "Time Left" : sectotime(psutil.sensors_battery().secsleft)
        }

def get_netstat():
        pipe = os.popen("sudo netstat -nlpt | grep LISTEN | awk '{print $4, $7}'")
        data = pipe.read().strip().split('\n')
        pipe.close()
        data = [i.split(None,1) for i in data]
        return data
@app.route('/network')
def get_network_info():
        interface_list = []
        interfaces = netifaces.interfaces()
        for i in interfaces:
                inet = netifaces.ifaddresses(i)[netifaces.AF_INET]
                for x in inet:
                        ipaddress = (x['addr'])
                        netmask = (x['netmask'])
                        interfaces_list ={
                                "interface" : i,
                                "ip address" : ipaddress,
                                "netmask" : netmask,
                        }
                        interface_list.append(interfaces_list)
        return {
        "Interfaces" : interface_list,
        "Programs IP and PID" : get_netstat()
        }


if __name__ == '__main__':
        app.run(debug=True)

