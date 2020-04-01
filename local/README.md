# Run Persistent BinderHub in minikube

1. [Install minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/)

```bash
# to start minikube
minikube start

# to stop minikube
minikube stop
# if you get error "error: You must be logged in to the server (Unauthorized)", 
# # you can delete and re-start minikube cluster
minikube delete
rm -rf ~/.kube

# to start dashboard
minikube dashboard
# to get ip of minikube cluster
minikube ip
```

2. [Install and initialize helm](https://github.com/jupyterhub/binderhub/blob/master/CONTRIBUTING.md#one-time-installation)
```bash
curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
helm init
# wait until tiller is ready
helm version

helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
```
Before starting your local deployment run:

`eval $(minikube docker-env)`

This command sets up docker to use the same Docker daemon as your minikube cluster does. 
This means images you build are directly available to the cluster. 
Note: when you no longer wish to use the minikube host, you can undo this change by running:

`eval $(minikube docker-env -u)`

3. 
```bash
cd persistent_binderhub
# update binderhub chart
helm dependency update persistent_binderhub

# test config for local development
helm template persistent_binderhub -f local/config.yaml
# install it in minikube cluster
helm upgrade --install --namespace=pbhub-dev-ns pbhub-dev persistent_binderhub --debug -f local/config.yaml

# to delete
helm delete pbhub-dev --purge
kubectl delete namespace pbhub-dev-ns

```
4. Get the kubernetes URL for the `proxy-public` service

```bash
minikube service --namespace=pbhub-dev-ns proxy-public --url=true
# to get get URL of binder service
minikube service --namespace=pbhub-dev-ns binder --url=true
# to list the URLs for all services
minikube service list --namespace=pbhub-dev-ns
```

5. in `config.yaml` replace all occurrences of `127.0.0.1` with the IP of `proxy-public` service 
and run helm install command again

```bash
helm upgrade --install --namespace=pbhub-dev-ns pbhub-dev persistent_binderhub --debug -f local/config.yaml
# run this command to reach the application in browser
minikube service --namespace=pbhub-dev-ns proxy-public
```

## Persistent volumes in minikube

https://minikube.sigs.k8s.io/docs/reference/persistent_volumes/

```bash
# ssh to minikube instance
minikube ssh
# inside minikube, list PVs
ls -alh /tmp/hostpath-provisioner/
```
