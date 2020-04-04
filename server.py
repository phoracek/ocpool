import os
import subprocess

import web

urls = ("/", "Index")
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


def get_host_name():
    try:
        host_name_raw = subprocess.check_output(["hostname"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Exception("Failed obtaining hostname", exc.returncode, exc.output)
    return str(host_name_raw, "utf-8").strip()


def collect_clusters():
    clusters = []
    for cluster_dir in os.listdir("clusters"):
        clusters.append(
            {
                "name": read_cluster_file(cluster_dir, "NAME"),
                "status": read_cluster_file(cluster_dir, "STATUS"),
                "owner": read_cluster_file(cluster_dir, "OWNER"),
            }
        )
    return clusters


def read_cluster_file(cluster, file_name):
    with open(os.path.join("clusters", cluster, file_name)) as cluster_file:
        return cluster_file.read().strip()


if __name__ == "__main__":
    app.run()
