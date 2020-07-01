###### BULK Adding VLANs to VMWare ESXi, Cisco UCSM, assign to VLAN Group at ucsm AND a Cisco Switch
###### VLANs created at Switch and ESXi are named the same. at UCSM with generic name. 
###### UCSM VLAN Group can be added to LAN Config for vmnetwork

# IMPORTANT - Before using, check and apply FI CLI Prompt in UCSM Part (around line 155)
import os
import getpass
import sys
import datetime
import time
import argparse
from netmiko import Netmiko
############################# ARG PARSE #############################

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--start', help='first VLAN ID', required=True)
parser.add_argument('-e', '--end', help='last VLAN ID', required=True)
parser.add_argument('-n', '--labuser', help='Used to derive the port group and vlan name (lab-xxxxxxx_<VLANID>)', required=True)
parser.add_argument('-U', '--ucsmonly', action='store_true', default=False, help='Changes config on UCS Manager only')
parser.add_argument('-H', '--hypervisoronly', action='store_true', default=False, help='Changes config on ESXi Servers only')
parser.add_argument('-N', '--networkingonly', action='store_true', default=False, help='Changes config on Switch only')
args = parser.parse_args() 

############################# Preparing #############################
passwordesxi="dummy"
passwordcisco="dummy"
passworducsm="dummy"
v_mode="none"

############################# ENV ARGS #############################

# Hosts
v_ip_esxi1="172.31.255.251"
v_ip_esxi2="172.31.255.251"
v_ip_esxi3="172.31.255.251"
v_ip_esxi4="172.31.255.251"
v_ip_coreswitch="172.31.255.251"
v_ip_ucsmfi="172.31.255.251"

# VLAN Group to assign to Server Profile
v_ucs_vmnetworkgrp="grp-vmnetworks"


if args.ucsmonly:
    v_mode="ucsm"
    print("OK - Running Mode is: "+v_mode)
    passworducsm = getpass.getpass(prompt='Password for UCSM: ')
if args.hypervisoronly:
    v_mode="hypervisor"
    print("OK - Running Mode is: "+v_mode)
    passwordesxi = getpass.getpass(prompt='Password for ESXi: ')
if args.networkingonly:
    v_mode="networking"
    print("OK - Running Mode is: "+v_mode)
    passwordcisco = getpass.getpass(prompt='Password for coreswitch: ')

if not args.ucsmonly and not args.hypervisoronly and not args.networkingonly:
    v_mode="all"
    print("OK - Running Mode is: "+v_mode)
    passwordcisco = getpass.getpass(prompt='Password for coreswitch: ')
    passwordesxi = getpass.getpass(prompt='Password for ESXi: ')
    passworducsm = getpass.getpass(prompt='Password for UCSM: ')

################################# SSH Hosts #################################
esxi1 = {
    "host": v_ip_esxi1,
    "username": "root",
    "password": passwordesxi,
    "device_type": "autodetect",
    "session_log": "sessionlog_esxi1.log",
    'global_delay_factor': 0.05
}

esxi2 = {
    "host": v_ip_esxi2,
    "username": "root",
    "password": passwordesxi,
    "device_type": "autodetect",
    "session_log": "sessionlog_esxi2.log",
    'global_delay_factor': 0.05
}

esxi3 = {
    "host": v_ip_esxi3,
    "username": "root",
    "password": passwordesxi,
    "device_type": "autodetect",
    "session_log": "sessionlog_esxi3.log",
    'global_delay_factor': 0.05
}

esxi4 = {
    "host": v_ip_esxi4,
    "username": "root",
    "password": passwordesxi,
    "device_type": "autodetect",
    "session_log": "sessionlog_esxi4.log",
    'global_delay_factor': 0.05
}

coreswitch = {
    "host": v_ip_coreswitch,
    "username": "admin",
    "password": passwordcisco,
    "device_type": "cisco_ios",
    "session_log": "sessionlog_coreswitch.log",
    'global_delay_factor': 0.2
}
ucsm = {
    "host": v_ip_ucsmfi,
    "username": "admin",
    "password": passworducsm,
    "device_type": "cisco_nxos",
    "session_log": "sessionlog_ucsm.log",
    'global_delay_factor': 0.2
}

v_idstart=int(args.start)
v_idend=int(args.end)
v_networkname="lab_"+args.labuser+"_"

######################################### DO NOT CHANGE ##########################################
###################################### WORK on Hypervisor ########################################
if v_mode=='all' or v_mode=="hypervisor":
    v_allservers = [esxi1, esxi2, esxi3, esxi4]
    for devices in v_allservers:
        # reset v_id
        v_id=v_idstart
        net_connect = Netmiko(**devices)
        while v_id<=v_idend:
            command1="esxcfg-vswitch --add-pg="+v_networkname+str(v_id)+" vswitch-hx-vm-network"
            command2="esxcfg-vswitch -v "+str(v_id)+" -p "+v_networkname+str(v_id)+" vswitch-hx-vm-network"
            output = net_connect.send_command_timing(command1)         
            output = net_connect.send_command_timing(command2)
            v_id=v_id+1

    net_connect.disconnect()

########################################## WORK on coreswitch ######################################
if v_mode=="all" or v_mode=="networking":
    net_connect = Netmiko(**coreswitch)
    # reset v_id
    v_id=v_idstart
    command1="conf t"
    output = net_connect.send_command_timing(command1)
    while v_id<=v_idend:
        command2="vlan "+str(v_id)
        command3="name "+v_networkname+str(v_id)
        output = net_connect.send_command_timing(command2)
        output = net_connect.send_command_timing(command3)
        v_id=v_id+1

    command4="end"
    command5="wr"
    output = net_connect.send_command_timing(command4)
    output = net_connect.send_command_timing(command5)
    net_connect.disconnect()


########################################## WORK on FabricInterconnect ######################################
if v_mode=="all" or v_mode=="ucsm":
    net_connect = Netmiko(**ucsm)
    # reset v_id
    v_id=v_idstart
    commandexit="exit"
    command1="scope eth-uplink"
    output = net_connect.send_command_timing(command1)
    while v_id<=v_idend:
        with open('sessionlog_ucsm.log') as myfile:
            if "hx-ucs-A /eth-uplink #" or "hx-ucs-A /eth-uplink* #" in list(myfile)[-1]:
                command2="create vlan vlan_lab"+str(v_id)+" "+str(v_id)
                output = net_connect.send_command_timing(command2)
            else:
                sys.exit("Got odd answer! Check sessionlog!")
        with open('sessionlog_ucsm.log') as myfile:
            if "Error: Managed object already exists" in list(myfile)[-2]:
                print("VLAN "+str(v_id)+" already Exists!")
            else:
                output = net_connect.send_command_timing(commandexit)
                continue
        v_id=v_id+1
#                if "Invalid Command at" in list(myfile)[-1]:
#                net_connect.disconnect()
#                sys.exit("Got odd answer! Check sessionlog!")
        
    # reset v_id
    v_id=v_idstart
    command3="scope vlan-group "+v_ucs_vmnetworkgrp
    output = net_connect.send_command_timing(command3)

    while v_id<=v_idend:
        command4="create member-vlan vlan_lab"+str(v_id)
        output = net_connect.send_command_timing(command4)
        output = net_connect.send_command_timing(commandexit)
        v_id=v_id+1
    output = net_connect.send_command_timing(commandexit)
    command_save="commit-buffer"
    output = net_connect.send_command_timing(command_save)
    output = net_connect.send_command_timing(commandexit)
    net_connect.disconnect()

print("DONE - please check sessionlogs!")