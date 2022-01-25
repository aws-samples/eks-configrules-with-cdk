** eks-trustedRegCheck-rule
The EKS Config rule can for trusted reg check currently checks against a list of registries when evaluating containers running in a Kubernetes cluster to ensure that images are only being pulled from trusted registries. To modify or extend this list we can add our fully qualified container registry names to the trusted_registries parameter in app.py

```
trusted_registries = '602401143452.dkr.ecr.us-east-1.amazonaws.com,busybox'
```
For example, if we wanted to add a registry we can add our registry 'myecr.dkr.ecr.us-east-1.amazonaws.com'
```
trusted_registries = '602401143452.dkr.ecr.us-east-1.amazonaws.com,busybox,myecr.dkr.ecr.us-east-1.amazonaws.com'
```
To deploy these changes run:
```
$cdk deploy configrules
 ```