from channels import route_class
from channels_api.routing import Routing
from .test_bindings import TestModelResourceBinding, TestPermissionResourceBinding


class TestDemultiplexer(Routing):

    consumers = {
        'testmodel': TestModelResourceBinding.consumer,
        'user:testmodel': TestPermissionResourceBinding.consumer,
    }

channel_routing = [
    route_class(TestDemultiplexer)
]