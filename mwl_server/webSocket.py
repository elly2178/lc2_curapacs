import tornado.web
import tornado.ioloop

# web --> used for the handlers
# ioloop --> will try to listen on a port
class basicRequestHandler(tornado.web.RequestHandler):
    def get(self, id):
        self.write("HI")

class resourceRequestHandler(tornado.web.RequestHandler):
    def get(self, id):
        self.write("Querying tweet with id "+ id)
        # http://localhost:8881/tweet/8

class staticRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class queryStringRequestHandler(tornado.web.RequestHandler):
    def get(self):
        n = int(self.get_argument("n"))
        #print(n)
        result = "odd" if n % 2 else "even"
        self.write("the number "+ str(n) + " is " + result)
        # localhost:8881/isEven?n=9
if __name__ == "__main__":
    app = tornado.web.Application([
        # here put the request handlers
        (r"/", basicRequestHandler),
        (r"/blog", staticRequestHandler),
        (r"/isEven", queryStringRequestHandler), 
        (r"/tweet/([0-9]+)", resourceRequestHandler)
    ])

    app.listen(8881)
    print("im listening on port 8881")
    # start the thread
    tornado.ioloop.IOLoop.current().start()