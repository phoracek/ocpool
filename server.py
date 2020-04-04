import web

urls = (
    '/(.*)', 'Hello'
)
app = web.application(urls, globals())

class Hello:
    def GET(self, name):
        if not name:
            name = 'World'
        return 'Hello, ' + name + '!'

if __name__ == '__main__':
    app.run()
