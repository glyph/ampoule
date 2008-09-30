import os

from twisted.application import service
from twisted.python import log
from twisted.internet.protocol import ServerFactory

def makeService(options):
    """
    Create the service for the application
    """
    ms = service.MultiService()
    
    from ampoule.pool import ProcessPool
    name = options['name']
    ampport = options['ampport']
    ampinterface = options['ampinterface']
    child = options['child']
    parent = options['parent']
    min = options['min']
    max = options['max']
    maxIdle = options['max_idle']
    recycle = options['recycle']
    
    pp = ProcessPool(child, parent, min, max, name, maxIdle, recycle)
    pp.start() # this is synchronous when it's the startup, even though
               # it returns a deferred.
    svc = AMPouleService(pp, child, ampport, ampinterface)
    svc.setServiceParent(ms)

    return ms

class AMPouleService(service.Service):
    def __init__(self, pool, child, port, interface):
        self.pool = pool
        self.port = port
        self.child = child
        self.interface = interface
        self.server = None

    def startService(self):
        """
        Before reactor.run() is called we setup the system.
        """
        service.Service.startService(self)
        from ampoule import rpool
        from twisted.internet import reactor

        try:
            factory = ServerFactory()
            factory.protocol = lambda: rpool.AMPProxy(wrapped=self.pool.doWork,
                                                      child=self.child)
            self.server = reactor.listenTCP(self.port,
                                            factory,
                                            interface=self.interface)
        except:
            import traceback
            print traceback.format_exc()

    def stopService(self):
        service.Service.stopService(self)
        if self.server is not None:
            self.server.stopListening()
        return self.pool.stop()
