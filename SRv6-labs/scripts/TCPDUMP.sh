#!/bin/bash

docker network ls | grep xr | awk '{print$2}'

read -p "Select And Paste Network Name: " DOCKERNET

IPGW=$(docker inspect -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}' $DOCKERNET); INT=$(ip address show | grep "$IPGW" | awk '{print$NF}'); sudo tcpdump -i $INT -s 65535 -w $DOCKERNET.pcap
