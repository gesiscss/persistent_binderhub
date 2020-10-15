# Run Persistent BinderHub in minikube

1. Follow the [documentation](https://kubernetes.io/docs/tasks/tools/install-minikube/) to install minikube
and then start your local cluster with  
`minikube start --driver <driver_name>`  
or if you want to start it with a specific kubernetes version and with 4 CPUs and 8 GB  
`minikube start --kubernetes-version v1.18.3 --driver <driver_name> --cpus 4 --memory 8192`  
and when the local cluster is ready, you can check the status with 
`minikube status`

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
in `local/minikube/config.yaml` replace all occurrences of the dummy IP (`127.0.0.1`) with the IP of the cluster.

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
    It takes couple of minutes until all pods get ready, 
    because required docker images must be downloaded into the local minikube cluster. 
    Meanwhile you can run the following command to observe the pods until they have status `Running`:  
    `kubectl get pod --namespace=pbhub-dev-ns --watch`  
    You can exit watching pods by `CTRL+C`.

6. Finally run this command to get the url of your persistent BinderHub instance:  
`minikube service proxy-public --namespace=pbhub-dev-ns --url=true`

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
# to delete the local minikube cluster
minikube delete
```

## Useful minikube commands

```bash
# to check status
minikube status
# to access to the kubernetes dashboard in minikube cluster
minikube dashboard
# to get ip of minikube cluster
minikube ip

# to configure your shell/environment to use minikube’s Docker daemon
eval $(minikube -p minikube docker-env)
# and to undo it
eval $(minikube docker-env -u)

# to get get URL of binder service
minikube service binder --url=true --namespace=pbhub-dev-ns
# to list the URLs for all services
minikube service list --namespace=pbhub-dev-ns

# to list supported addons
# NOTE: default storage class and provider addons are enabled by default
minikube addons list

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
