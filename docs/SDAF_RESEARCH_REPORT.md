# SDAF Conversational Chat Agent - Comprehensive Research Report

## Executive Summary

This report provides a complete analysis of the SAP Deployment Automation Framework (SDAF) System deployment parameters to enable building a conversational chat agent that generates SDAF-compliant tfvars files. The research identifies 200+ parameters, categorizes them into 15 logical groups, and designs a streamlined 6-prompt conversational flow that asks users only the essential parameters while applying sensible defaults for all others.

---

## 1. Complete Parameter Inventory

### 1.1 Environment & Identity (7 parameters)
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `environment` | string | Environment identifier (max 5 chars) | "DEV", "PROD", "NP" |
| `location` | string | Azure region for deployment | "westeurope", "eastus" |
| `network_logical_name` | string | Network identifier (max 7 chars) | "SAP01", "SAP02" |
| `sid` | string | SAP Application System ID (3 chars) | "X00", "S15" |
| `database_sid` | string | Database System ID | "HDB", "XDB" |
| `web_sid` | string | Web Dispatcher SID | "W00" |
| `Description` | string | SAP system description | "HANA distributed system" |

### 1.2 Database Platform & Sizing (12 parameters)
| Parameter | Type | Required | Description | Valid Values |
|-----------|------|----------|-------------|--------------|
| `database_platform` | string | YES | Database backend | HANA, DB2, ORACLE, ASE, SQLSERVER, NONE |
| `database_size` | string | YES | VM sizing key for HANA | See Section 2.1 for all options |
| `database_vm_sku` | string | NO | Override VM size | Any Azure VM SKU |
| `database_server_count` | int | NO | Number of DB servers | Default: 1 |
| `database_high_availability` | bool | NO | Deploy DB as HA | Default: false |
| `database_vm_zones` | array | NO | Availability zones | ["1"], ["2"], ["3"] |
| `database_instance_number` | string | NO | Database instance number | "00", "01", etc. |
| `database_vm_use_DHCP` | bool | NO | Use Azure DHCP | Default: true |
| `database_use_ppg` | bool | NO | Use proximity placement group | Default: false |
| `database_use_avset` | bool | NO | Use availability set | Default: false |
| `database_dual_nics` | bool | NO | Deploy dual NICs | Default: false |
| `database_use_premium_v2_storage` | bool | NO | Use Premium v2 storage | Default: false |

### 1.3 Database VM Image (7 parameters)
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `database_vm_image.os_type` | string | Operating system type | "LINUX", "WINDOWS" |
| `database_vm_image.publisher` | string | Image publisher | "SUSE", "RedHat" |
| `database_vm_image.offer` | string | Image offer | "sles-sap-15-sp5" |
| `database_vm_image.sku` | string | Image SKU | "gen2" |
| `database_vm_image.version` | string | Image version | "latest" |
| `database_vm_image.type` | string | Image type | "marketplace", "custom" |
| `database_vm_image.source_image_id` | string | Custom image resource ID | ARM resource ID |

### 1.4 Application Tier Configuration (15 parameters)
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `enable_app_tier_deployment` | bool | NO | Deploy application tier | true |
| `app_tier_sizing_dictionary_key` | string | NO | Sizing profile | "Optimized" |
| `app_tier_use_DHCP` | bool | NO | Use Azure DHCP | true |
| `app_tier_dual_nics` | bool | NO | Deploy dual NICs | false |
| `app_tier_authentication_type` | string | NO | Auth method | "key", "password" |
| `application_server_count` | int | YES | Number of app servers | 1 |
| `application_server_sku` | string | NO | VM size override | - |
| `application_server_zones` | array | NO | Availability zones | ["1"] |
| `application_server_use_ppg` | bool | NO | Use PPG | true |
| `application_server_use_avset` | bool | NO | Use availability set | true |
| `application_server_image.*` | object | NO | Image configuration | Same as DB image |
| `application_server_app_nic_ips` | array | NO | Static IPs | - |
| `application_server_admin_nic_ips` | array | NO | Admin subnet IPs | - |
| `application_server_nic_secondary_ips` | array | NO | Secondary IPs | - |
| `application_server_tags` | array | NO | Resource tags | - |

### 1.5 SAP Central Services (SCS) Configuration (16 parameters)
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `scs_server_count` | int | YES | Number of SCS servers | 1 |
| `scs_high_availability` | bool | NO | Deploy SCS as HA | false |
| `scs_instance_number` | string | NO | SCS instance number | "00" |
| `ers_instance_number` | string | NO | ERS instance number | "01" |
| `pas_instance_number` | string | NO | PAS instance number | "00" |
| `scs_server_sku` | string | NO | VM size override | - |
| `scs_server_zones` | array | NO | Availability zones | ["1"] |
| `scs_server_use_ppg` | bool | NO | Use PPG | true |
| `scs_server_use_avset` | bool | NO | Use availability set | false |
| `scs_server_image.*` | object | NO | Image configuration | Same as DB image |
| `scs_server_app_nic_ips` | array | NO | App subnet IPs | - |
| `scs_server_admin_nic_ips` | array | NO | Admin subnet IPs | - |
| `scs_server_nic_secondary_ips` | array | NO | Secondary IPs | - |
| `scs_server_loadbalancer_ips` | array | NO | Load balancer IPs | - |
| `scs_server_tags` | array | NO | Resource tags | - |
| `app_instance_number` | string | NO | Application instance number | - |

### 1.6 Web Dispatcher Configuration (13 parameters)
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `webdispatcher_server_count` | int | NO | Number of web dispatchers | 0 |
| `web_sid` | string | NO | Web Dispatcher SID | - |
| `web_instance_number` | string | NO | Web instance number | "00" |
| `webdispatcher_server_sku` | string | NO | VM size override | - |
| `webdispatcher_server_zones` | array | NO | Availability zones | ["1"] |
| `webdispatcher_server_use_ppg` | bool | NO | Use PPG | false |
| `webdispatcher_server_use_avset` | bool | NO | Use availability set | true |
| `webdispatcher_server_image.*` | object | NO | Image configuration | - |
| `webdispatcher_server_app_nic_ips` | array | NO | App subnet IPs | - |
| `webdispatcher_server_admin_nic_ips` | array | NO | Admin subnet IPs | - |
| `webdispatcher_server_nic_secondary_ips` | array | NO | Secondary IPs | - |
| `webdispatcher_server_loadbalancer_ips` | array | NO | Load balancer IPs | - |
| `webdispatcher_server_tags` | array | NO | Resource tags | - |

### 1.7 High Availability & Clustering (18 parameters)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `database_cluster_type` | string | DB cluster quorum type | "AFA" |
| `scs_cluster_type` | string | SCS cluster quorum type | "AFA" |
| `database_cluster_disk_lun` | int | LUN for DB cluster disk | 8 |
| `database_cluster_disk_size` | int | DB cluster disk size (GB) | 128 |
| `database_cluster_disk_type` | string | DB cluster storage type | "Premium_ZRS" |
| `scs_cluster_disk_lun` | int | LUN for SCS cluster disk | 5 |
| `scs_cluster_disk_size` | int | SCS cluster disk size (GB) | 128 |
| `scs_cluster_disk_type` | string | SCS cluster storage type | "Premium_ZRS" |
| `use_msi_for_clusters` | bool | Use MSI for Pacemaker fencing | true |
| `fencing_role_name` | string | Azure role for fencing | - |
| `use_simple_mount` | bool | Use Simple mounts (SLES 15+) | false |
| `use_fence_kdump` | bool | Use fence_kdump for fencing | false |
| `use_fence_kdump_size_gb_db` | int | Kdump disk size for DB (GB) | 128 |
| `use_fence_kdump_lun_db` | int | Kdump disk LUN for DB | 8 |
| `use_fence_kdump_size_gb_scs` | int | Kdump disk size for SCS (GB) | 64 |
| `use_fence_kdump_lun_scs` | int | Kdump disk LUN for SCS | 4 |
| `use_sles_saphanasr_angi` | bool | Use SLES HANA SR ANGI | - |
| `database_active_active` | bool | Active-active DB configuration | - |

### 1.8 Networking (25 parameters)
| Parameter | Type | Description | Required For |
|-----------|------|-------------|--------------|
| `network_arm_id` | string | VNet ARM resource ID | Brownfield |
| `admin_subnet_address_prefix` | string | Admin subnet CIDR | Greenfield |
| `admin_subnet_arm_id` | string | Admin subnet ARM ID | Brownfield |
| `admin_subnet_name` | string | Admin subnet name | Brownfield |
| `admin_subnet_nsg_arm_id` | string | Admin NSG ARM ID | Brownfield |
| `admin_subnet_nsg_name` | string | Admin NSG name | Brownfield |
| `db_subnet_address_prefix` | string | DB subnet CIDR | Greenfield |
| `db_subnet_arm_id` | string | DB subnet ARM ID | Brownfield |
| `db_subnet_name` | string | DB subnet name | Brownfield |
| `db_subnet_nsg_arm_id` | string | DB NSG ARM ID | Brownfield |
| `db_subnet_nsg_name` | string | DB NSG name | Brownfield |
| `app_subnet_address_prefix` | string | App subnet CIDR | Greenfield |
| `app_subnet_arm_id` | string | App subnet ARM ID | Brownfield |
| `app_subnet_name` | string | App subnet name | Brownfield |
| `app_subnet_nsg_arm_id` | string | App NSG ARM ID | Brownfield |
| `app_subnet_nsg_name` | string | App NSG name | Brownfield |
| `web_subnet_address_prefix` | string | Web subnet CIDR | Greenfield |
| `web_subnet_arm_id` | string | Web subnet ARM ID | Brownfield |
| `web_subnet_name` | string | Web subnet name | Brownfield |
| `web_subnet_nsg_arm_id` | string | Web NSG ARM ID | Brownfield |
| `web_subnet_nsg_name` | string | Web NSG name | Brownfield |
| `nsg_asg_with_vnet` | bool | ASG creation location | Default: false |
| `dual_nics` | bool | Dual NIC deployment | Default: true |
| `use_loadbalancers_for_standalone_deployments` | bool | Use LB for non-HA | Default: true |
| `use_private_endpoint` | bool | Private endpoints for KV/Storage | Default: true |

### 1.9 NFS & Shared Storage (8 parameters)
| Parameter | Type | Description | Valid Values |
|-----------|------|-------------|--------------|
| `NFS_provider` | string | NFS provider type | ANF, AFS, NFS, NONE |
| `sapmnt_volume_size` | int | Sapmnt volume size (GB) | Default: 128 |
| `use_random_id_for_storageaccounts` | bool | Add random suffix | Default: true |
| `azure_files_sapmnt_id` | string | Azure Files resource ID | ARM ID |
| `sapmnt_private_endpoint_id` | string | Private endpoint ID | ARM ID |
| `hanashared_id` | array | HANA shared storage IDs | ARM IDs |
| `hanashared_private_endpoint_id` | array | Private endpoint IDs | ARM IDs |
| `shared_access_key_enabled` | bool | Enable access keys | Default: false |

### 1.10 Azure NetApp Files (ANF) Configuration (22 parameters)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `ANF_HANA_use_AVG` | bool | Use Application Volume Group | false |
| `ANF_HANA_use_Zones` | bool | Use Availability zones | true |
| **Data Volumes** | | | |
| `ANF_HANA_data` | bool | Use ANF for data | - |
| `ANF_HANA_data_volume_size` | int | Data volume size (GB) | 256 |
| `ANF_HANA_data_volume_throughput` | int | Data throughput (MB/s) | 128 |
| `ANF_HANA_data_volume_count` | int | Number of data volumes | 1 |
| `ANF_HANA_data_use_existing_volume` | bool | Use existing volume | - |
| `ANF_HANA_data_volume_name` | string | Volume name | - |
| **Log Volumes** | | | |
| `ANF_HANA_log` | bool | Use ANF for log | - |
| `ANF_HANA_log_volume_size` | int | Log volume size (GB) | 128 |
| `ANF_HANA_log_volume_throughput` | int | Log throughput (MB/s) | 128 |
| `ANF_HANA_log_volume_count` | int | Number of log volumes | 1 |
| `ANF_HANA_log_use_existing` | bool | Use existing volume | - |
| `ANF_HANA_log_volume_name` | string | Volume name | - |
| **Shared Volumes** | | | |
| `ANF_HANA_shared` | bool | Use ANF for shared | - |
| `ANF_HANA_shared_volume_size` | int | Shared volume size (GB) | - |
| `ANF_HANA_shared_volume_throughput` | int | Throughput (MB/s) | - |
| `ANF_HANA_shared_use_existing` | bool | Use existing volume | - |
| `ANF_HANA_shared_volume_name` | string | Volume name | - |
| **USR SAP** | | | |
| `ANF_usr_sap` | bool | Use ANF for /usr/sap | - |
| `ANF_usr_sap_volume_size` | int | Volume size (GB) | - |
| `ANF_usr_sap_throughput` | int | Throughput (MB/s) | - |

### 1.11 HANA Scale-Out (4 parameters)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `database_HANA_use_scaleout_scenario` | bool | Enable scale-out | false |
| `database_HANA_no_standby_role` | bool | No standby nodes | false |
| `stand_by_node_count` | int | Standby node count | 0 |
| `database_HANA_use_ANF_scaleout_scenario` | bool | ANF for scale-out | false |

### 1.12 Authentication & Security (11 parameters)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `automation_username` | string | Admin username | - |
| `automation_password` | string | Admin password | - |
| `automation_path_to_public_key` | string | SSH public key path | - |
| `automation_path_to_private_key` | string | SSH private key path | - |
| `database_vm_authentication_type` | string | Auth method | "key", "password" |
| `user_keyvault_id` | string | User Key Vault ARM ID | - |
| `spn_keyvault_id` | string | SPN Key Vault ARM ID | - |
| `enable_purge_control_for_keyvaults` | bool | Enable purge protection | false |
| `user_assigned_identity_id` | string | User-assigned identity ID | - |
| `vm_disk_encryption_set_id` | string | Disk encryption set ID | - |
| `use_spn` | bool | Use SPN vs MSI | false |

### 1.13 Resource Management (11 parameters)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `subscription` | string | Subscription name | - |
| `subscription_id` | string | Subscription GUID | - |
| `resourcegroup_name` | string | Resource group name | - |
| `resourcegroup_arm_id` | string | Resource group ARM ID | - |
| `prevent_deletion_if_contains_resources` | bool | Prevent deletion | true |
| `tags` | array | Resource tags | [] |
| `custom_prefix` | string | Custom naming prefix | - |
| `use_prefix` | bool | Use prefix in names | true |
| `use_zonal_markers` | bool | Add zone to VM names | true |
| `resource_offset` | int | Resource naming offset | 0 |
| `save_naming_information` | bool | Save names to JSON | false |

### 1.14 VM Extensions & Monitoring (9 parameters)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `deploy_monitoring_extension` | bool | Azure Monitor extension | false |
| `deploy_v1_monitoring_extension` | bool | Enhanced monitoring extension | false |
| `deploy_defender_extension` | bool | Defender extension | false |
| `deploy_application_security_groups` | bool | Create ASGs | true |
| `enable_ha_monitoring` | bool | Prometheus HA monitoring | false |
| `enable_os_monitoring` | bool | Prometheus OS monitoring | false |
| `ams_resource_id` | string | Azure Monitor for SAP ID | - |
| `patch_mode` | string | VM patching mode | "ImageDefault" |
| `patch_assessment_mode` | string | Patch assessment mode | "ImageDefault" |

### 1.15 Advanced Configuration (15 parameters)
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `use_secondary_ips` | bool | VMs with secondary IPs | false |
| `use_scalesets_for_deployment` | bool | Use VM Scale Sets | false |
| `upgrade_packages` | bool | Upgrade packages on deploy | false |
| `bom_name` | string | Bill of Materials name | - |
| `custom_disk_sizes_filename` | string | Custom disk config file | - |
| `name_override_file` | string | Name override file | - |
| `dns_a_records_for_secondary_names` | bool | DNS for virtual hostnames | true |
| `register_endpoints_with_dns` | bool | Register endpoints | true |
| `use_service_endpoint` | bool | Use service endpoints | - |
| `shared_access_key_enabled_nfs` | bool | Access keys for NFS | false |
| `configuration_settings` | array | Custom config settings | [] |
| `scaleset_id` | string | Scale set resource ID | - |
| `workload_zone` | string | Workload zone reference | - |
| `tfstate_resource_id` | string | Terraform state storage | - |
| `deploy_anchor_vm` | bool | Deploy anchor VM | - |

---

## 2. Sizing Dictionary Reference

### 2.1 HANA Database Sizing Options (46 Options)

| Dictionary Key | VM SKU | Memory | Use Case |
|----------------|--------|--------|----------|
| **Demo/Development** | | | |
| Default | Standard_D8s_v3 | 32 GB | Basic testing |
| Demo | Standard_D8s_v3 | 32 GB | Demo systems |
| S4Demo | Standard_E32ds_v4 | 256 GB | S/4HANA demo |
| **Production - E-Series (Gen Purpose)** | | | |
| E20ds_v4 | Standard_E20ds_v4 | 160 GB | Small production |
| E20ds_v5 | Standard_E20ds_v5 | 160 GB | Small production (v5) |
| E32ds_v4 | Standard_E32ds_v4 | 256 GB | Medium production |
| E32ds_v5 | Standard_E32ds_v5 | 256 GB | Medium production (v5) |
| E48ds_v4 | Standard_E48ds_v4 | 384 GB | Large production |
| E48ds_v5 | Standard_E48ds_v5 | 384 GB | Large production (v5) |
| E64s_v3 | Standard_E64s_v3 | 432 GB | Large production |
| E64ds_v4 | Standard_E64ds_v4 | 504 GB | XLarge production |
| E64ds_v5 | Standard_E64ds_v5 | 512 GB | XLarge production (v5) |
| E96ds_v5 | Standard_E96ds_v5 | 672 GB | XXLarge production |
| **Production - M-Series (Memory Optimized)** | | | |
| M32ts | Standard_M32ts | 192 GB | Certified HANA |
| M32ls | Standard_M32ls | 256 GB | Certified HANA |
| M64ls | Standard_M64ls | 512 GB | Medium HANA |
| M64s | Standard_M64s | 1 TB | Large HANA |
| M64ms | Standard_M64ms | 1.7 TB | XLarge HANA |
| M128s | Standard_M128s | 2 TB | XXLarge HANA |
| M128ms | Standard_M128ms | 3.8 TB | XXXL HANA |
| M208s_v2 | Standard_M208s_v2 | 2.85 TB | Large HANA v2 |
| M208ms_v2 | Standard_M208ms_v2 | 5.7 TB | XLarge HANA v2 |
| M416s_v2 | Standard_M416s_v2 | 5.7 TB | XXLarge HANA v2 |
| M416ms_v2 | Standard_M416ms_v2 | 11.4 TB | XXXL HANA v2 |
| **M-Series Gen 3/4** | | | |
| M96ds_1_v3 | Standard_M96ds_1_v3 | 1.9 TB | Gen3 Medium |
| M176ds_3_v3 | Standard_M176ds_3_v3 | 3.5 TB | Gen3 Large |
| M176ds_3_v4 | Standard_M176ds_3_v4 | 3.5 TB | Gen4 Large |
| M416ds_6_v3 | Standard_M416ds_6_v3 | 8.3 TB | Gen3 XLarge |
| M416s_8_v2 | Standard_M416s_8_v2 | 11.4 TB | Ultra Large |

**Note:** Full list includes 46 options. See `/deploy/configs/hana_sizes.json` for complete details.

### 2.2 Application Tier Sizing Options (3 Options)

| Dictionary Key | App Server SKU | SCS SKU | Use Case |
|----------------|----------------|---------|----------|
| Default | Standard_D4s_v3 | Standard_D4ds_v5 | Basic deployments |
| Production | Standard_D4s_v3 | Standard_D4ds_v5 | Production (cost-optimized) |
| Optimized | Standard_D4ds_v5 | Standard_D4ds_v5 | Production (performance) |

**Application Server:** 4 vCPUs, 16 GB RAM
**SCS Server:** 4 vCPUs, 16 GB RAM

---

## 3. Parameter Classification: Required vs Optional

### 3.1 ALWAYS REQUIRED (Core Identity - 7 parameters)
1. `environment` - Environment identifier
2. `location` - Azure region
3. `network_logical_name` - Network name
4. `sid` - SAP Application SID
5. `database_sid` - Database SID
6. `database_platform` - Database type
7. `database_size` - Database VM sizing

### 3.2 REQUIRED FOR GREENFIELD (New Network - 4 parameters)
1. `admin_subnet_address_prefix`
2. `db_subnet_address_prefix`
3. `app_subnet_address_prefix`
4. `web_subnet_address_prefix`

### 3.3 REQUIRED FOR BROWNFIELD (Existing Network - 12+ parameters)
All `*_arm_id` parameters for existing resources:
- Network ARM IDs
- Subnet ARM IDs
- NSG ARM IDs
- Resource Group ARM IDs

### 3.4 CONTEXTUALLY REQUIRED
- `scs_server_count` - Required if deploying distributed architecture
- `application_server_count` - Required if deploying app tier
- `webdispatcher_server_count` - Required if deploying web dispatchers
- `web_sid` - Required if web dispatcher count > 0
- ANF parameters - Required if `NFS_provider` = "ANF"
- Cluster parameters - Required if HA = true

### 3.5 OPTIONAL WITH SENSIBLE DEFAULTS (180+ parameters)
All other parameters have framework-provided defaults.

---

## 4. Easy Mode: Minimal Parameter Set

### 4.1 Philosophy
Ask users 5-6 conversational prompts covering only essential decisions. Everything else gets sensible defaults.

### 4.2 The 6 Essential Questions

#### Question 1: Environment Identity
**What to ask:**
- Environment name (DEV/PROD/QA)
- Azure region
- Network name

**Why:** Forms the naming foundation for all resources.

#### Question 2: SAP System Identity
**What to ask:**
- SAP Application SID
- Database SID
- Database platform (HANA/Oracle/SQL Server/etc.)

**Why:** Defines what type of SAP system is being deployed.

#### Question 3: System Size
**What to ask:**
- Database size (Demo/Small/Medium/Large/XLarge)
- Expected workload (Development/Production)

**Why:** Determines VM sizing and performance.

#### Question 4: Architecture Pattern
**What to ask:**
- Standalone vs Distributed
- High Availability needed?
- Number of application servers (if distributed)

**Why:** Shapes the deployment topology.

#### Question 5: Network Configuration
**What to ask:**
- Greenfield (new network) vs Brownfield (existing)
- If Greenfield: suggest default subnet CIDRs
- If Brownfield: collect subnet ARM IDs

**Why:** Critical infrastructure dependency.

#### Question 6: Operating System
**What to ask:**
- OS family (SUSE SLES / Red Hat RHEL)
- Version preference (15 SP5 / 8.x / latest)

**Why:** Determines VM image configuration.

### 4.3 Default Values for Non-Prompted Parameters

| Category | Parameters | Default Value |
|----------|------------|---------------|
| **HA Clustering** | All cluster settings | Disabled (non-HA) |
| **Web Dispatcher** | All web tier settings | Not deployed (count=0) |
| **Monitoring** | All monitoring extensions | Disabled |
| **NFS** | NFS_provider | "AFS" (Azure Files) |
| **Authentication** | Auth type | SSH key |
| **Networking** | Use DHCP | true |
| **Networking** | Dual NICs | false |
| **Networking** | Private endpoints | true |
| **VM Options** | Use PPG (DB/SCS) | true |
| **VM Options** | Use Availability Set (App) | true |
| **VM Options** | Zones | ["1"] (single zone) |
| **Storage** | Premium v2 | false |
| **Scale Sets** | Use scale sets | false |
| **Package Management** | Upgrade packages | false |
| **Naming** | Use prefix | true |
| **Naming** | Use zonal markers | true |
| **App Tier** | Sizing dictionary | "Optimized" |
| **SCS** | Instance numbers | "00", "01", "00" |
| **Tags** | Resource tags | {DeployedBy: "SDAF-ChatAgent"} |

---

## 5. Conversational Flow Design

### 5.1 Overall Approach
- Friendly, conversational tone (like talking to Claude)
- Accept free-form input (case-insensitive)
- Parse natural language responses
- Provide clear examples
- Group related parameters together
- Show context about what's being configured

### 5.2 Prompt-by-Prompt Flow

---

#### PROMPT 1: Environment Identity

**LLM Message:**
```
Hi! I'll help you create an SAP deployment configuration. Let's start with the basics about your environment.

First, I need to know three things:

1. What environment is this? (e.g., DEV, PROD, QA, NONPROD)
2. Which Azure region? (e.g., westeurope, eastus, northeurope)
3. What should we call your network? (This is a short identifier, max 7 characters, like SAP01 or SAP02)

You can answer in any format you like - just tell me these three things!

Examples:
- "This is DEV in westeurope, network name SAP01"
- "production, east us, network SAP02"
- "dev / west europe / sap01"
```

**What we extract:**
- `environment` (normalize to uppercase, max 5 chars)
- `location` (normalize to Azure region code)
- `network_logical_name` (normalize, max 7 chars)

**Validation:**
- Environment: alphanumeric, max 5 characters
- Location: must be valid Azure region
- Network name: alphanumeric, max 7 characters

**Fallback defaults:**
- If unclear, ask clarifying questions

---

#### PROMPT 2: SAP System Identity

**LLM Message:**
```
Great! So we're setting up a {ENVIRONMENT} environment in {LOCATION} with network {NETWORK_NAME}.

Now, let's identify your SAP system:

1. What's the SAP Application SID? (3 characters, like X00, S15, P01)
2. What's the Database SID? (usually 3 characters, like HDB, XDB, ORA)
3. Which database platform are you using?
   - HANA (SAP HANA)
   - DB2 (IBM DB2)
   - ORACLE (Oracle Database)
   - ASE (SAP ASE/Sybase)
   - SQLSERVER (Microsoft SQL Server)
   - NONE (no database tier)

Examples:
- "SID is X00, database HDB, using HANA"
- "app sid: P01, db sid: ORA, oracle database"
- "X00 / HDB / HANA"
```

**What we extract:**
- `sid` (3 chars, uppercase)
- `database_sid` (3 chars, uppercase)
- `database_platform` (normalize to: HANA, DB2, ORACLE, ASE, SQLSERVER, NONE)

**Validation:**
- SID: alphanumeric, exactly 3 characters
- Database SID: alphanumeric, typically 3 characters
- Database platform: must match valid options

---

#### PROMPT 3: System Sizing

**LLM Message:**
```
Perfect! We're deploying SAP {SID} with {DATABASE_PLATFORM} database ({DATABASE_SID}).

Now let's talk about sizing. I need to understand how big this system needs to be:

1. What's the primary purpose?
   - Demo/Testing (small, cost-optimized)
   - Development (small to medium)
   - QA/Staging (medium)
   - Production (medium to large)
   - Production with high load (large to extra-large)

2. For HANA database, what size do you need?
   - Demo: 32 GB memory (Standard_D8s_v3)
   - Small: 160-256 GB memory (E20ds_v4 or E32ds_v4)
   - Medium: 256-512 GB memory (E32ds_v4 or E64ds_v4)
   - Large: 512 GB - 1 TB memory (E64ds_v5 or M64s)
   - XLarge: 1-4 TB memory (M128s or M128ms)
   - XXLarge: 4+ TB memory (M208ms_v2 or larger)

Just tell me what you're aiming for, and I'll pick the right VM size!

Examples:
- "This is for development, medium size should be fine"
- "Production system, need large, around 1TB memory"
- "Demo environment, keep it small"
```

**What we extract:**
- `database_size` (map to sizing dictionary key)
- Implicit: `app_tier_sizing_dictionary_key` = "Optimized" (or "Production" based on purpose)

**Mapping logic:**
| User Intent | Database Size Key | App Tier Key |
|-------------|-------------------|--------------|
| Demo/Testing | "Demo" or "S4Demo" | "Default" |
| Development | "E20ds_v4" or "E32ds_v4" | "Optimized" |
| QA/Staging | "E32ds_v4" or "E48ds_v4" | "Optimized" |
| Production | "E64ds_v4" or "M64s" | "Production" |
| High-load Prod | "M128s" or larger | "Production" |

---

#### PROMPT 4: Architecture Pattern

**LLM Message:**
```
Got it - we'll size this for a {PURPOSE} workload with {SIZE_DESCRIPTION}.

Now, let's decide on the architecture:

1. **Deployment Type:**
   - Standalone: Everything on one server (simplest, good for dev/test)
   - Distributed: Separate servers for database, central services, and app servers (recommended for production)

2. **High Availability:**
   - Do you need HA/clustering for zero downtime? (yes/no)
   - Note: HA requires at least 2 servers for both database and central services

3. **Application Servers:**
   - If you choose Distributed, how many application servers do you need? (typically 1-4 for most systems)

Examples:
- "Standalone, no HA needed, this is just dev"
- "Distributed with 2 app servers, yes we need HA"
- "Distributed, 3 app servers, no HA for now"
```

**What we extract:**
- Architecture pattern: Standalone vs Distributed
- `database_high_availability` (true/false)
- `scs_high_availability` (true/false)
- `scs_server_count` (1 or 2 if HA)
- `application_server_count` (user-specified or 0 for standalone)
- `enable_app_tier_deployment` (false for standalone, true for distributed)

**Defaults we set:**
- Standalone pattern:
  - `enable_app_tier_deployment` = false
  - `scs_server_count` = 1
  - `application_server_count` = 0
  - HA = false

- Distributed without HA:
  - `enable_app_tier_deployment` = true
  - `scs_server_count` = 1
  - `application_server_count` = user input
  - `database_server_count` = 1
  - All HA settings = false

- Distributed with HA:
  - `enable_app_tier_deployment` = true
  - `scs_server_count` = 2
  - `scs_high_availability` = true
  - `database_server_count` = 2
  - `database_high_availability` = true
  - `application_server_count` = user input
  - Cluster settings = defaults (AFA, Premium_ZRS, etc.)

---

#### PROMPT 5: Network Configuration

**LLM Message:**
```
Excellent! We're going with a {ARCHITECTURE_TYPE} architecture{HA_STATEMENT}.

Now for the network setup - this is important:

**Are you deploying into:**
1. **Greenfield** - A new virtual network that SDAF will create for you
2. **Brownfield** - An existing virtual network that's already set up

**If Greenfield (recommended for new deployments):**
I'll create a new VNet with four subnets using these default address ranges:
- Admin subnet: 10.1.0.0/24
- Database subnet: 10.1.1.0/24
- Application subnet: 10.1.2.0/24
- Web subnet: 10.1.3.0/24

You can customize these or accept the defaults.

**If Brownfield (using existing network):**
I'll need the Azure Resource IDs for:
- The VNet
- Admin subnet
- Database subnet
- Application subnet
- Web subnet (optional)

What would you like to do?

Examples:
- "Greenfield please, defaults are fine"
- "Greenfield but use 10.10.x.x range"
- "Brownfield - I have the subnet IDs"
```

**What we extract:**

**Greenfield path:**
- `admin_subnet_address_prefix` (default or user-specified)
- `db_subnet_address_prefix` (default or user-specified)
- `app_subnet_address_prefix` (default or user-specified)
- `web_subnet_address_prefix` (default or user-specified)

**Brownfield path:**
- `network_arm_id`
- `admin_subnet_arm_id`
- `db_subnet_arm_id`
- `app_subnet_arm_id`
- `web_subnet_arm_id` (optional)
- Optionally: NSG ARM IDs

**Default subnet sizing (Greenfield):**
```
admin_subnet_address_prefix  = "10.1.0.0/24"
db_subnet_address_prefix     = "10.1.1.0/24"
app_subnet_address_prefix    = "10.1.2.0/24"
web_subnet_address_prefix    = "10.1.3.0/24"
```

**For Brownfield:** Collect ARM IDs through follow-up questions.

---

#### PROMPT 6: Operating System Selection

**LLM Message:**
```
Almost done! Last question - which operating system would you like to use?

SDAF supports these SAP-certified OS options:

**SUSE Linux Enterprise Server (SLES):**
- SLES 15 SP5 (latest, recommended)
- SLES 15 SP4
- SLES 15 SP3
- SLES 12 SP5

**Red Hat Enterprise Linux (RHEL):**
- RHEL 9.x (latest)
- RHEL 8.x (8.6, 8.4, 8.2)
- RHEL 7.x

Just tell me your preference - I'll configure the right image for all VMs (database, SCS, app servers).

Examples:
- "SUSE latest" → SLES 15 SP5
- "Red Hat 8" → RHEL 8.6
- "SLES 15 SP5" → SLES 15 SP5
- "RHEL 9" → RHEL 9.x
```

**What we extract:**
- OS family (SUSE vs RedHat)
- OS version

**What we set (all VMs get the same OS):**
```javascript
// For SLES 15 SP5:
database_vm_image = {
  os_type   = "LINUX"
  publisher = "SUSE"
  offer     = "sles-sap-15-sp5"
  sku       = "gen2"
  version   = "latest"
  type      = "marketplace"
}

scs_server_image = { ... same ... }
application_server_image = { ... same ... }
webdispatcher_server_image = { ... same ... }

// For RHEL 8.6:
database_vm_image = {
  os_type   = "LINUX"
  publisher = "RedHat"
  offer     = "RHEL-SAP-HA"
  sku       = "8.6"
  version   = "latest"
  type      = "marketplace"
}
```

**Mapping table:**
| User Input | Publisher | Offer | SKU |
|------------|-----------|-------|-----|
| SLES 15 SP5 | SUSE | sles-sap-15-sp5 | gen2 |
| SLES 15 SP4 | SUSE | sles-sap-15-sp4 | gen2 |
| SLES 12 SP5 | SUSE | sles-sap-12-sp5 | gen2 |
| RHEL 9 | RedHat | RHEL-SAP-HA | 9_0 |
| RHEL 8.6 | RedHat | RHEL-SAP-HA | 8.6 |
| RHEL 8.4 | RedHat | RHEL-SAP-HA | 8.4 |
| RHEL 7.9 | RedHat | RHEL-SAP-HA | 7.9 |

---

### 5.3 Final Summary & Generation

**LLM Message:**
```
Perfect! I have everything I need. Let me summarize your SAP deployment configuration:

**Environment:** {ENVIRONMENT} in {LOCATION}
**Network:** {NETWORK_LOGICAL_NAME}
**SAP System:** {SID} ({DATABASE_PLATFORM} database: {DATABASE_SID})
**Sizing:** {SIZE_DESCRIPTION} ({DATABASE_SIZE_KEY})
**Architecture:** {ARCHITECTURE_TYPE}{HA_STATEMENT}
**Servers:**
  - Database: {DB_COUNT} x {DB_VM_SIZE}
  - SCS: {SCS_COUNT} x {SCS_VM_SIZE}
  - Application: {APP_COUNT} x {APP_VM_SIZE}
**Network:** {GREENFIELD_OR_BROWNFIELD}
**Operating System:** {OS_DESCRIPTION}

I'm now generating your SDAF-compliant tfvars file...

[Generated tfvars content]

Would you like me to:
1. Save this to a file
2. Explain any of these settings
3. Adjust anything
4. Show you how to deploy this
```

---

## 6. Parameter Validation Rules

### 6.1 Format Validation

| Parameter | Regex/Rule | Example |
|-----------|------------|---------|
| `environment` | `^[A-Za-z0-9]{1,5}$` | "DEV", "PROD" |
| `location` | Valid Azure region | "westeurope", "eastus" |
| `network_logical_name` | `^\w{0,7}$` | "SAP01", "SAP02" |
| `sid` | `^\w{3}$` | "X00", "P01" |
| `database_sid` | `^\w{0,3}$` | "HDB", "XDB" |
| `web_sid` | `^\w{3}$` | "W00" |
| `*_subnet_address_prefix` | Valid CIDR | "10.1.0.0/24" |
| `*_arm_id` | Valid ARM resource ID | "/subscriptions/{guid}/..." |
| `*_instance_number` | `^\d{2}$` | "00", "01", "02" |
| `subscription_id` | Valid GUID | "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" |

### 6.2 Value Validation

| Parameter | Valid Values |
|-----------|--------------|
| `database_platform` | HANA, DB2, ORACLE, ORACLE-ASM, ASE, SQLSERVER, NONE |
| `database_cluster_type` | AFA, ASD, ISCSI |
| `scs_cluster_type` | AFA, ASD, ISCSI |
| `NFS_provider` | ANF, AFS, NFS, NONE |
| `database_vm_image.os_type` | LINUX, WINDOWS |
| `database_vm_image.type` | marketplace, custom |
| `*_authentication_type` | key, password |
| `patch_mode` | ImageDefault, AutomaticByPlatform, Manual |
| `*_disk_type` | Premium_LRS, Premium_ZRS, StandardSSD_LRS, UltraSSD_LRS |

### 6.3 Logical Validation

| Rule | Description |
|------|-------------|
| HA Server Count | If `*_high_availability` = true, then `*_server_count` >= 2 |
| Web Dispatcher SID | If `webdispatcher_server_count` > 0, then `web_sid` is required |
| Network Mode | Either provide subnet prefixes (Greenfield) OR ARM IDs (Brownfield), not both |
| ANF Dependencies | If any `ANF_HANA_*` = true, then `NFS_provider` must = "ANF" |
| Cluster Dependencies | If `*_high_availability` = true, then cluster_type and disk settings are required |
| Standalone Deployment | If `enable_app_tier_deployment` = false, then `application_server_count` = 0 |
| Instance Numbers | All instance numbers must be unique within a system |
| Zone Consistency | If using zones, ensure VMs are distributed across available zones |

### 6.4 Azure-Specific Validation

| Rule | Description |
|------|-------------|
| VM SKU Availability | Validate VM SKU is available in selected region |
| Subnet Size | Ensure subnet CIDR has enough IPs for all VMs + Azure reserved (5 per subnet) |
| Zone Support | Validate selected region supports Availability Zones |
| Premium Storage | Some VM sizes don't support Premium storage |
| Accelerated Networking | Validate VM size supports accelerated networking |

---

## 7. Complete Default Value Reference

### 7.1 Topology Defaults

```hcl
# Basic Topology
enable_app_tier_deployment = true
application_server_count   = 1
scs_server_count          = 1
database_server_count     = 1
webdispatcher_server_count = 0

# High Availability
database_high_availability = false
scs_high_availability     = false
```

### 7.2 Instance Numbers

```hcl
scs_instance_number = "00"
ers_instance_number = "01"
pas_instance_number = "00"
web_instance_number = "00"
# database_instance_number and app_instance_number typically not set
```

### 7.3 Sizing

```hcl
app_tier_sizing_dictionary_key = "Optimized"
# database_size = user-specified (required)
```

### 7.4 Networking

```hcl
database_vm_use_DHCP  = true
app_tier_use_DHCP     = true
dual_nics             = false
app_tier_dual_nics    = false
database_dual_nics    = false

use_loadbalancers_for_standalone_deployments = true
use_private_endpoint = true
use_service_endpoint = null
nsg_asg_with_vnet   = false

deploy_application_security_groups = true
```

### 7.5 VM Placement

```hcl
# Database
database_use_ppg   = false
database_use_avset = false
database_vm_zones  = ["1"]

# SCS
scs_server_use_ppg   = true
scs_server_use_avset = false
scs_server_zones     = ["1"]

# Application
application_server_use_ppg   = true
application_server_use_avset = true
application_server_zones     = ["1"]

# Web Dispatcher
webdispatcher_server_use_ppg   = false
webdispatcher_server_use_avset = true
webdispatcher_server_zones     = ["1"]
```

### 7.6 Clustering (HA)

```hcl
database_cluster_type      = "AFA"
database_cluster_disk_lun  = 8
database_cluster_disk_size = 128
database_cluster_disk_type = "Premium_ZRS"

scs_cluster_type      = "AFA"
scs_cluster_disk_lun  = 5
scs_cluster_disk_size = 128
scs_cluster_disk_type = "Premium_ZRS"

use_msi_for_clusters = true
use_simple_mount     = false

# Fence Kdump (disabled by default)
use_fence_kdump             = false
use_fence_kdump_size_gb_db  = 128
use_fence_kdump_lun_db      = 8
use_fence_kdump_size_gb_scs = 64
use_fence_kdump_lun_scs     = 4
```

### 7.7 Storage & NFS

```hcl
NFS_provider                       = "AFS"  # Azure Files
sapmnt_volume_size                 = 128    # GB
use_random_id_for_storageaccounts  = true
shared_access_key_enabled          = false
shared_access_key_enabled_nfs      = false
database_use_premium_v2_storage    = false
```

### 7.8 Azure NetApp Files

```hcl
ANF_HANA_use_AVG   = false
ANF_HANA_use_Zones = true

# Data volumes
ANF_HANA_data_volume_size       = 256  # GB
ANF_HANA_data_volume_throughput = 128  # MB/s
ANF_HANA_data_volume_count      = 1

# Log volumes
ANF_HANA_log_volume_size       = 128  # GB
ANF_HANA_log_volume_throughput = 128  # MB/s
ANF_HANA_log_volume_count      = 1
```

### 7.9 HANA Scale-Out

```hcl
database_HANA_use_scaleout_scenario    = false
database_HANA_no_standby_role          = false
stand_by_node_count                    = 0
database_HANA_use_ANF_scaleout_scenario = false
```

### 7.10 Authentication & Security

```hcl
database_vm_authentication_type = "key"
app_tier_authentication_type    = "key"
enable_purge_control_for_keyvaults = false
use_spn = false  # Use MSI by default
```

### 7.11 Monitoring & Extensions

```hcl
deploy_monitoring_extension    = false
deploy_v1_monitoring_extension = false
deploy_defender_extension      = false
enable_ha_monitoring          = false
enable_os_monitoring          = false
```

### 7.12 VM Configuration

```hcl
patch_mode            = "ImageDefault"
patch_assessment_mode = "ImageDefault"
use_scalesets_for_deployment = false
upgrade_packages = false
use_secondary_ips = false
```

### 7.13 Naming & Tagging

```hcl
use_prefix         = true
use_zonal_markers  = true
resource_offset    = 0
save_naming_information = false

tags = {
  DeployedBy = "SDAF-ChatAgent"
}
```

### 7.14 DNS

```hcl
dns_a_records_for_secondary_names = true
register_endpoints_with_dns       = true
```

### 7.15 Resource Management

```hcl
prevent_deletion_if_contains_resources = true
```

---

## 8. Conversation Flow Examples

### Example 1: Simple Development System

**User Journey:**

**Prompt 1:**
- User: "dev environment, west europe, network sap01"
- Extracted: environment="DEV", location="westeurope", network_logical_name="SAP01"

**Prompt 2:**
- User: "SID is D01, database HDB, using HANA"
- Extracted: sid="D01", database_sid="HDB", database_platform="HANA"

**Prompt 3:**
- User: "development system, keep it small"
- Mapped: database_size="Demo", app_tier_sizing_dictionary_key="Default"

**Prompt 4:**
- User: "standalone is fine, no HA needed"
- Set: enable_app_tier_deployment=false, all HA=false, scs_server_count=1

**Prompt 5:**
- User: "greenfield, defaults are good"
- Set: All subnet prefixes to defaults (10.1.x.x/24)

**Prompt 6:**
- User: "SUSE latest"
- Set: All VM images to SLES 15 SP5

**Result:** Minimal 1-VM standalone SAP system for development.

---

### Example 2: Production HA System

**User Journey:**

**Prompt 1:**
- User: "production, east us 2, network SAP02"
- Extracted: environment="PROD", location="eastus2", network_logical_name="SAP02"

**Prompt 2:**
- User: "Application SID is P01, database PRD, HANA platform"
- Extracted: sid="P01", database_sid="PRD", database_platform="HANA"

**Prompt 3:**
- User: "production workload, need large size, around 1 TB memory"
- Mapped: database_size="M64s" (1TB M-series), app_tier_sizing_dictionary_key="Production"

**Prompt 4:**
- User: "distributed with HA, 3 application servers"
- Set:
  - enable_app_tier_deployment=true
  - database_high_availability=true, database_server_count=2
  - scs_high_availability=true, scs_server_count=2
  - application_server_count=3
  - All cluster defaults (AFA, Premium_ZRS, etc.)

**Prompt 5:**
- User: "brownfield, here are the IDs: [provides subnet ARM IDs]"
- Set: All *_arm_id parameters with user-provided values

**Prompt 6:**
- User: "Red Hat 8.6"
- Set: All VM images to RHEL-SAP-HA 8.6

**Result:** Enterprise-grade HA SAP system with 2 DB nodes, 2 SCS nodes, 3 app servers.

---

### Example 3: Staged Conversation with Clarifications

**Prompt 1:**
- User: "I want to deploy SAP in Azure"
- Agent: "Great! Let me help you configure that. First, what environment is this - development, production, or something else? And which Azure region would you like to use?"
- User: "dev in west europe"
- Agent: "Perfect. And what should we call your network? This is a short identifier like SAP01 or SAP02."
- User: "SAP01"
- Extracted: environment="DEV", location="westeurope", network_logical_name="SAP01"

**Prompt 2:**
- User: "S/4HANA system"
- Agent: "Got it, S/4HANA. What's the 3-character SID you'd like to use? For example, S01, S15, or X00."
- User: "S01"
- Agent: "And the database SID? This is typically HDB for HANA."
- User: "HDB is fine"
- Extracted: sid="S01", database_sid="HDB", database_platform="HANA"

[Continues with natural back-and-forth...]

---

## 9. Parameter Grouping for Advanced Mode

If you later want to build an "Advanced Mode" with more control, here's how to group parameters:

### Group 1: Basic Identity (7)
- environment, location, network_logical_name, sid, database_sid, web_sid, Description

### Group 2: Database Configuration (12)
- database_platform, database_size, database_server_count, database_high_availability, database_vm_zones, database_instance_number, database_vm_use_DHCP, database_use_ppg, database_use_avset, database_dual_nics, database_use_premium_v2_storage, custom_disk_sizes_filename

### Group 3: Database VM Image (7)
- All database_vm_image.* parameters

### Group 4: Application Tier (15)
- enable_app_tier_deployment, app_tier_sizing_dictionary_key, app_tier_use_DHCP, app_tier_dual_nics, application_server_count, application_server_zones, application_server_use_ppg, application_server_use_avset, etc.

### Group 5: SCS Configuration (16)
- scs_server_count, scs_high_availability, scs_instance_number, ers_instance_number, pas_instance_number, scs_server_zones, scs_server_use_ppg, scs_server_use_avset, etc.

### Group 6: Web Dispatcher (13)
- All webdispatcher_* parameters

### Group 7: High Availability (18)
- All cluster parameters, fencing, kdump settings

### Group 8: Networking - Greenfield (4)
- Subnet address prefixes

### Group 9: Networking - Brownfield (21)
- All ARM IDs for existing resources

### Group 10: Networking - Advanced (4)
- nsg_asg_with_vnet, dual_nics, use_loadbalancers_for_standalone_deployments, use_private_endpoint

### Group 11: NFS & Storage (8)
- NFS_provider, sapmnt_volume_size, use_random_id_for_storageaccounts, shared_access_key settings

### Group 12: Azure NetApp Files (22)
- All ANF_* parameters

### Group 13: HANA Scale-Out (4)
- database_HANA_use_scaleout_scenario, database_HANA_no_standby_role, stand_by_node_count, database_HANA_use_ANF_scaleout_scenario

### Group 14: Security & Auth (11)
- All authentication, Key Vault, encryption parameters

### Group 15: Monitoring & Extensions (9)
- All monitoring and extension parameters

### Group 16: Resource Management (11)
- Subscription, resource group, tags, naming settings

### Group 17: Advanced VM Options (6)
- use_secondary_ips, use_scalesets_for_deployment, upgrade_packages, patch settings

### Group 18: DNS & Miscellaneous (5)
- DNS settings, BOM, configuration settings

---

## 10. Implementation Recommendations

### 10.1 Natural Language Processing

**Input Normalization:**
```python
# Environment
"dev" | "DEV" | "development" → "DEV"
"prod" | "production" | "prd" → "PROD"
"qa" | "quality" | "test" → "QA"
"nonprod" | "non-prod" | "np" → "NP"

# Location
"west europe" | "westeurope" | "West Europe" → "westeurope"
"east us" | "eastus" | "East US" → "eastus"

# Database Platform
"hana" | "HANA" | "sap hana" | "SAP HANA" → "HANA"
"oracle" | "Oracle" | "Oracle DB" → "ORACLE"
"sql server" | "sqlserver" | "mssql" → "SQLSERVER"

# Boolean responses
"yes" | "y" | "true" | "sure" | "yeah" → true
"no" | "n" | "false" | "nope" → false
```

**Pattern Matching:**
Use regex and fuzzy matching to extract structured data from free-form responses:
```python
# Extract SIDs from natural text
"SID is X00, database HDB" → sid="X00", database_sid="HDB"
"app: P01 / db: PRD" → sid="P01", database_sid="PRD"

# Extract sizing intent
"small" | "demo" | "testing" → Demo/S4Demo size
"medium" | "moderate" → E32ds_v4/E48ds_v4
"large" | "big" | "1TB" | "1 TB" → M64s
"extra large" | "xlarge" | "2TB" → M128s
```

### 10.2 Validation Strategy

**Three-tier validation:**

1. **Syntax Validation** (immediate)
   - Format checks (regex)
   - Length constraints
   - Character restrictions

2. **Semantic Validation** (during conversation)
   - Valid values from enum
   - Logical consistency
   - Cross-parameter dependencies

3. **Azure Validation** (pre-deployment)
   - Region/SKU availability
   - Quota checks
   - Subnet IP capacity
   - Resource naming conflicts

### 10.3 Error Handling

**User-friendly error messages:**

Bad:
```
Error: Invalid value for parameter 'database_platform'. Must be one of: HANA, DB2, ORACLE, ASE, SQLSERVER, NONE.
```

Good:
```
I didn't recognize that database platform. The options are:
- HANA (SAP HANA)
- Oracle (Oracle Database)
- SQL Server (Microsoft SQL Server)
- DB2 (IBM DB2)
- ASE (SAP ASE/Sybase)

Which one would you like to use?
```

### 10.4 Conversation State Management

Store conversation state as structured data:

```json
{
  "conversation_id": "uuid",
  "current_prompt": 3,
  "completed_prompts": [1, 2],
  "extracted_params": {
    "environment": "DEV",
    "location": "westeurope",
    "network_logical_name": "SAP01",
    "sid": "D01",
    "database_sid": "HDB",
    "database_platform": "HANA"
  },
  "pending_clarifications": [],
  "user_intent": {
    "deployment_type": "development",
    "size_preference": "small",
    "ha_required": false
  }
}
```

### 10.5 Template Generation

**Final tfvars output should:**
1. Include all user-specified parameters
2. Add all default parameters with comments explaining them
3. Group related parameters together
4. Include inline documentation
5. Show calculated/derived values

Example output structure:
```hcl
#######################################################
# SAP System Configuration
# Generated by SDAF Chat Agent
# Date: 2025-01-15
#######################################################

#######################################################
# Environment Identity
#######################################################
environment          = "DEV"
location             = "westeurope"
network_logical_name = "SAP01"

#######################################################
# SAP System Identity
#######################################################
sid              = "D01"
database_sid     = "HDB"
database_platform = "HANA"
Description      = "Development SAP system deployed via chat agent"

#######################################################
# Database Tier Configuration
#######################################################
database_size          = "Demo"
database_server_count  = 1
database_high_availability = false
# ... etc
```

---

## 11. SDAF Architecture Context

For the chat agent to provide helpful guidance, it should understand the SDAF deployment hierarchy:

### 11.1 SDAF Components

1. **Control Plane** (must be deployed first)
   - Deployer VM (executes Terraform/Ansible)
   - SAP Library (stores state files, installation media, BOM files)
   - Key Vault (stores deployment credentials)

2. **Workload Zone** (depends on Control Plane)
   - Virtual Network
   - Key Vault for system credentials
   - Storage accounts for shared files
   - Represents an environment tier (DEV/QA/PROD)

3. **SAP System** (depends on Workload Zone) ← **THIS IS WHAT WE'RE GENERATING**
   - Database tier
   - Application tier
   - Web dispatcher tier

### 11.2 Prerequisites the User Must Have

Before generating the System tfvars, the user should have:
1. Control Plane deployed
2. Workload Zone deployed for the target environment
3. SAP installation media uploaded to SAP Library
4. Bill of Materials (BOM) file prepared

The chat agent could ask about these prerequisites and provide guidance if missing.

---

## 12. Sample Generated tfvars File

Based on Example 1 (Simple Dev System):

```hcl
#######################################################
# SAP System Configuration - Development System
# Environment: DEV
# Location: westeurope
# Network: SAP01
# System: D01 (HANA)
# Generated: 2025-01-15 by SDAF Chat Agent
#######################################################

#######################################################
# Environment Identity
#######################################################
environment          = "DEV"
location             = "westeurope"
network_logical_name = "SAP01"

#######################################################
# SAP System Identity
#######################################################
sid              = "D01"
database_sid     = "HDB"
database_platform = "HANA"
Description      = "Development HANA system - standalone deployment"

#######################################################
# Database Tier Configuration
#######################################################
database_size                      = "Demo"  # Standard_D8s_v3, 32 GB RAM
database_server_count              = 1
database_high_availability         = false
database_vm_use_DHCP              = true
database_use_ppg                  = false
database_use_avset                = false
database_vm_zones                 = ["1"]
database_use_premium_v2_storage   = false

#######################################################
# Database VM Image
#######################################################
database_vm_image = {
  os_type   = "LINUX"
  publisher = "SUSE"
  offer     = "sles-sap-15-sp5"
  sku       = "gen2"
  version   = "latest"
  type      = "marketplace"
}

#######################################################
# Application Tier Configuration
# Note: Standalone deployment - app tier disabled
#######################################################
enable_app_tier_deployment = false
application_server_count   = 0

#######################################################
# SAP Central Services (SCS)
#######################################################
scs_server_count       = 1
scs_high_availability  = false
scs_instance_number    = "00"
ers_instance_number    = "01"
pas_instance_number    = "00"
scs_server_use_ppg     = true
scs_server_use_avset   = false
scs_server_zones       = ["1"]

scs_server_image = {
  os_type   = "LINUX"
  publisher = "SUSE"
  offer     = "sles-sap-15-sp5"
  sku       = "gen2"
  version   = "latest"
  type      = "marketplace"
}

#######################################################
# Web Dispatcher
# Note: Not deployed for this system
#######################################################
webdispatcher_server_count = 0

#######################################################
# Networking - Greenfield Deployment
#######################################################
admin_subnet_address_prefix = "10.1.0.0/24"
db_subnet_address_prefix    = "10.1.1.0/24"
app_subnet_address_prefix   = "10.1.2.0/24"
web_subnet_address_prefix   = "10.1.3.0/24"

#######################################################
# Networking - Advanced Settings
#######################################################
use_loadbalancers_for_standalone_deployments = true
use_private_endpoint                         = true
deploy_application_security_groups          = true
nsg_asg_with_vnet                           = false

#######################################################
# NFS / Shared Storage
#######################################################
NFS_provider                      = "AFS"  # Azure Files
sapmnt_volume_size                = 128    # GB
use_random_id_for_storageaccounts = true

#######################################################
# High Availability & Clustering
# Note: HA disabled for this system
#######################################################
use_msi_for_clusters = true
use_simple_mount     = false

#######################################################
# Authentication
#######################################################
database_vm_authentication_type = "key"
app_tier_authentication_type    = "key"

#######################################################
# Monitoring & Extensions
#######################################################
deploy_monitoring_extension    = false
deploy_v1_monitoring_extension = false
deploy_defender_extension      = false
enable_ha_monitoring           = false
enable_os_monitoring           = false

#######################################################
# VM Configuration
#######################################################
patch_mode                    = "ImageDefault"
patch_assessment_mode         = "ImageDefault"
use_scalesets_for_deployment = false
upgrade_packages             = false
use_secondary_ips            = false

#######################################################
# Naming & Tagging
#######################################################
use_prefix        = true
use_zonal_markers = true
resource_offset   = 0

tags = {
  DeployedBy   = "SDAF-ChatAgent"
  Environment  = "DEV"
  System       = "D01"
  DeploymentDate = "2025-01-15"
}

#######################################################
# DNS
#######################################################
dns_a_records_for_secondary_names = true
register_endpoints_with_dns       = true

#######################################################
# Resource Management
#######################################################
prevent_deletion_if_contains_resources = true
```

---

## 13. Additional Recommendations

### 13.1 Progressive Disclosure

Don't overwhelm users with all options upfront. Start simple, then offer advanced customization:

After generating the basic tfvars:
```
I've created your configuration with sensible defaults. Would you like to customize any of these advanced settings?

- High Availability clustering options
- Azure NetApp Files for storage
- Custom VM sizes
- Network security groups
- Monitoring extensions
- Custom disk configurations

Just ask if you want to tweak anything, or we can proceed with this configuration!
```

### 13.2 Validation Checkpoints

Before generating final tfvars:
```
Let me verify a few things about your deployment:

✓ Region 'westeurope' supports Availability Zones
✓ VM size 'Standard_D8s_v3' is available in westeurope
✓ SLES 15 SP5 image is available
✓ Subnet CIDR 10.1.1.0/24 has 251 usable IPs (enough for 1 DB server + Azure reserved)

Everything looks good! Ready to generate your tfvars file.
```

### 13.3 Post-Generation Assistance

After generating tfvars:
```
Your configuration is ready! Here's what to do next:

1. **Save the file**: Save this as DEV-WEEU-SAP01-D01.tfvars

2. **Review the configuration**: Make sure the settings match your expectations

3. **Deploy the system**:
   ```bash
   ${DEPLOYMENT_REPO_PATH}/deploy/scripts/installer.sh \
     --parameterfile DEV-WEEU-SAP01-D01.tfvars \
     --type sap_system \
     --auto-approve
   ```

4. **Monitor deployment**: This will take 20-30 minutes

Need help with any of these steps? Just ask!
```

### 13.4 Preset Templates

Offer common presets for quick deployment:

```
Would you like to use a preset template?

1. **Dev/Test Starter**: Standalone, small HANA (Demo), SLES, no HA
2. **Production Standard**: Distributed, medium HANA (E64ds_v4), HA enabled, 2 app servers
3. **Production Enterprise**: Distributed, large HANA (M128s), HA enabled, 4 app servers
4. **Custom**: Walk through all options (what we've been doing)

Choose a preset to quickly customize, or continue with custom configuration.
```

### 13.5 Learning Mode

Offer to explain what's being configured:

```
🎓 Learning Mode: Would you like me to explain what each setting does as we go?

For example, I can explain:
- What Proximity Placement Groups do and when to use them
- How Availability Zones improve reliability
- What the different cluster types (AFA, ASD, ISCSI) mean
- How DHCP vs static IPs affect your deployment

Toggle this on/off anytime!
```

---

## 14. Summary of Key Findings

### Parameter Statistics
- **Total parameters identified**: 200+
- **Absolutely required**: 7 (environment, location, network_logical_name, sid, database_sid, database_platform, database_size)
- **Contextually required**: 15-20 (depends on deployment type)
- **Optional with defaults**: 180+
- **HANA sizing options**: 46 predefined VM SKUs
- **App tier sizing options**: 3 profiles

### Easy Mode Design
- **Number of prompts**: 6
- **Average time to complete**: 3-5 minutes
- **Parameters collected from user**: 10-12
- **Parameters auto-defaulted**: 188-190
- **Deployment patterns supported**: Standalone, Distributed, HA
- **Network modes supported**: Greenfield, Brownfield

### Validation Complexity
- **Format validations**: 15+ regex patterns
- **Value validations**: 10+ enum checks
- **Logical validations**: 20+ cross-parameter rules
- **Azure-specific validations**: 5+ cloud-aware checks

---

## 15. Next Steps for Implementation

1. **Build NLP parser** to extract structured data from free-form responses
2. **Implement conversation state machine** to manage 6-prompt flow
3. **Create validation engine** with three-tier validation strategy
4. **Design template generator** to produce SDAF-compliant tfvars
5. **Build default value resolver** to apply 180+ defaults intelligently
6. **Implement Azure validation layer** for SKU/region/quota checks
7. **Create preset library** for common deployment patterns
8. **Add explanation engine** for learning mode
9. **Build deployment assistant** for post-generation guidance

---

## 16. References & Resources

### Official Documentation
- Microsoft Learn: https://learn.microsoft.com/en-us/azure/sap/automation/
- SDAF GitHub Repo: https://github.com/Azure/sap-automation
- Sample Configs: https://github.com/Azure/SAP-automation-samples

### Key Files Analyzed
- System tfvars example: `/WORKSPACES/SYSTEM/DEV-WEEU-SAP01-X00/DEV-WEEU-SAP01-X00.tfvars`
- SystemModel class: `/Webapp/SDAF/Models/SystemModel.cs`
- HANA sizing config: `/deploy/configs/hana_sizes.json`
- App sizing config: `/deploy/configs/app_sizes.json`

### Deployment Documentation
- System deployment: https://learn.microsoft.com/en-us/azure/sap/automation/deploy-system
- System configuration: https://learn.microsoft.com/en-us/azure/sap/automation/configure-system
- Naming conventions: https://learn.microsoft.com/en-us/azure/sap/automation/naming
- Architecture planning: https://learn.microsoft.com/en-us/azure/sap/automation/plan-deployment

---

**END OF REPORT**

*This research report provides comprehensive analysis for building a conversational chat agent that generates SDAF-compliant tfvars files. The 6-prompt conversational flow balances simplicity with completeness, asking users only essential questions while intelligently applying 180+ default values.*
