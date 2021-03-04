# https://hub.docker.com/r/jupyter/base-notebook/tags/
# https://github.com/jupyter/docker-stacks/tree/master/base-notebook
FROM jupyter/base-notebook:hub-1.3.0

COPY intro_to_persistent_binderhub.ipynb ${HOME}/intro_to_persistent_binderhub.ipynb
RUN rm -rf ${HOME}/work
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}
