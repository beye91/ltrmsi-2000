#!/usr/bin/python

## import modules used here
import sys
import time
import subprocess
from subprocess import Popen,PIPE
import os
import re
import socket, paramiko, datetime, getpass
import itertools

bia_list = []
name_list = []
ip_list = []
int_list = []
bia_mac_list = []
pid_list = []
docker_net_list = []
docker_if_net_list = []
docker_if_final_list = []
i_pos = [2, 5, 8, 11, 14]


## Router IP Address
NET = "198.18.1."


## Add all the Links where L2 is required in the following format:
## "name1": "docker-router-name-A", "rtr1": "IP-last-Octet-A", "int1": "Interface-A", "name2": "docker-router-name-B", "rtr2": "IP-last-Octet-B", "int2": "Interface-B"

links = [
{
		"name1": "xr-9", "rtr1": "10", "int1": "1", "name2": "xr-12", "rtr2": "13", "int2": "1",
	},
	{
		"name1": "xr-9", "rtr1": "10", "int1": "4", "name2": "xr-12","rtr2": "13", "int2": "4",
	},
	{
		"name1": "xr-10", "rtr1": "11", "int1": "3", "name2": "xr-12","rtr2": "13", "int2": "0",
	},
	{
		"name1": "xr-10", "rtr1": "11", "int1": "5", "name2": "xr-12","rtr2": "13", "int2": "5",
	},
	{
		"name1": "xr-18", "rtr1": "19", "int1": "1", "name2": "xr-21","rtr2": "22", "int2": "1",
	},
	{
		"name1": "xr-18", "rtr1": "19", "int1": "4", "name2": "xr-21","rtr2": "22", "int2": "4",
	},
	{
		"name1": "xr-19", "rtr1": "20", "int1": "3", "name2": "xr-21","rtr2": "22", "int2": "0",
	},
	{
		"name1": "xr-19", "rtr1": "20", "int1": "5", "name2": "xr-21","rtr2": "22", "int2": "5",
	},
	{
		"name1": "xr-19", "rtr1": "20", "int1": "1", "name2": "xr-22","rtr2": "23", "int2": "1",
	}
]

for i in links:
	name1 = i["name1"]
	ip1 = i["rtr1"]
	int1 = i["int1"]
	name2 = i["name2"]
	ip2 = i["rtr2"]
	int2 = i["int2"]
	name_list.extend((name1, name2))
	ip_list.extend((ip1, ip2))
	int_list.extend((int1, int2))

## SSH into router and run cli commands
	
	for ip, int in zip(ip_list, int_list):
	    try:
	        remote_conn_pre = paramiko.SSHClient()
	        remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	        remote_conn_pre.connect(NET+ip, username="cisco", password="cisco123", look_for_keys=False, allow_agent=False)
	        remote_conn = remote_conn_pre.invoke_shell()
	    except:
	        time.sleep(30)
	        continue
	    time.sleep(5)
	    output = remote_conn.recv(64000)
	    stdin, stdout, stderr = remote_conn_pre.exec_command('''run show_interface "-i" "GigabitEthernet0_0_0_''' + str(int) + '''" | grep bia | awk  '{print $6}'\n''')
	    bia = stdout.read()
	    bia = bia.decode().split()
	    bia = [element.replace(".", "") for element in bia]
	    bia_list.append(bia[-1])
	    #print(NET+ip)
	    #print("GigabitEthernet0_0_0_", int)
	    #print(bia)
	    time.sleep(2)
	#print(bia_list)
	remote_conn.close()


## Insert the char ":" into mac address so easier to grep for later in the script
	for s in bia_list:
	    for i in i_pos:
	        s = s[:i] + ":" + s[i:]
	    bia_mac_list.append(s)

	#print(bia_mac_list)

	## Get the Process ID List
	for name in name_list:
	    command = '''docker inspect --format "{{.State.Pid}}" ''' + str(name)
	    pid = subprocess.check_output(command, shell=True)
	    pid = pid.decode().strip()
	    pid_list.append(pid)
	#print (str(pid_list))

	## Use process ID and get the Network and mac details
	for pid_id, i in zip(pid_list, bia_mac_list):
	    command = """sudo nsenter -t """ + str(pid_id) + """ -n ip link  | awk '(/link\/ether/) || (/xr/) {print $2}'"""
	    docker_net = subprocess.check_output(command, shell=True)
	    docker_net = docker_net.decode().split('\n')
	    try:
	        index = docker_net.index(i)
	        #print(index)
	    except:
	        pass
	    docker_if_net = docker_net[index-1]
	    docker_if_net_list.append(docker_if_net)

	#print(docker_if_net_list)

	docker_temp_list = list(set(docker_if_net_list))
	for i in docker_temp_list:
	    temp = re.sub(r"^xr-\d+@|:$", "", i)
	    docker_if_final_list.append(temp)
	#print(docker_if_final_list)

	## Execute the Actual commands to stitch the 2 Bridge interfaces together
	subprocess.run('sudo tc qdisc add dev ' + str(docker_if_final_list[0]) + ' handle ffff: ingress', shell=True)
	subprocess.run('sudo tc qdisc add dev ' + str(docker_if_final_list[1]) + ' handle ffff: ingress', shell=True)
	subprocess.run('sudo tc filter add dev ' + str(docker_if_final_list[0]) + ' parent ffff: u32 match u32 0 0 action mirred egress redirect dev ' + str(docker_if_final_list[1]), shell=True)
	subprocess.run('sudo tc filter add dev ' + str(docker_if_final_list[1]) + ' parent ffff: u32 match u32 0 0 action mirred egress redirect dev ' + str(docker_if_final_list[0]), shell=True)


	## Use the print commands to verify if the script works:
	print("These following lines are what was configured")
	print("sudo tc qdisc add dev "+ str(docker_if_final_list[0]) + " handle ffff: ingress")
	print("sudo tc qdisc add dev "+ str(docker_if_final_list[1]) + " handle ffff: ingress")
	print("sudo tc filter add dev "+ str(docker_if_final_list[0]) + " parent ffff: u32 match u32 0 0 action mirred egress redirect dev " + str(docker_if_final_list[1]))
	print("sudo tc filter add dev "+ str(docker_if_final_list[1]) + " parent ffff: u32 match u32 0 0 action mirred egress redirect dev " + str(docker_if_final_list[0]))
	name_list = []
	ip_list = []
	int_list = []
	bia_list = []
	bia_mac_list = []
	pid_list = []
	docker_net_list = []
	docker_if_net_list = []
	docker_if_final_list = []
	time.sleep(2)


