# Patrones de descomposición — cómo cortar los componentes

Cuatro patrones comunes para descomponer un contenedor en componentes.
Elige el que coincida con la arquitectura real, no fuerces uno.

---

## 1. Layered (capas) — clásico API REST

Mejor cuando el equipo organiza el código por responsabilidades técnicas y
no usa patrones específicos de DDD.

```
[Cliente / SPA]
       ↓ HTTPS/JSON
┌─────────────────────────────────────────┐
│  XxxController                          │
│  AuthInterceptor                        │
└─────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  XxxService                             │
│  YyyService                             │
└─────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  XxxRepository                          │
│  ExternalApiGateway                     │
└─────────────────────────────────────────┘
       ↓ JDBC / HTTPS
[BD / Sistemas externos]
```

Componentes típicos: `Controller`, `Service`, `Repository`, `Gateway`,
`Interceptor`, `Validator`, `Mapper` (si tiene lógica no trivial).

---

## 2. Hexagonal / Ports & Adapters

Mejor cuando el equipo separa el **dominio** del mundo exterior y testea el
dominio sin Spring/JPA/HTTP.

```
[Inbound Adapters]              [Outbound Adapters]
┌──────────────────┐           ┌──────────────────┐
│ RestAdapter      │           │ JpaOrderAdapter  │
│ KafkaConsumerAdpt│           │ StripeHttpAdptr  │
│ GrpcAdapter      │           │ KafkaPublisher   │
└──────────────────┘           └──────────────────┘
        ↓                              ↑
        ↓                              ↑
        ↓     ┌──────────────────┐     ↑
        ↓     │  Domain (Application + │
        ↓────→│  Aggregates + UseCases)│
              └────────────────────────┘
```

Componentes típicos: `RestAdapter`, `KafkaConsumerAdapter`, `JpaOrderAdapter`,
`StripeHttpAdapter`, `KafkaPublisher`, y en el centro **el dominio**:
`OrderUseCases`, `OrderAggregate` (si son grandes, divídelos).

Convención del label: agrega el tipo de port en `description`:
- "Inbound REST adapter".
- "Outbound JPA adapter para la BD."
- "Outbound HTTP adapter hacia Stripe."

---

## 3. CQRS

Mejor cuando lectura y escritura tienen modelos y caminos separados.

```
[Comandos]                    [Consultas]
   ↓                              ↓
┌──────────────┐              ┌──────────────┐
│ CommandCtrl  │              │ QueryCtrl    │
│ CommandHndlr │              │ QueryHandler │
└──────────────┘              └──────────────┘
        ↓                              ↓
┌──────────────┐              ┌──────────────┐
│ Domain +     │      events  │ ReadModel    │
│ EventStore   │  ───────────→│ Projections  │
└──────────────┘              └──────────────┘
        ↓                              ↑
   [Event Store BD]            [Read BD / cache]
```

Componentes típicos: `CommandController`, `CommandHandler`, `Domain`,
`EventStoreRepo`, `Projection<Xxx>`, `ReadModelRepo`, `QueryController`,
`QueryHandler`.

---

## 4. Event-driven worker

Mejor cuando el contenedor es un consumidor de cola que reacciona a eventos
sin exponer un API HTTP.

```
[Topic Kafka]
     ↓ consume (async)
┌─────────────────────────────────────────┐
│  OrderEventConsumer                     │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│  OrderHandler                           │
│  PaymentHandler                         │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│  OrderRepository                        │
│  PaymentGateway                         │
│  NotificationPublisher                  │
└─────────────────────────────────────────┘
     ↓ JDBC / HTTPS / Kafka
[BD / API externa / Otro topic]
```

Componentes típicos: `XxxEventConsumer`, `XxxHandler`, `Repository`,
`Gateway`, `Publisher`. Las flechas de consumo/publicación llevan
`async:true`.

---

## Mezclas y casos reales

Es legítimo combinar patrones — pero **mantén un solo lenguaje** dentro del
diagrama. Si modelas hexagonal, no llames `XxxController` a tu inbound
adapter; llámalo `XxxRestAdapter`.

---

## Reglas comunes a todos los patrones

1. **Cohesión:** un componente hace una cosa bien.
2. **Acoplamiento dirigido:** las dependencias fluyen hacia un sentido lógico
   (controllers → services → repositories; adapters → domain).
3. **Una sola flecha por par** — si A llama a B en 3 sitios distintos, sigue
   siendo UNA relación.
4. **No dibujes ciclos** a menos que sean reales y deliberados (event bus,
   notificación inversa). Si aparece un ciclo accidental, probablemente
   estás mezclando responsabilidades.

---

## Cuándo NO descomponer

Si el contenedor tiene <5 componentes lógicos claros, considera saltarte el
N3. Un README con un texto breve puede ser más útil que un diagrama con 4
cajas.
