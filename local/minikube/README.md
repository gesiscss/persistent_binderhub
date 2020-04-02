# Run Persistent BinderHub in minikube

1. Follow the [documentation](https://kubernetes.io/docs/tasks/tools/install-minikube/) to install minikube
and then start it: 

`minikube start`

2. Install and initialize helm [[1](https://github.com/jupyterhub/binderhub/blob/master/CONTRIBUTING.md#one-time-installation)]:
```bash
curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
helm init
# run this command until tiller is ready
helm version
# add jupyterhub chart repo and update charts
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update

```
Before starting your local deployment run:

`eval $(minikube docker-env)`

This command sets up docker to use the same Docker daemon as your minikube cluster does. 
This means images you build are directly available to the cluster. 
Note: when you no longer wish to use the minikube host, you can undo this change by running:

`eval $(minikube docker-env -u)`

3. Deploy persistent BinderHub:

```bash
cd persistent_binderhub
# update binderhub chart
helm dependency update persistent_binderhub
# test local config
helm template persistent_binderhub -f local/minikube/config.yaml
# install it in minikube cluster
helm upgrade pbhub-dev persistent_binderhub \
             --install \
             --namespace=pbhub-dev-ns \
             -f local/minikube/config.yaml \
             --debug

```

4. Get the kubernetes URL for the `proxy-public` service:

`minikube service --namespace=pbhub-dev-ns proxy-public --url=true`

5. in `config.yaml` replace all occurrences of `127.0.0.1` with the IP of `proxy-public` service, 
which you acquired in the previous step 
and run helm installation command again:

```bash
helm upgrade pbhub-dev persistent_binderhub \
             --install \
             --namespace=pbhub-dev-ns \
             -f local/minikube/config.yaml \
             --debug

```

6. Finally run this command to reach the application in browser:

`minikube service --namespace=pbhub-dev-ns proxy-public`

It takes couple of minutes until all pods get ready, because required docker images must be downloaded into minikube cluster. 
Meanwhile you can start the k8s dashboard and observe pods in `pbhub-dev-ns` namespace:

`minikube dashboard`

## Tearing everything down

```bash
# to delete the release
helm delete pbhub-dev --purge
# to delete the namespace
kubectl delete namespace pbhub-dev-ns

# to stop minikube
minikube stop
# if you get error "error: You must be logged in to the server (Unauthorized)", 
# # you can delete and re-start minikube cluster
minikube delete
rm -rf ~/.kube
```

## Useful minikube commands

```bash
# to get ip of minikube cluster
minikube ip

# to get get URL of binder service
minikube service --namespace=pbhub-dev-ns binder --url=true
# to list the URLs for all services
minikube service list --namespace=pbhub-dev-ns

# to mount a local directory to minikube instance
# https://minikube.sigs.k8s.io/docs/tasks/mount/
minikube mount path/to/dir:/mount/path
```

## Persistent volumes in minikube

https://minikube.sigs.k8s.io/docs/reference/persistent_volumes/

```bash
# ssh to minikube instance
minikube ssh
# inside minikube, list PVs
ls -alh /tmp/hostpath-provisioner/
```
