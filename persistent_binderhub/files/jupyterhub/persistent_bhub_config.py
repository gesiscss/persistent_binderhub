"""
Custom KubeSpawner and an API handler for projects to be used in persistent BinderHub deployment.
These are imported in binderhub.jupyterhub.hub.extraConfig in values.yaml.
"""
import json
import string
import random
import z2jh
from os.path import join
from urllib.parse import urlparse
from tornado import web
from jupyterhub.utils import admin_only
from jupyterhub.apihandlers.users import admin_or_self
from jupyterhub.apihandlers.base import APIHandler
from kubespawner import KubeSpawner


class PersistentBinderSpawner(KubeSpawner):
    """Assuming that each user has a storage (Persistent Volume)
    - copies launched project's data (repo content) into a separate directory by using `initContainers`.
      So in the project dir we have the same content as provided by repo2docker.
      This is particularly important because projects may use further features of repo2docker such as the postBuild script.
    - deletes dirs of projects, which are in state["deleted_projects"] of `spawners` table
    - mounts user’s PV somewhere other than the home dir (to /projects), so that users can access files across multiple projects
    - mounts the dir of the launched project (from user’s PV) into the home dir (/home/jovyan)
    - starts a notebook server on `/home/jovyan` which is the default behavior of BinderHub.
      Takes project information (e.g. image and repo url) from `user_options`, which is set by binder.
    - adds/updates data of the launched project into state["projects"] of `spawners` table
    """
    def __init__(self, **kwargs):
        super(PersistentBinderSpawner, self).__init__(**kwargs)
        # get default_project from custom config of z2jh chart (`binderhub.jupyterhub.custom`)
        # https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/advanced.html#custom-configuration
        default_project = z2jh.get_config('custom.default_project')
        display_name = self.url_to_display_name(default_project["repo_url"])
        # default_project is only to use when first login
        self.default_project = {
            "repo_url": default_project["repo_url"],
            "image": "",
            "ref": default_project["ref"],
            "display_name": display_name,
            "last_used": "never",
        }

    def url_to_display_name(self, url):
        """Converts a URL to display name in a `prefix/user_or_org_name/repo_name` format."""
        if url.endswith('.git'):
            url = url[:-4]
        url_parts = urlparse(url)
        # TODO handle provider prefix for other providers
        provider = url_parts.netloc.lower()
        if 'gist.github.com' in provider:
            provider_prefix = 'gist'
        elif 'github.com' in provider:
            provider_prefix = 'gh'
        elif 'gitlab.com' in provider:
            provider_prefix = 'gl'
        else:
            provider_prefix = 'git'
        path = url_parts.path.strip('/')
        display_name = f'{provider_prefix}/{path}'
        return display_name

    def url_to_dir(self, url):
        """Converts a URL to directory name."""
        display_name = self.url_to_display_name(url)
        dir_name = ''.join([c if c.isalnum() or c in ['-', '.'] else '_' for c in display_name])
        if len(dir_name) > 255:
            suffix_chars = string.ascii_lowercase + string.digits
            suffix = random.choices(suffix_chars, k=8)
            dir_name = f'{dir_name[:122]}_{dir_name[-122:]}_{suffix}'
        return dir_name

    def start(self):
        """Starts the user's pod with `user_options`, which is set by binder.
        Before starting the notebook server, starts an `initContainer` which
        first gets the information of projects to delete from state["deleted_projects"] (`spawners` table),
        then deletes these projects on disk (user storage),
        and then copies content of image's home dir into project dir if project dir doesn't exist.

        Starts the notebook server with 2 mounts,
        first one is the user storage (where all projects take place), which is mounted to `/projects` and
        second one is currently launched project's dir on the user storage, which is mounted to `/home/jovyan`.

        Note: init and notebooks containers shares a volume (user storage), that's how project content, which is
        copied by init container, is also available to notebook container.
        """
        # clean attributes, so we dont save wrong values in state when error happens
        for attr in ('repo_url', 'ref', 'image'):
            self.__dict__.pop(attr, None)

        # get image spec from user_options
        if 'image' in self.user_options and \
           'repo_url' in self.user_options and \
           'token' in self.user_options:
            # binder service sets the image spec via user options
            # user_options is saved in database, so even user deletes all projects,
            # user_options for last launched repo stays in database
            # NOTE: user can pass any options through API (without using binder) too
            self.image = self.user_options['image']
            self.ref = self.image.split(':')[-1]
            # repo_url is generated in binderhub by repo providers
            self.repo_url = self.user_options['repo_url']
            # strip .git at the end
            if self.repo_url.endswith('.git'):
                self.repo_url = self.repo_url[:-4]
        else:
            # if user never launched a repo before (user_options in database is empty)
            # and user is trying to start the server via spawn url
            # normally this shouldn't happen and
            # it would be good but we can't display a message to user, and raising errors cause hub to restart
            # so (as a workaround) launch a repo until we handle this better FIXME
            projects = self.get_state_field('projects')
            if projects and projects[-1].get("image"):
                # first be sure that user has no valid projects
                self.repo_url = projects[-1]["repo_url"]
                self.image = projects[-1]["image"]
                self.ref = projects[-1]["ref"]
                self.log.warning(f"Project '{self.repo_url}' with '{self.image}' doesn't exist in user_options.")
            else:
                msg = f"User ({self.user.name}) is trying to start the server via spawn url."
                # self.handler.redirect("/hub/home")
                # raise Exception(msg)
                self.log.info(msg)
                self.repo_url = "https://github.com/gesiscss/persistent_binderhub"
                self.image = "gesiscss/binder-gesiscss-2dpersistent-5fbinderhub-ab107f:0.2.0-n528.1"
                self.ref = self.image.split(':')[-1]
        self.log.info(f"User ({self.user.name}) is launching '{self.repo_url}' project with '{self.image}'.")

        # prepare the initContainer
        # NOTE: first initContainer runs and when it is done, then notebook container runs
        # https://kubernetes.io/docs/concepts/workloads/pods/init-containers/
        # https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-initialization/#create-a-pod-that-has-an-init-container
        # https://github.com/jupyterhub/kubespawner/blob/v0.8.1/kubespawner/spawner.py#L638-L664
        mount_path = '/projects/'
        # first it deletes projects on disk (if there are any to delete)
        # get list of projects to delete from disk before spawn in initContainer
        deleted_projects = self.get_state_field('deleted_projects')
        if deleted_projects:
            delete_cmd = f"rm -rf {' '.join([join(mount_path, self.url_to_dir(d)) for d in deleted_projects])}"
            self.log.info(f"Following projects will be deleted for user ({self.user.name}): {deleted_projects}")
        else:
            delete_cmd = ""
        # then copies image's home dir (repo content after r2d process)
        # into project's dir on disk (if project_path doesnt exists on persistent disk)
        project_dir = self.url_to_dir(self.repo_url)
        project_path = join(mount_path, project_dir)
        copy_cmd = f"if [ -d {project_path} ]; " \
                   f"then echo 'directory {project_path} exists'; " \
                   f"elif [ -L {project_path} ]; " \
                   f"then echo '{project_path} is a symlink'; " \
                   f"else mkdir {project_path} && cp -a ~/. {project_path}; fi"
        init_container_cmds = [delete_cmd, copy_cmd] if delete_cmd else [copy_cmd]
        command = ["/bin/sh", "-c", " && ".join(init_container_cmds)]
        self.log.debug(f"Following command will be executed for user ({self.user.name}): {command}")
        projects_volume_mount = {'name': self.volumes[0]['name'], 'mountPath': mount_path}
        # NOTE: if binder "start" config is defined
        #  (https://mybinder.readthedocs.io/en/latest/config_files.html#start-run-code-before-the-user-sessions-starts)
        #  and if start command changes the content,
        #  initcontainer misses that change.
        #  because start command is run as an ENTRYPOINT and initcontainer's command overwrites it
        #  But start command will be executed in notebook container (because we dont define a custom command for it),
        #  so change will take place there, and on user's side, there is no problem
        self.init_containers = [{
            "name": "project-manager",
            "image": self.image,
            "command": command,
            # volumes is already defined for notebook container (self.volumes)
            "volume_mounts": [projects_volume_mount],
        }]

        # notebook container (user server)
        # mount all projects (complete user disk) to /projects
        # first remove existing volume mounts to /projects, this mount path should be unique,
        # normally we shouldn't need this, but sometimes there is duplication when there is a spawn error
        # for example timeout error due to long docker pull (of a notebook server image)
        for i, v_m in enumerate(self.volume_mounts):
            if v_m['mountPath'] == projects_volume_mount['mountPath']:
                del self.volume_mounts[i]
        self.volume_mounts.append(projects_volume_mount)
        # mountPath is /home/jovyan, this is set in z2jh helm chart values.yaml
        # mount_path = "~/"
        # mount_path = "$(HOME)"
        # self.volume_mounts[0]['mountPath'] = mount_path
        # https://kubernetes.io/docs/concepts/storage/volumes/#using-subpath
        # mount only project_path to home
        self.volume_mounts[0]['subPath'] = project_dir

        self.reset_deleted_projects = True
        return super().start()

    def get_state_field(self, field_name):
        """Returns just current value of a field in state, doesn't update anything in spawner's state."""
        self.update_projects = False
        reset_deleted_projects = getattr(self, 'reset_deleted_projects', False)
        self.reset_deleted_projects = False
        state = self.get_state()
        self.update_projects = True
        self.reset_deleted_projects = reset_deleted_projects
        return state[field_name]

    def get_state(self):
        """Updates state["projects"] in `spawners` table and returns the updated state value.

        We use this method to update projects, because this method is called both in
        start and stop of the server (see jupyterhub.User's `start` and `stop` methods),
        db.commit is called after these methods.
        """
        _state = self.orm_spawner.state
        if _state:
            # user already launched a project (started its server), spawner has a state
            projects = _state.get('projects', [])
            _projects = []
            for project in projects:
                # to be backwards compatible for version <= 0.2.0-n153
                # convert list, which contains project data, to dict
                if isinstance(project, list):
                    _projects.append({
                        "repo_url": project[0],
                        "image": project[1],
                        "ref": project[2],
                        "display_name": project[3],
                        "last_used": project[4],
                    })
                else:
                    _projects.append(project)
            projects = _projects
            deleted_projects = _state.get('deleted_projects', [])
        else:
            # if user never launched project (state is empty), use default_project
            projects = [self.default_project]
            deleted_projects = []
            self.log.info(f"User ({self.user.name}) hasn't launched a project yet.")
        state = super().get_state()
        state['projects'] = projects
        state['deleted_projects'] = deleted_projects

        if getattr(self, 'update_projects', True) is True and \
           hasattr(self, 'repo_url') and hasattr(self, 'image') and hasattr(self, 'ref'):
            # project is started or already running or is stopped,
            # so move project to the end and update the "last used" time
            new_projects = []
            for project in projects:
                if project["repo_url"] != self.repo_url:
                    new_projects.append(project)
            from datetime import datetime
            new_projects.append({
                "repo_url": self.repo_url,
                "image": self.image,
                "ref": self.ref,
                "display_name": self.url_to_display_name(self.repo_url),
                "last_used": datetime.utcnow().isoformat() + 'Z',
            })
            state['projects'] = new_projects
            self.log.info(f"User ({self.user.name}) has just used the project {self.repo_url}.")

        if getattr(self, 'reset_deleted_projects', False) is True:
            state['deleted_projects'] = []

        return state

    def get_env(self):
        env = super().get_env()
        if 'repo_url' in self.user_options:
            env['BINDER_REPO_URL'] = self.user_options['repo_url']
        for key in (
                'binder_ref_url',
                'binder_launch_host',
                'binder_persistent_request',
                'binder_request'):
            if key in self.user_options:
                env[key.upper()] = self.user_options[key]
        return env


class ProjectAPIHandler(APIHandler):
    """A JupyterHub API handler to manage user projects."""

    def get_json_body(self):
        body = super().get_json_body()
        if body is None:
            body = {}
        return body

    @admin_only
    async def get(self, user_name):
        """Takes a user name and returns projects of that user."""
        # get user's projects
        user = self.find_user(user_name)
        if not user:
            raise web.HTTPError(404)
        projects = {'projects': user.spawner.get_state_field('projects')}
        self.write(json.dumps(projects))

    @admin_or_self
    async def delete(self, user_name):
        """Deletes a project from state["projects"] and adds it into state["deleted_projects"]
        in `spawners` table in database. It doesn't delete project files on disk (user storage),
        this is done by `InitContainer` during launch of a project next time.
        If user has a running server, this method returns a message to user and doesn't do any change.
        """
        # delete a project of user
        user = self.find_user(user_name)
        response = {}
        if user.spawner.active:
            response["error"] = "Project deletion is not allowed while the user server is active."
        else:
            body = self.get_json_body()
            if "repo_url" in body and "name" in body and "id" in body:
                repo_url = body["repo_url"]
                projects = user.spawner.get_state_field('projects')
                new_projects = []
                deleted_projects = user.spawner.get_state_field('deleted_projects')
                found = False
                for project in projects:
                    if repo_url != project["repo_url"]:
                        new_projects.append(project)
                    else:
                        found = True
                        if repo_url not in deleted_projects:
                            deleted_projects.append(repo_url)
                if found is True:
                    # NOTE: this way we ensure that this JSONDict field (state) is updated with db.commit()
                    state = user.spawner.get_state()
                    state["projects"] = new_projects
                    state["deleted_projects"] = deleted_projects
                    user.spawner.orm_spawner.state = state
                    self.db.commit()
                    message = f"Project {body['name']} is deleted."
                    self.log.info(f"{user.name}: {message}")
                    response["success"] = message
                    response["id"] = body["id"]
                else:
                    message = f"Project {body['name']} ({body['repo_url']}) doesn't exist."
                    self.log.info(f"{user.name}: {message}")
                    response["error"] = message
            else:
                response["error"] = "Bad request."
        self.write(json.dumps(response))
