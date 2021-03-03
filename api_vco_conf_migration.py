#!/usr/bin/env python3
#
# Author: vfrancadesou@vmware.com
#
# Not to be considered as best practices in using VMware VCO API
# Meant to be used in Lab environments - Please test it and use at your own risk
#
# please note that VMWare API and Support team - do not guarantee this samples
# It is provided - AS IS - i.e. while we are glad to answer questions about API usage
# and behavior generally speaking, VMware cannot and do not specifically support these scripts
#
# Compatible with api v1 of the vmware sd-wan vco api
# using tokens to authenticate
#
#
# Script that can be used to migrate partial configuration from 5x0 to a edge6X0
#
#
# Script that can be used to migrate partial configuration from 5x0 to a edge6X0

# in this first version it supports copying existing Business Policies and Firewall Rules.

# It works by reading from a csv file containing a source edge name, a destination edge name and the interface mapping between the 2 versions

#Sample edges.csv

# 5x0,6x0,GE1,GE4,GE5,GE6,GE2,GE3,SFP1,SFP2
# EdgeOld,EdgeNew,GE1,GE4,GE5,GE6,GE2,GE3,SFP1,SFP2

# The script will read the file and confirm if the Edge Source exists , if not it will ask you if you want to continue with the script or just stop processing. Same applies for the destination edge, however you have the option to provision the destination edge with the same name if one does not exist.

# During the provision , the new edge will use the same: Profile, License, PKI option as the original Edge.

# You have a few options and inputs as below:
# "-f", "--firewall", Export Firewall Configurations"
# "-b", "--business", Export Business Policy Configurations"
# "-s", "--static", Export Static Routes" (not implemented)
# "-p", "--provision", Option: Provision new Target 6x0 Edge"
# "-i", "--input", "input file with edges and map info" - Required


import os
import sys
import requests
import json
import copy
import argparse
import csv


######### VELO VARIABLES AND FUNCTIONS

########## VCO info and credentials
# Prefer to use OS environments to hold token variable
token = "Token %s" %(os.environ['VCO_TOKEN'])
headers = {"Content-Type": "application/json", "Authorization": token}
VCO_FQDN='vco58-usvi1.velocloud.net'
vco_url = 'https://'+ "vco58-usvi1.velocloud.net"+'/portal/rest/'
#vco_url = 'https://' + os.environ['VCO_FQDN'] + '/portal/'

######## VCO API methods
get_enterprise = vco_url + 'enterprise/getEnterprise'
get_edgelist = vco_url+'enterprise/getEnterpriseEdgeList'
get_edgeconfig = vco_url + 'edge/getEdgeConfigurationStack'
get_edgeoverview = vco_url + 'enterprise/getEnterpriseEdges'
update_edgeconfig = vco_url+'configuration/updateConfigurationModule'
edge_prov = vco_url+'edge/edgeProvision'
get_profiles =vco_url + 'enterprise/getEnterpriseConfigurations'
create_profile = vco_url+'configuration/cloneEnterpriseTemplate'
insert_module = vco_url+'configuration/insertConfigurationModule'


######## VCO FUNCTIONS

########

#### RETRIEVE ENTERPRISE ID for this user
def find_velo_enterpriseId():
	#Fetch enterprise id convert to JSON
	eid=0
	try:
	   enterprise = requests.post(get_enterprise, headers=headers, data='')
	except Exception as e:
	   print('Error while retrivieng Enterprise')
	   print(e)
	   sys.exit()
	ent_j = enterprise.json()
	eid=ent_j['id']
	print('Enterprise Id = %d'%(eid))
	return eid

#### CREATE NEW VMWARE SD-WAN CONFIGURATION PROFILE

def create_velo_profile(eid,ProfileName):
	### Confirm existing profile names, if "AWS-PROFILE" not found, create a new profile
	params = {'enterpriseId': eid	}
	try:
	   profile = requests.post(get_profiles, headers=headers, data=json.dumps(params))
	except Exception as e:
	   print('error getting profiles')
	   print(e)
	   sys.exit()
	prof_dict = profile.json()

	length = len(prof_dict)
	z=0
	ProfId=0
	notfound=True
	pid=0
	while z < length:
	    if(ProfileName==prof_dict[z]['name']):
				   pid = prof_dict[z]['id']
				   print ('Profile named '+ProfileName+' already found on VCO '+VCO_FQDN+' with Profile id: '+str(pid))
				   return pid
				   notfound=False
	    z+=1
	if(notfound):
		#Provision new Profile and grab its id
		 params = {"id" : eid,"name":ProfileName}
		 print('Profile not found, creating new one')
		 profile_resp = requests.post(create_profile, headers=headers, data=json.dumps(params))
		 #print(profile_resp.json())
		 prof_dict = profile_resp.json()
		 pid = prof_dict['id']
		 print('New Profile named '+ProfileName+' created with Id = %d'%(pid))
		 return pid

#### PROVISION NEW VMWARE SD-WAN EDGE
def provision_velo_edge(eid,pid,EdgeName,site):
	#### Provision new virtual edge in the AWS Profile
	#Provision new Profile and grab its id
	rEdgeName=EdgeName
	params = {'id' : eid,'name':rEdgeName,'modelNumber': 'virtual','configurationId': pid,'site': site}
	try:
		edid = requests.post(edge_prov, headers=headers, data=json.dumps(params))
		edid_j = edid.json()
		edid=edid_j['id']
		activationkey=edid_j['activationKey']
		print('New Edge named '+rEdgeName+' created with Id '+str(edid)+' and activation key '+activationkey)
		return [edid,activationkey]

	except Exception as e:
	     print(e)
	     sys.exit()
#############

def grab_config(ed_id):
    ### Grab base config from target EDGE

    params2 = {'edgeId': edid}
    Edge_Configuration = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params2))

    for configs in Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                for modules in configs["modules"]:
                    if modules["name"] == "deviceSettings":
                        Edge_device_settings_data = copy.copy(modules["data"])
                        Edge_settings_id = modules["id"]
                    if modules["name"] == "WAN":
                        Edge_wan_id = modules["id"]
                        Edge_wan_settings = copy.copy(modules["data"])
                    if modules["name"] == "firewall":
                        Edge_wan_id = modules["id"]
                        Edge_firewall_settings = copy.copy(modules["data"])
                    if modules["name"] == "QOS":
                        Edge_wan_id = modules["id"]
                        Edge_QOS_settings = copy.copy(modules["data"])

####### GRAB MODULE IDs
def grab_modules_id(ed_id):
    ### Grab target Edge Configuration Ids
    params2 = {'edgeId': edid}
    Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params2))
    Edge_Configuration=Edge_Config.json()

    Edge_settings_id = 0
    Edge_wan_id = 0
    Edge_qos_id = 0
    Edge_firewall_id = 0
    edge_overrides=False
    wan_change=True
    for configs in Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                for modules in configs["modules"]:
                    if modules["name"] == "deviceSettings":
                        #Edge_device_settings_data = copy.copy(modules["data"])
                        Edge_settings_id = modules["id"]
                    if modules["name"] == "WAN":
                        Edge_wan_id = modules["id"]
                        Edge_wan_settings = copy.copy(modules["data"])
                        #print(Edge_wan_settings)
                    if modules["name"] == "firewall":
                        Edge_wan_id = modules["id"]
                        #Edge_firewall_settings = copy.copy(modules["data"])
                    if modules["name"] == "QOS":
                        Edge_qos_id = modules["id"]
                        #Edge_QOS_settings = copy.copy(modules["data"])

    if (Edge_wan_settings=={}):
        #print('No WAN module override')
        wan_change=False
    if (Edge_qos_id == 0 and Edge_firewall_id == 0 and wan_change==False):
        #print('No Edge specific configuration has been overwritten')
        edge_overrides=False
    if (Edge_qos_id != 0 or Edge_firewall_id != 0):
        edge_overrides=True

    Configs_Id = {"Edge_settings_id": Edge_settings_id, "Edge_wan_id": Edge_wan_id,"Edge_qos_id": Edge_qos_id,"Edge_firewall_id":Edge_firewall_id,"Edge Overrides":edge_overrides,"Wan Module Changes":wan_change }
    return(Configs_Id)

#### Restore QOS module
def rebuild_qos(eid,ed_id,target_edid):
    ### Grab source Edge Configuration Id and Data
    params = {'edgeId': edid}
    Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
    Edge_Configuration=Edge_Config.json()
    Edge_qos_id = 0

    for configs in Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                for modules in configs["modules"]:
                    if modules["name"] == "QOS":
                        Edge_qos_id = modules["id"]
                        Edge_QOS_settings = copy.copy(modules["data"])
    ####
    params = {'edgeId': target_edid}
    Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
    T_Edge_Configuration=Edge_Config.json()
    T_Edge_qos_id = 0

    for configs in T_Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                config_id = configs["id"]
                print(config_id)
                for modules in configs["modules"]:
                    if modules["name"] == "QOS":
                        T_Edge_qos_id = modules["id"]
                        #print('Edge QOS ID '+str(T_Edge_qos_id))
    ##
    # If there is no QOS overrides in the Edge we need to create a new module
    ##
    if T_Edge_qos_id == 0:
        print('Inserting new QOS module')
        params_qos= {  "enterpriseId": eid,  "name": "QOS",  "data": Edge_QOS_settings,  "configurationId": config_id}
        resp = requests.post(insert_module, headers=headers, data=(json.dumps(params_qos)))
        #print(resp.json())

    else:

         d={"data":{}}
         d['data']=Edge_QOS_settings
         params = {"enterpridId": eid,
         "configurationModuleId" : T_Edge_qos_id,
         "returnData" : 'true',
         "_update":  d,
        }
         print(params)
         resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params)))
         #print(resp.json())
         print('Business Policy Rules updated')


def swap_ints(argument,map):
    switcher = map
    return switcher.get(argument, "")

def remap_qos(eid,ed_id,target_edid):
    #### REMAP QOS
    params2 = {'edgeId': edid}
    Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params2))
    Edge_Configuration=Edge_Config.json()

    Edge_settings_id = 0
    Edge_wan_id = 0
    Edge_qos_id = 0
    Edge_firewall_id = 0
    edge_overrides=False
    wan_change=True
    for configs in Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                for modules in configs["modules"]:
                    if modules["name"] == "QOS":
                        Edge_qos_id = modules["id"]
                        Edge_QOS_settings = copy.copy(modules["data"])

    # Change interface config
    ### GLOBAL Segment
    #print(Edge_QOS_settings['segments'][0]['rules'])
    rules_l=Edge_QOS_settings['segments'][0]['rules']
    # print(rules_l)
    i=0
    for rules in rules_l:
        #print(rules['match']['dInterface'])
        arg=rules['match']['dInterface']
        rules['match']['dInterface']=swap_ints(arg,switcher)
        arg=rules['match']['sInterface']
        rules['match']['sInterface']=swap_ints(arg,switcher)
        arg=rules['action']['edge2EdgeRouteAction']['interface']
        rules['action']['edge2EdgeRouteAction']['interface']=swap_ints(arg,switcher)
        arg=rules['action']['edge2EdgeRouteAction']['wanlink']
        rules['action']['edge2EdgeRouteAction']['wanlink']=swap_ints(arg,switcher)
        arg=rules['action']['edge2DataCenterRouteAction']['interface']
        rules['action']['edge2DataCenterRouteAction']['interface']=swap_ints(arg,switcher)
        arg=rules['action']['edge2DataCenterRouteAction']['wanlink']
        rules['action']['edge2DataCenterRouteAction']['wanlink']=swap_ints(arg,switcher)
        arg=rules['action']['edge2CloudRouteAction']['interface']
        rules['action']['edge2CloudRouteAction']['interface']=swap_ints(arg,switcher)
        arg=rules['action']['edge2CloudRouteAction']['wanlink']
        rules['action']['edge2CloudRouteAction']['wanlink']=swap_ints(arg,switcher)
        #print(rules)
        #print(' ')
        Edge_QOS_settings['segments'][0]['rules'][i]=rules
        i+=1


    #print(Edge_QOS_settings)
    params = {'edgeId': target_edid}
    Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
    T_Edge_Configuration=Edge_Config.json()
    T_Edge_qos_id = 0

    for configs in T_Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                config_id = configs["id"]
                #print(config_id)
                for modules in configs["modules"]:
                    if modules["name"] == "QOS":
                        T_Edge_qos_id = modules["id"]
                        #print('Edge QOS ID '+str(T_Edge_qos_id))
    ##
    # If there is no QOS overrides in the Edge we need to create a new module
    ##
    if T_Edge_qos_id == 0:
        print('Inserting new QOS module')
        params_qos= {  "enterpriseId": eid,  "name": "QOS",  "data": Edge_QOS_settings,  "configurationId": config_id}
        resp = requests.post(insert_module, headers=headers, data=(json.dumps(params_qos)))
        #print(resp.json())

    else:

         d={"data":{}}
         d['data']=Edge_QOS_settings
         params = {"enterpridId": eid,
         "configurationModuleId" : T_Edge_qos_id,
         "returnData" : 'true',
         "_update":  d,
        }
         #print(params)
         resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params)))
         #print(resp.json())
         print('Business Policy Rules updated')

#### Restore FW module no interface swap
def rebuild_fw(eid,ed_id,target_edid):
    ### Grab source Edge Configuration Id and Data
    params = {'edgeId': edid}
    Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
    Edge_Configuration=Edge_Config.json()
    Edge_fw_id = 0

    for configs in Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                for modules in configs["modules"]:
                    if modules["name"] == "firewall":
                        Edge_fw_id = modules["id"]
                        Edge_fw_settings = copy.copy(modules["data"])
    ####
    params = {'edgeId': target_edid}
    Edge_Config = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
    T_Edge_Configuration=Edge_Config.json()
    T_Edge_fw_id = 0

    for configs in T_Edge_Configuration:
            if configs["name"] == "Edge Specific Profile":
                config_id = configs["id"]
                #print(config_id)
                for modules in configs["modules"]:
                    if modules["name"] == "firewall":
                        T_Edge_fw_id = modules["id"]
                        #print('Edge QOS ID '+str(T_Edge_qos_id))

#### remap_fw
    # Change interface config
    ### GLOBAL Segment
    #print(Edge_QOS_settings['segments'][0]['rules'])
    rules_l=Edge_fw_settings['segments'][0]['outbound']
    #print(rules_l)
    i=0
    for rules in rules_l:
        #print(rules['match']['dInterface'])
        arg=rules['match']['dInterface']
        rules['match']['dInterface']=swap_ints(arg,switcher)
        arg=rules['match']['sInterface']
        rules['match']['sInterface']=swap_ints(arg,switcher)

        #print(rules)
        #print(' ')
        Edge_fw_settings['segments'][0]['outbound'][i]=rules
        i+=1

    ##
    # If there is no QOS overrides in the Edge we need to create a new module
    ##
    if T_Edge_fw_id == 0:
        print('Inserting new FW module')
        params= {  "enterpriseId": eid,  "name": "firewall",  "data": Edge_fw_settings,  "configurationId": config_id}
        resp = requests.post(insert_module, headers=headers, data=(json.dumps(params)))
        #print(resp.json())

    else:
         d={"data":{}}
         d['data']=Edge_fw_settings
         params = {"enterpridId": eid,
         "configurationModuleId" : T_Edge_fw_id,
         "returnData" : 'true',
         "_update":  d,
        }
         #print(params)
         resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params)))
         #print(resp.json())
         print('Firewall Rules updated')

##### Find Edge in the list
def search_name(name,listName):
    for p in listName:
        if p['name'] == name:
            return p

#### PROVISION NEW VMWARE SD-WAN EDGE
def provision_velo_edge(eid,pid,EdgeName,site,edgelic):
	#### Provision new virtual edge in the AWS Profile
	#Provision new Profile and grab its id
	rEdgeName=EdgeName
	params = {'id' : eid,'name':rEdgeName,'modelNumber': 'edge6X0','configurationId': pid,'site': site}
	try:
		edid = requests.post(edge_prov, headers=headers, data=json.dumps(params))
		edid_j = edid.json()
		edid=edid_j['id']
		activationkey=edid_j['activationKey']
		print('New Edge named '+rEdgeName+' created with Id '+str(edid)+' and activation key '+activationkey)
		return [edid,activationkey]

	except Exception as e:
	     print(e)
	     sys.exit()

######################### Main Program #####################

#### MAIN BODY

######################### Main Program #####################

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--firewall",  action='store_true', help="Option: Export Firewall Configurations",default = False)
parser.add_argument("-b", "--business", action='store_true', help="Option: Export Business Policy Configurations",default = False)
parser.add_argument("-s", "--static", action='store_true', help="Option: Export Static Routes",default = False)
parser.add_argument("-p", "--provision", action='store_true', help="Option: Provision new Target 6x0 Edge",default = False)
parser.add_argument("-i", "--input", help="input file with edges and map info",required=True)
#parser.add_argument('EdgeSource')
#parser.add_argument('EdgeDest')
#parser.add_argument('Map')
#print(f'Source 5x0 {args.EdgeSource} and Target 6x0 {args.EdgeDest} with Interface Mapping {args.EdgeSource}')

args = parser.parse_args()
#if args.firewall:
#    print("Exporting Firewall Configurations")
#if args.business:
#    print("Exporting Business Policy Configurations")
#if args.static:
#    print("Exporting Static Routes")
#print(args.input)

#with open(args.input) as json_file:
#    jfile = json.load(json_file)
#EdgeSrcName= jfile['SrcEdge']
#EdgeTrgName=jfile['TrgEdge']
switcher={
  "LAN1": "GE1",
  "LAN2": "GE4",
  "LAN3": "GE5",
  "LAN4": "GE6",
  "GE1": "GE2",
  "GE2": "GE3",
  "SFP1": "SFP1",
  "SFP2": "SFP2",
  "auto": "auto"
}

eid = find_velo_enterpriseId()

with open(args.input) as csvfile:
	readCSV = csv.reader(csvfile, delimiter=',')
	for row in readCSV:
		print('Input Parameters')
		print(row)
		EdgeSrcName=row[0]
		EdgeTrgName=row[1]
		switcher['LAN1']=row[2]
		switcher['LAN2']=row[3]
		switcher['LAN3']=row[4]
		switcher['LAN4']=row[5]
		switcher['GE1']=row[6]
		switcher['GE2']=row[7]
		switcher['SFP1']=row[8]
		switcher['SFP2']=row[9]

		#print(EdgeSrcName)
		#edid= 1428
		#target_edid=1429

		# Find Source Edge id based on Edge name
		params = {'enterpriseId': eid	}
		try:
		  edgesList = requests.post(get_edgelist, headers=headers, data=json.dumps(params))
		except Exception as e:
		  print(e)
		  sys.exit()
		eList_dict=edgesList.json()
		length = len(eList_dict)
		#print(eList_dict)
		#print(length)
		#### Find Source Edge
		name=search_name(EdgeSrcName, eList_dict)
		#print(name)
		if (str(name)=='None'):
			print('Source Edge '+EdgeSrcName+' not found!')
			go=False
			while go==False:
				a = input("Enter [yes/no] to continue: ").lower()
				if a=="yes":
					go=True
					continue
				elif a=="no":
					sys.exit(0)
				else:
					print("Enter either yes/no: ")

		else:
			edid = name['id']
			print ('Source Edge: '+EdgeSrcName+' found on VCO with Edge id: '+str(edid))

		if(args.provision):
			### Only try to provision if Edge does not exists
			name=search_name(EdgeTrgName, eList_dict)
			if (str(name)=='None'):
				print('Provisioning new 6x0 named '+EdgeTrgName)
				### Grab Edge Overview info being used by source EDGE
				#Change device settings to match needed interface config so it matches cloudformation
				params = {'with':['certificates','configuration',"site",'licenses'],'edgeIds':[edid]}
				resp = requests.post(get_edgeoverview, headers=headers, data=json.dumps(params))
				resp_j = resp.json()
				pki= (resp_j[0]['endpointPkiMode'])
				EdgeContactName=(resp_j[0]['site']['contactName'])
				EdgeContactEmail=(resp_j[0]['site']['contactEmail'])
				pid=(resp_j[0]['configuration']['enterprise']['id'])
				elic=(resp_j[0]['licenses'][0]['id'])

				site={
	      "contactName": EdgeContactName,
	      "contactEmail": EdgeContactEmail
	    }

				params = {'id' : eid,'name':EdgeTrgName,'modelNumber': 'edge6x0','configurationId': pid,'edgeLicenseId': elic,'endpointPkiMode': pki,'site':site}
				#print (params)
				try:
				    redid = requests.post(edge_prov, headers=headers, data=json.dumps(params))

				    edid_j = redid.json()
				    #print(edid_j)
				    target_edid=edid_j['id']
				    activationkey=edid_j['activationKey']
				    print('New Edge named '+EdgeTrgName+' created with Id '+str(target_edid)+' and activation key '+activationkey)
				except Exception as e:
				     print('Error provisioning edge')
				     sys.exit()
			else:
				target_edid = name['id']
				print ('Skipping Provisioning - Target Edge: '+EdgeTrgName+' found on VCO with Edge id: '+str(target_edid))

		else: #### Without Provisioning option - expect edge to be present

			name=search_name(EdgeTrgName, eList_dict)
			#print(name)
			if (str(name)=='None'):
				print('Target Edge '+EdgeTrgName+' not found, rerun script with the option -p to provision a new 6x0 edge')
				go=False
				while go==False:
					a = input("Enter [yes/no] to continue: ").lower()
					if a=="yes":
						go=True
						continue
					elif a=="no":
						sys.exit(0)
					else:
						print("Enter either yes/no: ")
			else:
				target_edid = name['id']
				print ('Target Edge: '+EdgeTrgName+' found on VCO with Edge id: '+str(target_edid))

		modules_id=grab_modules_id(edid)

    	###### Rebuild Business Policy (QOS module) with Interface Remap
		if(args.business):
			if (modules_id["Edge_qos_id"] != 0):
			    remap_qos(eid,edid,target_edid)

		###### Rebuild FW Rules with Interface Remap
		if(args.firewall):
			if (modules_id["Edge_qos_id"] != 0):
			    rebuild_fw(eid,edid,target_edid)
		print('')
