# coding:utf-8

import tornado.ioloop
import tornado.web
from qiniu_lite import Cow

cow = Cow('access key', 'secret key')
policy = cow.get_put_policy('bucket name')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('''
            <html><body>
            <form method="post" action="http://upload.qiniu.com/" enctype="multipart/form-data">
                <input name="token" type="hidden" value="%s">
                <input name="file" type="file" />
                <input name="accept" type="hidden" />
                <input type="submit" value="上传" />
            </form>
            </body></html>''' % policy.token())


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
