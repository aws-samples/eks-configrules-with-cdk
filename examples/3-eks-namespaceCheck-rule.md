## eks-namespaceCheck-rule
To ensure that pods are not running in the default namespace, create a dedicated namespace for resource deployment
```
$ kubectl create namespace mynamespace
```
When deploying resources ensure that the desired namespace is specified in the pod manifest. If we do not specify a namespace in  our manifest, the deployment will end up in the default namespace:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insecure-deployment
  labels:
    app: insecure
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
```
As we can see in the example above, a namespace is not defined, if we update the manifest we can ensure that our deployment is deployed to the desired namespace
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insecure-deployment
  namespace: mynamespace
  labels:
    app: insecure
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

To delete the deployment we can run:
```
kubectl delete deployment insecure-deployment --namespace default
```
We can then run:
```
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insecure-deployment
  namespace: mynamespace
  labels:
    app: insecure
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
```



