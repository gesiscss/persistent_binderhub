# Run Persistent BinderHub in minikube

1. Follow the [documentation](https://kubernetes.io/docs/tasks/tools/install-minikube/) to install minikube
and then start it: 

`minikube start` or `minikube start --memory 8192` if you want to start Minikube with a 8 GB VM

To point your shell to minikube's docker-daemon, run: 

`eval $(minikube -p minikube docker-env)`

This means images you build are directly available to the cluster. And to undo it run: 

`eval $(minikube docker-env -u)`

2. Install and initialize helm:

2.1. Helm 2 [[1](https://github.com/jupyterhub/binderhub/blob/master/CONTRIBUTING.md#one-time-installation)]:
```bash
curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
helm init
# run this command until tiller is ready
helm version

```

2.2. Helm 3 [[2](https://helm.sh/docs/intro/install/#from-script)]:
```bash
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
helm version

```

3. Clone the repo and cd into it:

```bash
git clone https://github.com/gesiscss/persistent_binderhub.git
cd persistent_binderhub
```

4. Run `minikube ip` to get the IP of the running cluster and 
in `local/minikube/config.yaml` replace all occurrences of `127.0.0.1` with the IP of the cluster.

5. Deploy persistent BinderHub:

```bash
# fetch the required charts (BinderHub and JupyterHub charts) into charts folder
helm dependency update persistent_binderhub
# test local config
helm template persistent_binderhub -f local/minikube/config.yaml
# install it in minikube cluster
kubectl create namespace pbhub-dev-ns
helm upgrade pbhub-dev persistent_binderhub/. \
             --install --namespace=pbhub-dev-ns \
             -f local/minikube/config.yaml \
             --debug

```

It takes couple of minutes until all pods get ready, because required docker images must be downloaded into the minikube cluster. 
Meanwhile you can run the following command to observe the pods until they have status `Running`:

`kubectl get pod --namespace=pbhub-dev-ns --watch`

You can exit watching by `CTRL+C`.

6. Finally run this command to reach the application in browser:

`minikube service proxy-public --namespace=pbhub-dev-ns`

## Tearing everything down

```bash
# to delete the Helm release
# if using helm 2
helm delete pbhub-dev --purge
# if using helm 3
helm delete pbhub-dev --namespace=pbhub-dev-ns
# to delete the Kubernetes namespace
kubectl delete namespace pbhub-dev-ns

# to stop minikube
minikube stop
# if you get error "error: You must be logged in to the server (Unauthorized)", 
# you can delete and re-start minikube cluster
minikube delete
```

## Useful minikube commands

```bash
# to access to the kubernetes dashboard in minikube cluster
minikube dashboard
# to get ip of minikube cluster
minikube ip

# to get get URL of binder service
minikube service binder --url=true --namespace=pbhub-dev-ns
# to list the URLs for all services
minikube service list --namespace=pbhub-dev-ns

# to mount a local directory to minikube instance
# https://minikube.sigs.k8s.io/docs/tasks/mount/
minikube mount path/to/dir:/mount/path
```

## Persistent volumes in minikube

https://minikube.sigs.k8s.io/docs/reference/persistent_volumes/

```bash
# returns the default storage class
kubectl get storageclass

# ssh to minikube instance
minikube ssh
# inside minikube, list PVs
ls -alh /tmp/hostpath-provisioner/
```
