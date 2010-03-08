import string

from django.http import HttpResponse, HttpResponseNotAllowed


class Resource(HttpResponse):
    
    """Represents a single resource within a RESTful web service.
    
    The ``Resource`` class should be used to represent a single resource
    within a RESTful web service. It exists to be subclassed for each
    resource within the service, and these subclasses should define a method
    for each possible HTTP request method on the so"""
	
	def __init__(self, request, *args, **kwargs):
	    """Instantiate a ``Resource`` instance.
	    
	    This method overrides ``HttpResponse.__init__``, providing an
	    alternative way of serving views. It calls the overridden method
	    first, to handle the initialization, and then performs a dispatch
	    on the HTTP request method. The return values of these methods are
	    then merged back into the current ``HttpResponse`` instance.
	    
	    Because this is called like a view function, this method accepts
	    a request object and any other positional and/or keyword arguments,
	    These will be passed to the methods defined on a subclass, so those
	    methods should support any arguments given.
	    
	    If the given HTTP request method is not defined for a subclass, then
	    a 405 'Method Not Allowed' response is returned, along with a list
	    of allowed methods (obtained via introspection)."""
		HttpResponse.__init__(self)
		if hasattr(self, request.method.lower()):
			value = getattr(self, request.method.lower())(request,
			    *args, **kwargs)
			if isinstance(value, HttpResponse):
				self._update(value)
		elif hasattr(self, 'run'):
			value = self.run(request, *args, **kwargs)
			if isinstance(value, HttpResponse):
				self._update(value)
		else:
		    allowed_methods = []
		    for attr in dir(self):
		        if set(attr).issubset(set(string.lowercase)):
		            allowed_methods.append(attr.upper())
		    self._update(HttpResponseNotAllowed(sorted(allowed_methods)))
	
	def _update(self, response):
	    """Merge the info from another response with this instance.
	    
	    This method simply copies the attributes from the given response to
	    this instance, with the exceptions of the ``_headers`` and ``cookies``
	    dictionaries, whose ``update`` methods are called. This means that any
	    headers or cookies which are present in this response but not the
	    argument are preserved."""
		self._charset = response._charset
		self._is_string = response._is_string
		self._container = response._container
		self._headers.update(response._headers)
		self.cookies.update(response.cookies)
		self.status_code = response.status_code

