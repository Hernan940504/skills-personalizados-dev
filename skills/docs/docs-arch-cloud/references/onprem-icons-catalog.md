# Catálogo OnPremise — íconos disponibles

Para infraestructura on-premise (data centers corporativos, redes internas)
usamos shapes nativos de draw.io: `mxgraph.networks.*`, cilindro para BDs,
actor para usuarios. Estos íconos están en cualquier instalación de draw.io
sin dependencias externas.

---

## Compute / Servers

| `type` | Uso | Tag |
|---|---|---|
| `server` | Servidor genérico | Server |
| `application_server` | Servidor de aplicación | Application Server |
| `web_server` | Servidor web | Web Server |
| `mainframe` | Mainframe | Mainframe |
| `virtual_machine` | VM | Virtual Machine |
| `container` | Host de contenedores (Docker, K8s on-prem) | Container Host |

## Storage

| `type` | Uso | Tag |
|---|---|---|
| `database` | Base de datos relacional/NoSQL | Database (cilindro) |
| `file_server` | Servidor de archivos | File Server |
| `nas` | Network Attached Storage | NAS |
| `san` | Storage Area Network | SAN |
| `backup` | Sistema de backup / tape library | Backup |
| `storage_array` | Cabina de almacenamiento | Storage Array |

## Network

| `type` | Uso | Tag |
|---|---|---|
| `router` | Router | Router |
| `switch` | Switch | Switch |
| `load_balancer` | Balanceador hardware (F5, A10) | Load Balancer |
| `gateway` | Gateway / API Gateway físico | Gateway |
| `modem` | Modem | Modem |
| `wireless_ap` | Access Point Wi-Fi | Wireless AP |
| `proxy` | Reverse proxy / forward proxy | Proxy Server |
| `api_gateway` | API Gateway local | API Gateway |
| `message_broker` | Broker de mensajería (Kafka, RabbitMQ self-hosted) | Message Broker |

## Security

| `type` | Uso | Tag |
|---|---|---|
| `firewall` | Firewall | Firewall |
| `ids` | Intrusion Detection System | IDS |
| `ips` | Intrusion Prevention System | IPS |
| `vpn` | VPN Gateway | VPN Gateway |

## Users / Clients

| `type` | Uso | Tag |
|---|---|---|
| `user` | Un usuario | User |
| `users` | Múltiples usuarios | Users |
| `workstation` | Estación de trabajo | Workstation |
| `laptop` | Laptop | Laptop |
| `mobile` | Dispositivo móvil | Mobile Device |
| `browser` | Navegador | Browser |
| `printer` | Impresora | Printer |

## Generic

| `type` | Uso | Tag |
|---|---|---|
| `service` | Servicio genérico | Service |
| `component` | Componente lógico | Component |
| `system` | Sistema | System |
| `internet` | Símbolo Internet | Internet |
| `cloud` | Cloud genérica | Cloud |

Los íconos llevan automáticamente la etiqueta `[Tag]` o `[Tag: technology]`
en el label si se da el campo `technology`.

---

## Grupos (boundaries)

| `type` | Uso |
|---|---|
| `data_center` | Data center / sitio físico |
| `dmz` | Zona desmilitarizada |
| `internal_network` | Red interna |
| `rack` | Rack físico |
| `vlan` | VLAN específica |
| `zone` | Zona genérica (HA, replicación, etc.) |
| `system` | Sistema lógico que agrupa componentes |
| `site` | Sitio físico (sucursal, oficina) |

### Anidamiento típico

```
data_center "DC Bogotá"
├── dmz "DMZ"
│   ├── firewall
│   ├── load_balancer
│   └── proxy
└── internal_network "Red Interna"
    ├── vlan "VLAN Web"
    ├── vlan "VLAN App"
    └── vlan "VLAN Data"
```

---

## Tips para que el diagrama luzca bien

- **Modela siempre la DMZ como grupo aparte** — separa la red expuesta de la
  red interna. Los firewalls van en el límite entre las dos.
- **VLANs por capa**: web / app / data (red de tres capas clásica).
- **Bases de datos** en VLAN data, NUNCA en la DMZ.
- **Replicación / HA**: modela la BD primaria y la standby como dos
  `database`, con relación `async:true` etiquetada (Data Guard, replicación
  síncrona, etc.).
- **Sitios remotos** (sucursales, DR site): usa grupos `site` separados
  conectados por `vpn`.
- **Trafico east-west vs north-south**: las flechas que cruzan firewalls/DMZ
  son north-south; las internas (app→db, app→nas) son east-west.

---

## Cómo elegir el tipo correcto

- ¿Es un servidor general? → `server`.
- ¿Es un servidor web (nginx/Apache)? → `web_server`.
- ¿Es un servidor de aplicaciones (Tomcat, WebLogic)? → `application_server`.
- ¿Es una BD persistente? → `database` (renderiza como cilindro).
- ¿Es un message broker / cola? → `message_broker`.
- ¿Es un firewall físico? → `firewall`. ¿Es IDS/IPS específico? → `ids` / `ips`.
- ¿Es un usuario humano? → `user` / `users` / `workstation`.

Si la lista no cubre tu caso, usa el más genérico (`server`, `service`,
`component`) y aclara en `description`.
