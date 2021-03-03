# vmware_sd-wan_5x0_migration_tool

# Not to be considered as best practices in using VMware VCO API
# Meant to be used in Lab environments - Please test it and use at your own risk
#
# Please note that VMWare API and Support team - do not guarantee this samples
# It is provided - AS IS - i.e. while I am glad to answer questions about API usage
# and behavior generally speaking, VMware cannot and do not specifically support these scripts
#
# Compatible with api v1 of the vmware sd-wan vco api
# using tokens to authenticate
#
#
# Script that can be used to migrate partial configuration from 5x0 to a edge6X0
#
# in this first version it supports copying existing Business Policies and Firewall Rules.
#
# I works by reading from a csv file containing a source edge name, a destination edge name and the interface mapping between the 2 versions
# 
# Sample edges.csv
# 
# 5x0,6x0,GE1,GE4,GE5,GE6,GE2,GE3,SFP1,SFP2
# EdgeOld,EdgeNew,GE1,GE4,GE5,GE6,GE2,GE3,SFP1,SFP2
#

The script will read the file and confirm if the Edge Source exists , if not it will ask you if you want to continue with the script or just stop processing.
Same applies for the destination edge, however you have the option to provision the destination edge with the same name if one does not exist.

During the provision , the new edge will use the same: Profile, License, PKI option as the original Edge.

You have a few options and inputs as below:
"-f", "--firewall",  Export Firewall Configurations"
"-b", "--business", Export Business Policy Configurations"
"-s", "--static", Export Static Routes"
"-p", "--provision", Option: Provision new Target 6x0 Edge"
"-i", "--input", "input file with edges and map info" - Required

Sample run:
python3 api_vco-copy-fw-rm-v2.py -i edges.csv -p -b -f

Enterprise Id = 308
Input Parameters
['5x0', 'n-6x0', 'GE1', 'GE4', 'GE5', 'GE6', 'GE2', 'GE3', 'SFP1', 'SFP2']
Source Edge: 5x0 found on VCO with Edge id: 1428
Provisioning new 6x0 named n-6x0
New Edge named n-6x0 created with Id 1452 and activation key 6F4M-2HW2-P2ZV-RSXE
Inserting new QOS module
Inserting new FW module

Input Parameters
['OldEdge', 'NewEdge', 'GE1', 'GE4', 'GE5', 'GE6', 'GE2', 'GE3', 'SFP1', 'SFP2']
Source Edge OldEdge not found!
Enter [yes/no] to continue: no


Sample 
