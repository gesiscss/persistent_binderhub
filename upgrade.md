## Upgrading this chart

### If there is a new version of BinderHub chart

Here you can find the releases of BinderHub chart: https://jupyterhub.github.io/helm-chart/#development-releases-binderhub

1. http://github.com/jupyterhub/binderhub/compare/bc17443...X
2. If there is a z2jh upgrade: https://github.com/jupyterhub/zero-to-jupyterhub-k8s/compare/X...Y
3. If there is a JupyterHub upgrade:
 - https://github.com/jupyterhub/jupyterhub/compare/X...Y
 - Update base image tag with new version of JupyterHub in `.binder/Dockerfile`
 - Then update image tag of "gesiscss/binder-gesiscss-2dpersistent-5fbinderhub-ab107f" 
   in `persistent_binderhub/files/jupyterhub/persistent_bhub_config.py`
4. Update following files according to changes in comparison urls:
 - `persistent_binderhub/values.yaml`
 - `persistent_binderhub/files/jupyterhub/persistent_bhub_config.py`
 - `persistent_binderhub/files/jupyterhub/templates/home.html`
 - `README.md`s, `local` folder etc
5. Upgrade BinderHub chart version in `persistent_binderhub/requirements.yaml`
6. Upgrade chart version in `persistent_binderhub/Chart.yaml`, you should only update the `-nxyz` part, 
   it must be same as in version of BinderHub chart

### If updating/fixing files of this chart

1. Do your changes
2. Upgrade chart version in `persistent_binderhub/Chart.yaml`, you should only add .n at the end, e.g. 0.2.0-n153.1 or 0.2.0-n153.2. 
   The `-nxyz` part must stay same as in version of BinderHub chart

## How to add a new chart into chart repo

When you made changes to this repo and want to create a new version,

1. First update README.md (version of chart in "Installing the chart" section) and `binderhub.jupyterhub.custom.default_project.ref` in values.yaml and commit

2.
```bash
# be sure that you are in master branch

# verify that the chart is well-formed
#rm -rf persistent_binderhub/charts/*
helm lint persistent_binderhub/

# pull down the required binderhub chart into `charts` dir
#helm dependency update persistent_binderhub
# package the chart
helm package -u persistent_binderhub/
mv persistent_binderhub-<version>.tgz docs/

# create the index.yaml with chart info
#helm repo index --url https://gesiscss.github.io/persistent_binderhub/ docs/.
# merge the new chart info into index.yaml
helm repo index --url https://gesiscss.github.io/persistent_binderhub/ --merge docs/index.yaml docs/.
# fix the `created` date of previous versions 

git add docs/index.yaml docs/persistent_binderhub-<version>.tgz
git commit -m "persistent_binderhub-<version>.tgz"
git push
# use version of the chart for tag
git tag <version>
git push --tags

# helm 2
# search command returns only stable releases, the latest stable versions
helm search persistent_binderhub
# use --devel flag, if you want to get also pre-release versions
helm search persistent_binderhub --devel
# helm 3
helm search repo persistent_binderhub
helm search repo persistent_binderhub --devel

```

- https://helm.sh/docs/topics/chart_repository/
- https://v2.helm.sh/docs/developing_charts/#the-chart-repository-guide
- https://medium.com/@mattiaperi/create-a-public-helm-chart-repository-with-github-pages-49b180dbb417
