"""Dictionary that defines the lambdas being created"""
lambdas = {
    "functions": {
        "privEscalation": {
            "name": "privEscalation",
            "description": "Config rule that checks for pods that have privilege escalation enabled",
            "code": "resources/priv-escalation",
        },
        "logCheck": {
            "name": "logCheck",
            "description": "Config rule that checks that in scope EKS clusters have logging enabled",
            "code": "resources/logging-check",
        },
        "netPolCheck": {
            "name": "netPolCheck",
            "description": "Config rule that checks that in scope clusters have a network policy configured in each namespace",
            "code": "resources/network-policy",
        },
        "namespaceCheck": {
            "name": "namespaceCheck",
            "description": "Config rule that checks that in scope EKS clusters for pods running in the default namespace",
            "code": "resources/namespace-check",
        },
        "trustedRegCheck": {
            "name": "trustedRegCheck",
            "description": "Config rule that checks that in scope EKS clusters for containers that are running images from untrusted registries",
            "code": "resources/trusted-registry",
        },
    }
}
