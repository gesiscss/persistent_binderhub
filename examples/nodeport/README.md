This example is created for documentation purposes and 
it contains a minimal configuration to deploy a persistent BinderHub. 
It is not meant to be used in production.

This example configuration
- requires that a default [storage class](https://kubernetes.io/docs/concepts/storage/storage-classes/) 
is set (see https://zero-to-jupyterhub.readthedocs.io/en/latest/customizing/user-storage.html)
- uses [nodePort services](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) 
to expose the application on `<NodeIP>:<NodePort>`
- doesn't uses a [container registry](https://binderhub.readthedocs.io/en/latest/setup-registry.html), 
so only local docker images are used, this is useful when running in a single node
- uses the default authenticator (DummyAuthenticator), 
see the [authentication guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/authentication.html) to obtain more information
- uses the default [database for hub](https://zero-to-jupyterhub.readthedocs.io/en/latest/reference/reference.html#hub-db)
- doesn't define [compute resources for user containers](https://zero-to-jupyterhub.readthedocs.io/en/latest/customizing/user-resources.html#set-user-memory-and-cpu-guarantees-limits)
- disables [cluster autoscaling](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/optimization.html#efficient-cluster-autoscaling) for simplicity
- disables image cleaner, 
 [dind](https://binderhub.readthedocs.io/en/latest/setup-binderhub.html#use-docker-inside-docker-dind)
 and [https](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/advanced.html#ingress) for simplicity

If you want to deploy a test persistent BinderHub with this config:

1. you have to replace `<NodeIP>` in `examples/nodeport/config.yaml` with the IP of your node
2. then assuming that you are at repo root, run
```bash
helm dependency update persistent_binderhub
helm upgrade pbhub-test persistent_binderhub \
             --install \
             --namespace=pbhub-test-ns \
             -f examples/nodeport/config.yaml \
             --debug

```
3. and finally you can reach it at `http://<NodeIP>:30123`
