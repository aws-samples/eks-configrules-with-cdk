#!/bin/bash
# A sample manifest has been provided that updates the Security Context settings of the insecure-deployment that was deployed as part of the CDK Deployment.
# The deployment update unsets the value for the allowPrivilegeEscalation. To deploy the updated manifest run:
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insecure-deployment
  labels:
    app: insecure
    status:nowsecure
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        securityContext:
          runAsUser: 2000
          #allowPrivilegeEscalation: true
        ports:
        - containerPort: 80
EOF
