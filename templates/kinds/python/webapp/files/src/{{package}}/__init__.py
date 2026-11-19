"""{{title}}: <one line: what this service does>.

Layers (imports point one way, downwards; `make structure-check` enforces it):

    main      builds the app and wires the layers together (the composition root)
    api       HTTP: routes, request and response models, error format
    services  use cases: orchestrate the domain and the ports
    domain    business rules as plain Python; imports no framework, no storage
    adapters  the outside world: databases, queues, other services (implement ports)
"""
