# Practice 5: SNMP

## Lab Layout
This is the `EVE-NG` lab layout, where `cloud2` is directly attached to `vnic2`

![alt text](attachments/lab_layout_eve.png)

### IP Addressing

| Device        | Interface       | IP            | OSPF ID | OSPF Area |
|---------------|-----------------|---------------|---------|-----------|
| ubuntu-server | `ens19`/`vnic1` | 10.10.3.10/24 | NA      | NA        |
| R1            | `l0`            | 1.1.1.1       | 100     | 0         |
|               | `e1/0`          | 10.10.3.1/24  | 100     | 0         |
|               | `e1/2`          | 30.30.3.1/24  | 100     | 0         |
|               | `e1/3`          | 20.20.3.1/24  | 100     | 0         |
| R2            | `l0`            | 2.2.2.2       | 100     | 0         |
|               | `e1/0`          | 40.40.3.1/24  | 100     | 0         |
|               | `e1/1`          | 20.20.3.2/24  | 100     | 0         |
| R3            | `l0`            | 3.3.3.3       | 100     | 0         |
|               | `e1/1`          | 30.30.3.2/24  | 100     | 0         |
|               | `e1/2`          | 40.40.3.2/24  | 100     | 0         |

### Prerequisites
* Routers:
    - IPs assigned.
    - Loopback 0 interface.
    - Routing Protocol (Ex. OSPF)
    - Connectivity
    - Cloud Network attached to `vnic` at the same LAN that `ubuntu` VM.
* Ubuntu:
    - Python 3
    - Minimum of 2 NICs
    - Netplan configured
    - Connectivity to the routers.
    - Docker

File Structure:
```
.
├── attachments
│   ├── lab_layout_cacti.drawio
│   ├── lab_layout_cacti.png
│   ├── lab_layout_eve.png
│   ├── lab_layout_snmp_app.drawio
│   └── lab_layout_snmp_app.png
├── automation
├── cacti
│   └── docker-compose.yaml
└── README.md
```

### Ubuntu

By connecting our `ubuntu` VM we need to add the following configuration to `netplan`.
We have 2 NICs, `ens18` and `ens19`, where `ens18` is the NIC bridged to my home network, receiving IP from DHCP, and finally `ens19` that is `vnic1` with IP `10.10.3.10` directly connected at the same lan that `vnic2` from `eve-ng` VM, also I added some routes, to access to the `loopback0` of each router by using `R1` as gateway with IP `10.10.3.1`.

Content of `/etc/netplan/00-installer-config.yaml`:
```yaml
# This is the network config written by 'subiquity'
network:
  ethernets:
    ens18:
      dhcp4: true
    ens19:
      addresses:
      - 10.10.3.10/24
      nameservers:
        addresses: []
        search: []
      routes:
        - to: 1.1.1.1/32
          via: 10.10.3.1
        - to: 2.2.2.2/32
          via: 10.10.3.1
        - to: 3.3.3.3/32
          via: 10.10.3.1
  version: 2
```

## Cacti
This is the layout at `proxmox` hypervisor.

![alt text](attachments/lab_layout_cacti.png)

> Note: `nic` are physical `NICs` and `vnic` are `Virtual NICs`

### Installation
To deploy `cacti` server I used `docker` containers, because why not.

Content of `cacti/docker-compose.yaml`:
```yaml
services:
  cacti:
    image: "smcline06/cacti:1.2.17"
    container_name: cacti
    domainname: example.com
    hostname: cacti
    ports:
      - "80:80"
      - "443:443"
      - "161:161/udp"
    environment:
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASS=${DB_PASS}
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_ROOT_PASS=${MYSQL_ROOT_PASSWORD}
      - INITIALIZE_DB=${INITIALIZE_DB}
      - TZ=${TZ}
    volumes:
      - cacti-data:/cacti
      - cacti-spine:/spine
      - cacti-backups:/backups
    links:
      - db

  db:
    image: "mariadb:10.3"
    container_name: cacti_db
    domainname: example.com
    hostname: db
    ports:
      - "3306:3306"
    command:
      - mysqld
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --max_connections=200
      - --max_heap_table_size=128M
      - --max_allowed_packet=32M
      - --tmp_table_size=128M
      - --join_buffer_size=128M
      - --innodb_buffer_pool_size=1G
      - --innodb_doublewrite=ON
      - --innodb_flush_log_at_timeout=3
      - --innodb_read_io_threads=32
      - --innodb_write_io_threads=16
      - --innodb_buffer_pool_instances=9
      - --innodb_file_format=Barracuda
      - --innodb_large_prefix=1
      - --innodb_io_capacity=5000
      - --innodb_io_capacity_max=10000
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - TZ=${TZ}
    volumes:
      - cacti-db:/var/lib/mysql

volumes:
  cacti-db:
  cacti-data:
  cacti-spine:
  cacti-backups:
```

Content of `cacti/.env`:
```shell
DB_NAME=cacti_master
DB_USER=cactiuser
DB_PASS=cactipassword
DB_HOST=db
DB_PORT=3306
MYSQL_ROOT_PASSWORD=rootpassword
INITIALIZE_DB=1
TZ=America/Mexico_City
```

### Routers
Set up routers to enable `SNMPv2`.

Get into privileged mode.
```
enable
```

Get into config mode.
```
configure terminal
```

Enable `SNMPv2`.
```
snmp-server community equipo3 RW
```

Enable `cacti-server` as SNMP Server.
```
snmp-server host 10.10.3.10 version 2c equipo3
```
Where:
- `10.10.3.10` is IP for `cacti-server`
- `2c` version of `SNMP`
- `equipo3` community string.

### Add Device to Cacti
Go to homepage and click on `Create`, then click on `New Device`.
And fill the form:
![alt text](attachments/image.png)

### Add Graphs for Device in Cacti
Go to homepage and click on `Create`, then click on `New Graph`.
And fill the form:
![alt text](attachments/image-1.png)

### Add Tree for devices' graphs
Go to homepage and click on `Management`, then click on `Trees`.
Then click on `+` to add a tree.
And fill the form:
![alt text](attachments/image-2.png)

Once created, edit the tree, click on `Add Root Branch` and drag the device and their graphs inside the `Root Branch`. Also mark as `on` `Publish` field:
![alt text](attachments/image-3.png)

Click on `Finish Editing Tree` to save the changes,

### View your graphs
Go to `Graphs` section and expand the `R1` tree > `R1` > `R1`. You will be able to see the device's graphs.
![alt text](attachments/image-4.png)

### Add `cacti-server` to monitor by itself
By default the `cacti-server` (localhost) is added.
You can consult the graphs by going to `Graphs` section and expand the `Default Tree` > `Local` > `Machine` > `Local Linux Machine`. You will be able to see the `cacti-server`'s graphs.
![alt text](attachments/image-5.png)

### Analyze Packet Capture (SNMP)

Start the capture over the nic attached to the routers.
```shell
tshark -i ens19 -w ./snmpv2.pcapng
```
Wait few seconds and stop the capture by pressing `CTRL-C`.

Then open the generated file `syslog.pcapng` with `wireshark`.

This is the content of one of the `SNMP` packets.
![alt text](attachments/image-7.png)

Here you can see many data fields of `SNMP` such as:
- `version`: `SNMP` version
- `community`: String identifier for `SNMP`
- `get-response`: Response from client
    * `variable-blindings`: `OIDs` Items
        - `item`: `OID` Item
            * `Object Name`: `1.3.6.1.2.1.1.3.0`: `OID` Name
            * `Value`: `706324`: `OID` Value

### Conclusion

This practice successfully demonstrated the potential of Docker containers for deploying network monitoring tools like Cacti. The process involved:

* **Deploying Cacti in a Docker container:** This showcased the individual's understanding of containerization and its advantages for application deployment.
* **Enabling SNMP v2 on Cisco routers:** This granted Cacti access to valuable network data through SNMP.
* **Integrating network devices into Cacti:** The individual successfully integrated network devices into Cacti, allowing for centralized monitoring and data collection via SNMP.
* **Creating interface graphs:**  Interface graphs were created within Cacti, providing a visual representation of network traffic and performance.
* **Analyzing a pcapng capture containing SNMP data:** The ability to interpret network communication at a deeper level was demonstrated through the analysis of a pcapng capture containing SNMP data.

This combination of skills equips the individual to effectively monitor and analyze network performance using modern tools and techniques. This knowledge can be leveraged for troubleshooting network issues, optimizing resource allocation, and ensuring network health.

By continuing to explore and refine these skills, the individual can become a valuable asset in maintaining and optimizing network performance.

## Automation
This is the layout at `proxmox` hypervisor.

![alt text](attachments/lab_layout_snmp_app.png)

> Note: `nic` are physical `NICs` and `vnic` are `Virtual NICs`

