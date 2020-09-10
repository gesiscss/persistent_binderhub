# Persistent BinderHub

This is a Helm chart to install a persistent BinderHub. 
It simply configures and extends [BinderHub chart](https://github.com/jupyterhub/binderhub) to add persistent storage, 
it doesn't define any new component. 
Therefore before using this chart it is required that you read through [BinderHub documentation](https://binderhub.readthedocs.io/en/latest/), 
you know how to deploy a [standard BinderHub](http://mybinder.org/) 
and you are familiar with [enabling authentication](https://binderhub.readthedocs.io/en/latest/authentication.html) in BinderHub.

* [Prerequisites](#prerequisites)
   * [User storage](#user-storage)
   * [Authentication](#authentication)
* [Installing the chart](#installing-the-chart)
   * [Known issues](#known-issues)
* [Uninstalling the chart](#uninstalling-the-chart)
* [Customization](#customization)
   * [BinderHub customization](#binderhub-customization)
   * [Default project](#default-project)
   * [Projects limit per user](#projects-limit-per-user)
   * [Repo providers](#repo-providers)
   * [Spawner](#spawner)
* [Local development](#local-development)
* [Migrating from JupyterHub chart](#migrating-from-jupyterhub-chart)
* [Limitations](#limitations)

## Prerequisites

First of all create a `config.yaml` file, everything explained here can go into that file 
and then it will be used for the installation. 
Before the installation there are configurations required to be done for `User storage` and `Authentication`.

### User storage

To be able to offer a persistent storage to users, in your kubernetes cluster you need to have a 
[storage class](https://kubernetes.io/docs/concepts/storage/storage-classes/) defined, 
which dynamically provisions persistent volumes. Please follow the 
[user storage documentation](https://zero-to-jupyterhub.readthedocs.io/en/latest/customizing/user-storage.html) 
of [JupyterHub chart](https://zero-to-jupyterhub.readthedocs.io/) for more information. 

Note that any configuration for JupyterHub chart goes under `binderhub.jupyterhub` 
in `config.yaml` that you created to install this chart. For example, if you want to specify the storage class, 
you have to add the following into your `config.yaml`:

```yaml
binderhub:
  jupyterhub:
    singleuser:
      storage:
        dynamic:
          storageClass: <storageclass-name>
```

### Authentication

This chart already includes some of the required changes for 
[enabling authentication](https://binderhub.readthedocs.io/en/latest/authentication.html#enabling-authentication). 
But there are pieces that have to be manually configured. In your `config.yaml`:

1. You have to set `oauth_client_id`:

```bash
binderhub:
  jupyterhub:
    hub:
      services:
        binder:
          # this is the default value
          oauth_client_id: "binder-oauth-client-test"
```

2. You have to use config of your authenticator for `binderhub.jupyterhub.auth`.
For more information you can check the 
[authentication guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/authentication.html).

```bash
binderhub:
  jupyterhub:
    # add the config of your authenticator here
    auth: {}
```

Note that by default the authenticator is [DummyAuthenticator](https://github.com/jupyterhub/dummyauthenticator) 
and it is recommended to use it only for testing purposes. 

## Installing the chart

First of all you can find the list of charts here: 
https://gesiscss.github.io/persistent_binderhub/

The installation consists of 2 steps. As a first step we install the chart, 
then we will finalize the configuration of the Binder service 
and upgrade the chart to apply final changes in the config.

To install the chart with the release name `pbhub` into namespace `pbhub-ns`:

```bash
# add the persistent_binderhub helm chart repo
helm repo add persistent_binderhub https://gesiscss.github.io/persistent_binderhub/
# update charts
helm repo update

# you can change release name and namespace as you want
RELEASENAME=pbhub
NAMESPACE=pbhub-ns
kubectl create namespace $NAMESPACE
helm upgrade $RELEASENAME persistent_binderhub/persistent_binderhub \
             --version=0.2.0-n219 \
             --install --namespace=$NAMESPACE \
             --debug
```

After the first step, run `kubectl get service proxy-public --namespace=$NAMESPACE` 
and note down the IP address under `EXTERNAL-IP`, which is the IP of the JupyterHub. 
Then run `kubectl get service binder --namespace=$NAMESPACE` 
and again note down the IP address under `EXTERNAL-IP`, which is the IP of the Binder service. 

With the IP addresses you just acquired update your `config.yaml`:

```bash
binderhub:
  jupyterhub:
    hub:
      services:
        binder:
          # where binder runs
          url: "http://<Binder_IP>"
          # when url is set, binder can be reached through JupyterHub
          oauth_redirect_uri: "http://<JupyterHub_IP>/services/binder/oauth_callback"
```

Finally upgrade the chart to apply this change:

```bash
helm upgrade $RELEASENAME persistent_binderhub/persistent_binderhub \
             --version=0.2.0-n219 \
             --install --namespace=$NAMESPACE \
             --debug
```

When the installation is done, 
the persistent BinderHub will be available at "http://<JupyterHub_IP>", 
and there (at JupyterHub home page) you will see a customized BinderHub UI for persistence, 
which is the place that users will interact with the system mostly. 
The standard BinderHub will be available at "http://<JupyterHub_IP>/services/binder" as a service of JupyterHub.

### Known issues

1. If you don't know the url of the JupyterHub (`binderhub.config.BinderHub.hub_url`) 
and it is not set during the first step of the installation, 
you will get an error similar to 
`Error: render error in "persistent_binderhub/charts/binderhub/templates/deployment.yaml": template: persistent_binderhub/charts/binderhub/templates/deployment.yaml:98:74: executing "persistent_binderhub/charts/binderhub/templates/deployment.yaml" at <"/">: invalid value; expected string`  
To fix it, you can use a dummy value for the `hub_url`, e.g. "http://127.0.0.1",  
and after the first step when you have the correct url of the hub, you can replace it.  
GitHub issue: https://github.com/gesiscss/persistent_binderhub/issues/5  
Potential fix: https://github.com/jupyterhub/binderhub/pull/1139

## Uninstalling the chart

```bash
# to delete the Helm release
helm delete $RELEASENAME --purge
# to delete the Kubernetes namespace
kubectl delete namespace $NAMESPACE
```

## Customization

As mentioned before, this chart extends the BinderHub chart in order to bring persistency in. 
To do that this chart also uses `extraConfig` from JupyterHub and BinderHub charts. While using persistent BinderHub chart, 
you should use another name for your `extraConfig`s, 
unless you want to overwrite defaults of this chart and you know what you are doing. 
Here is the list of `extraConfig`s used:

- `binderhub.extraConfig`:
  - `20-launcher` 
  - `10-repo-providers`

- `binderhub.jupyterhub.hub.extraConfig`:
  - `20-template-variables`
  - `10-project-api`
  - `00-binder`

For more information check [values.yaml](persistent_binderhub/values.yaml).

### BinderHub customization

Anything you want to customize in BinderHub chart you can refer to the 
[BinderHub documentation](https://binderhub.readthedocs.io/en/latest/). 
The only thing you have to pay attention is that you put that configs under `binderhub` in your `config.yaml`.
For example, if you want to use another version of repo2docker to build repos, add following into your `config.yaml`:

```yaml
binderhub:
  config:
    BinderHub:
      build_image: jupyter/repo2docker:0.11.0-52.g175b930
```

Note: `jupyter/repo2docker:0.11.0-52.g175b930` is the repo2docker version used in this chart.

### Default project

A project is simply a binder-ready repository that you launch in a persistent BinderHub. 

Default project is this repo itself by default 
(check [.binder folder](.binder), there is `intro_to_persistent_binderhub` notebook). 

Assuming that you have a binder-ready repo with the following information
- repo url: `https://github.com/user_name/repo_name`
- branch or tag or commit: `ref`

you can set it as default project by adding the following into your `config.yaml`:

```yaml
binderhub:
  jupyterhub:
    custom:
      default_project:
        repo_url: "https://github.com/user_name/repo_name"
        ref: "ref"
```

Warning: Default project must be a binder-ready repo, e.g. https://github.com/binder-examples/requirements.

### Projects limit per user

Number of projects concurrently stored per user. By default it is 5. 
For example, if you want to increase it to 10, 
add the following into your `config.yaml`:

```yaml
binderhub:
  extraEnv:
    - name: PROJECTS_LIMIT_PER_USER
      value: "10"  # change this value as you wish
```

<!-- we shouldn't encourage people not to have no limit. -->
<!-- If you want to have no projects limit, set `PROJECTS_LIMIT_PER_USER` to "0". -->

### Repo providers

Only the following repo providers are supported in this chart:
 - GitHubRepoProvider
 - GistRepoProvider
 - GitLabRepoProvider
 - GitRepoProvider

Other providers (ZenodoProvider, FigshareProvider, HydroshareProvider, DataverseProvider) are currently not supported. 
If you enable them, persistent BinderHub is not going to work as expected for these providers.

For example, if you want to only enable `GitHubRepoProvider` and `GistRepoProvider`, 
add the following into your config.yaml:

```yaml
binderhub:
  extraConfig:
    10-repo-providers:  |
      from binderhub.repoproviders import GitHubRepoProvider, GistRepoProvider
      c.BinderHub.repo_providers = {
          'gh': GitHubRepoProvider,
          'gist': GistRepoProvider,
      }
```

### Spawner

This chart uses the 
[PersistentBinderSpawner](https://github.com/gesiscss/persistent_binderhub/blob/master/persistent_binderhub/files/jupyterhub/persistent_bhub_config.py#L19).
If you want to customize it, you can subclass it in `extraConfig`. For example:

```yaml
binderhub:
  jupyterhub:
    hub:
      extraConfig:
        00-binder: |
          from persistent_bhub_config import PersistentBinderSpawner
          MyPersistentBinderSpawner(PersistentBinderSpawner):
            ...
          c.JupyterHub.spawner_class = MyPersistentBinderSpawner
```

## Local development

In [local/minikube](local/minikube) folder you can find instructions and configuration file to install this chart in minikube.

## Migrating from JupyterHub chart

Be aware that this is not tested widely, 
but it should be safe to migrate from [JupyterHub chart](https://zero-to-jupyterhub.readthedocs.io/) to this chart.

Here are the differences compared to fresh installation of this chart:
- after migration, existing users will have no default project in the beginning
- files of existing users won't be copied to anywhere,
  existing users can find them under `/projects` dir and 
  they should manage them manually via terminal

## Limitations

1. Binder pod (`binderhub.replicas`) must be 1, otherwise there are authentication errors 
  (https://github.com/jupyterhub/jupyterhub/issues/2841).

-------

Funded by the German Research Foundation (DFG). 
FKZ/project number: 
[324867496](https://gepris.dfg.de/gepris/projekt/324867496?context=projekt&task=showDetail&id=324867496&).
