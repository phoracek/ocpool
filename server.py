import subprocess

import web

urls = (
    '/', 'Hello'
)
app = web.application(urls, globals())
render = web.template.render('templates/')


class Hello:
    def GET(self):
        try:
            host_name = get_host_name()
        except Exception as exc:
            raise web.internalerror(exc)
        return render.index(host_name=host_name)


def get_host_name():
    try:
        host_name_raw = subprocess.check_output(['hostname'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Exception("Failed obtaining hostname", exc.returncode, exc.output)
    return str(host_name_raw, 'utf-8').strip()


if __name__ == '__main__':
    app.run()
