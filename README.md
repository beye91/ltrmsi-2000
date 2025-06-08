## Scenario
This solution shows SRv6 uSID as a full replacement of MPLS technology in Service Provider (SP) networks. In this preconfigured SRv6 sandbox the user will work with a small model of an SP network where IPv6 routing is used to provide underlay reachability and SRv6 is used to provide overlay services. This lab covers L3VPN as a service example and also demonstrates point-to-point L2VPN services using EVPN.

NOTE: This lab fully supports the L2VPN control plane. The L2VPN data plane is partially supported (E-Line only) in the virtual environment.

All features used in this lab are available in IOS XR 7.9.2. Functionality covered in this lab include:

•	SRv6 Locator  
•	SRv6 IS-IS  
•	SRv6 IS-IS TI-LFA  
•	SRv6 Traffic Engineering using Flexible Algorithm  
•	SRv6 Services: L3VPN and L2VPN (EVPN)  

The Docker image can be downloaded here: https://software.cisco.com/download/home/286331236/type/280805694/release/7.11.2
