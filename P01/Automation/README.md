# Web Router Interfaces Info

## Prerequisites
- Connectivity between your host and the routers
- `netmiko`, `flask` and `python-dotenv` installed
- SSH enabled on all routers
- Secret enabled to get into privileged mode.
- `.env` file. Refer to [.env.example](/.env.example) file.
- `inventory.yaml` file.

## Enable SSH into your Routers

Set a hostname
```
hostname <hostname>
```

Set a Domain Name
```
ip domain-name cisco.local
```

Generate a RSA key
```
crypto key generate rsa
```
Then write the size of `2048`

Enable SSH version 2
```
ip ssh version 2
```

Get into `line vty 0 4`
```
line vty 0 4
transport input ssh
login local
exit
```

Add a user:
```
username cisco password cisco123
```

Enable a secret for privileged mode
```
enable secret cisco123
```

## Inventory File
This script requires an inventory file, that contains the `ip` and `name` information about the routers that you want to use.

`inventory.yaml`:
```yaml
routers:
  - name: R1 GDL
    ip: "1.1.1.1"
  - name: R2 Monterrey
    ip: "2.2.2.2"
  - name: R3 CDMX
    ip: "3.3.3.3"
```