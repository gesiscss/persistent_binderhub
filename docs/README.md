# Persistent BinderHub Helm Charts

Using github pages to host persistent BinderHub Helm charts

## How to add a new chart into repo

When you made changes to this repo and want to create a new version,

1. First update README.md ("Installing the chart" section) and commit

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

git add docs/index.yaml docs/persistent_binderhub-0.2.0-n134.tgz
git commit -m "persistent_binderhub-<version>.tgz"
git push
# use version of the chart for tag
git tag <version>
git push --tags

```

- https://helm.sh/docs/topics/chart_repository/
- https://v2.helm.sh/docs/developing_charts/#the-chart-repository-guide
- https://medium.com/@mattiaperi/create-a-public-helm-chart-repository-with-github-pages-49b180dbb417
