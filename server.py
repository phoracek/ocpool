import os
import subprocess

import web
from web import form

urls = (
    "/", "Index",
    "/cluster/(.*)/config", "Config",
    "/cluster/(.*)/logs", "Logs",
    "/cluster/(.*)/login", "Login",
    "/cluster/(.*)/kubeconfig", "Kubeconfig",
)
app = web.application(urls, globals())
render = web.template.render("templates/")


class Index:
    def GET(self):
        try:
            host_name = get_host_name()
            clusters = collect_clusters()
        except Exception as exc:
            raise web.internalerror(exc)

        return render.index(host_name=host_name, clusters=clusters)

    def POST(self):
        owner_form = build_owner_form(full=True)
        if owner_form.validates():
            if owner_form.get("Take").get_value() is not None:
                new_user = owner_form.get("User").get_value()
                cluster = owner_form.get("Cluster").get_value()
                write_cluster_file(cluster, "OWNER", new_user)
            elif owner_form.get("Release").get_value() is not None:
                cluster = owner_form.get("Cluster").get_value()
                write_cluster_file(cluster, "OWNER", "")

        reprovision_form = build_reprovision_form()
        if reprovision_form.validates():
            if reprovision_form.get("Reprovision").get_value() is not None:
                cluster = reprovision_form.get("Cluster").get_value()
                try:
                    trigger_reprovision(cluster)
                except Exception as exc:
                    raise web.internalerror(exc)

        web.seeother("/")


class Config:
    def GET(self, cluster_name):
        try:
            return read_cluster_file(cluster_name, "config")
        except Exception as exc:
            raise web.internalerror(exc)


class Logs:
    def GET(self, cluster_name):
        try:
            return read_provision_logs(cluster_name)
        except Exception as exc:
            raise web.internalerror(exc)


class Login:
    def GET(self, cluster_name):
        try:
            host_name = get_host_name()
            host_name_and_port = web.ctx.host
            console_password = read_auth_file(cluster_name, "kubeadmin-password")
            external_subnet = read_config_variable(cluster_name, "EXTERNAL_SUBNET")
        except Exception as exc:
            raise web.internalerror(exc)

        return render.login(
            host_name=host_name,
            host_name_and_port=host_name_and_port,
            cluster_name=cluster_name,
            external_subnet=external_subnet,
            console_password=console_password,
        )


class Kubeconfig:
    def GET(self, cluster_name):
        return read_auth_file(cluster_name, "kubeconfig")


def get_host_name():
    try:
        host_name_raw = subprocess.check_output(["hostname"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Exception("Failed obtaining hostname", exc.returncode, exc.output)
    return str(host_name_raw, "utf-8").strip()


def collect_clusters():
    clusters = []

    for cluster_dir in os.listdir("clusters"):
        if read_cluster_file(cluster_dir, "ENABLED") != "YES":
            continue

        cluster = {}
        cluster["name"] = read_cluster_file(cluster_dir, "NAME")
        cluster["status"] = read_cluster_file(cluster_dir, "STATUS")
        cluster["owner"] = read_cluster_file(cluster_dir, "OWNER")
        cluster["owner_form"] = build_owner_form(
            read_cluster_file(cluster_dir, "OWNER"), cluster["name"])
        cluster["reprovision_form"] = build_reprovision_form(
            read_cluster_file(cluster_dir, "OWNER"), cluster["name"])
        clusters.append(cluster)

    return clusters


def build_owner_form(user=None, cluster=None, full=False):
    if full:
        return form.Form(
            form.Hidden("Cluster", description="Cluster"),
            form.Textbox("User", description="User"),
            form.Button("Release", description="Release", type="submit"),
            form.Button("Take", description="Take", type="submit"),
        )
    elif user:
        return form.Form(
            form.Hidden("Cluster", description="Cluster", value=cluster),
            form.Textbox("User", description="User", value=user, disabled=None),
            form.Button("Release", description="Release", type="submit"),
        )
    else:
        return form.Form(
            form.Hidden("Cluster", description="Cluster", value=cluster),
            form.Textbox("User", description="User", value=user),
            form.Button("Take", description="Take", type="submit"),
        )


def build_reprovision_form(user=None, cluster=None):
    if user:
        return form.Form(
            form.Hidden("Cluster", description="Cluster", value=cluster),
            form.Button("Reprovision", description="Reprovision", type="submit"),
        )
    else:
        return form.Form(
            form.Hidden("Cluster", description="Cluster", value=cluster),
            form.Button("Reprovision", description="Reprovision", type="submit", disabled=None),
        )


def read_cluster_file(cluster, file_name):
    path = os.path.join("clusters", cluster, file_name)

    if not os.path.exists(path):
        return None

    with open(path) as cluster_file:
        return cluster_file.read().strip()


def write_cluster_file(cluster, file_name, value):
    with open(os.path.join("clusters", cluster, file_name), "w") as cluster_file:
        return cluster_file.write(value)


def trigger_reprovision(cluster_name):
    try:
        subprocess.check_output(["./trigger_reprovision", cluster_name], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Exception("Failed triggering reprovision", exc.returncode, exc.output)


def read_provision_logs(cluster_name):
    try:
        provision_logs = subprocess.check_output(["./read_provision_logs", cluster_name], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Exception("Failed reading provision logs", exc.returncode, exc.output)
    return str(provision_logs, "utf-8").strip()


def read_auth_file(cluster, file_name):
    path = os.path.expanduser(os.path.join("~/dev-scripts", "ocp", cluster, "auth", file_name))

    if not os.path.exists(path):
        return "Not found"

    with open(path) as cluster_file:
        return cluster_file.read()


def read_config_variable(cluster, variable_name):
    with open(os.path.join("clusters", cluster, "config")) as cluster_config:
        for line in cluster_config.readlines():
            if line.startswith(f"export {variable_name}="):
                return line.split("=", 1)[1]

    raise Exception(f"Variable '{variable_name}' was not found in cluster '{cluster}' config")


if __name__ == "__main__":
    app.run()
