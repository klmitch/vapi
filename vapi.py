# Copyright 2014 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the
#    License. You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing,
#    software distributed under the License is distributed on an "AS
#    IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#    express or implied. See the License for the specific language
#    governing permissions and limitations under the License.

import functools

import six


class Required(object):
    """
    A utility class to bind together information about which API
    version a method became required in and which capability (if any)
    it corresponds to.
    """

    def __init__(self, since, caps):
        """
        Initialize a ``Required`` object.

        :param since: The first version the method appeared in.
        :param cap: The set of capabilities conferred by the method.
        """

        self.since = since
        self.caps = caps

    def required(self, version, caps):
        """
        Compute whether the method is required.

        :param version: The API version being implemented.
        :param caps: A set of capabilities implemented by the plugin.

        :returns: A ``True`` value if the method is required, or
                  ``False`` if it is not.
        """

        return (version >= self.since and
                (self.caps is None or bool(self.caps & caps)))


class Provides(object):
    """
    A utility class to bind together information about which API
    version a method was provided in.
    """

    def __init__(self, since):
        """
        Initialize a ``Provides`` object.

        :param since: The first version the method appeared in.
        """

        self.since = since


class RequiredProperty(property):
    """
    A subclass of ``property`` that adds the ``__isrequiredmethod__``
    instance attribute.
    """

    def __init__(self, req, fget=None, fset=None, fdel=None, doc=None):
        """
        Initialize a ``RequiredProperty`` instance.

        :param req: An instance of ``Required`` specifying the
                    requirements for the property.
        :param fget: A function used to get the value of the property.
        :param fset: A function used to set the value of the property.
        :param fdel: A function used to delete the value of the
                     property.
        :param doc: Documentation for the property.
        """

        self.__isrequiredmethod__ = req
        super(RequiredProperty, self).__init__(fget, fset, fdel, doc)


class ProvidesProperty(property):
    """
    A subclass of ``property`` that adds the ``__isprovidedmethod__``
    instance attribute.
    """

    def __init__(self, prov, fget=None, fset=None, fdel=None, doc=None):
        """
        Initialize a ``ProvidesProperty`` instance.

        :param req: An instance of ``Required`` specifying the
                    requirements for the property.
        :param fget: A function used to get the value of the property.
        :param fset: A function used to set the value of the property.
        :param fdel: A function used to delete the value of the
                     property.
        :param doc: Documentation for the property.
        """

        self.__isprovidedmethod__ = req
        super(ProvidesProperty, self).__init__(fget, fset, fdel, doc)


def _helper(args, kwargs, decorator, keys, cls):
    """
    A helper for implementing the decorators.

    :param args: The positional arguments passed to the decorator.
    :param kwargs: The keyword arguments passed to the decorator.
    :param decorator: The actual decorator function.  This will be
                      passed the ``cls`` instance and the function to
                      be decorated.
    :param keys: A set of keyword argument names expected by ``cls``.
    :param cls: One of the ``Required`` or ``Provides`` classes to
                instantiate and pass to ``decorator``.

    :returns: If the original decorator was called without arguments,
              it was called with the function to be decorated; in this
              case, returns the function.  Otherwise, returns a
              callable of one argument that performs the necessary
              decoration.
    """

    cls_args = {}

    # Grab the 'since' version
    if 'since' in keys:
        cls_args['since'] = kwargs.pop('since', 0)

    # Compute the capabilities
    if 'cap' in keys:
        caps = kwargs.pop('cap', None)
        if caps:
            cls_args['caps'] = frozenset([caps]
                                         if isinstance(caps, six.string_types)
                                         else caps)
        else:
            cls_args['caps'] = None

    # Complain if there are any other keyword arguments
    if kwargs:
        raise TypeError('invalid keyword arguments "%s"' %
                        '", "'.join(sorted(kwargs.keys())))

    # Sanity-check positional arguments...
    if len(args) > 1:
        raise TypeError('invalid positional arguments; expecting at most 1, '
                        'got %d arguments' % len(args))

    # Instantiate the class
    inst = cls(**cls_args)

    # Call the decorator with it
    if args:
        # Called with the function to decorate, so decorate it
        return decorator(inst, args[0])
    else:
        # Return a decorator
        return functools.partial(decorator, inst)


def required(*args, **kwargs):
    """
    Mark a method as required.  This is similar to
    ``@abc.abstractmethod``, except that it takes two optional
    keyword-only arguments.

    :param since: Specifies the first version in which the required
                  method appeared.  Must be an integer.  If not
                  specified, defaults to 0.
    :param cap: Specifies a capability or a set of capabilities
                associated with the method.  The value may be a single
                string, naming the capability, or it may be a sequence
                of capability strings.  If the method is implemented,
                all methods or properties with corresponding
                capabilities will be required, and the capabilities
                implemented will be listed in the class's
                ``__capabilities__`` set.

    :returns: The decorated function or a decorator function,
              depending on whether a positional argument was passed.
    """

    # The actual decorator function
    def decorator(req, func):
        func.__isrequiredmethod__ = req
        return func

    # Handle the arguments
    return _helper(args, kwargs, decorator, set(['since', 'cap']), Required)


def required_property(*args, **kwargs):
    """
    Mark a property as required.  This is similar to
    ``@abc.abstractproperty``, except that it takes two optional
    keyword-only arguments.

    :param since: Specifies the first version in which the required
                  property appeared.  Must be an integer.  If not
                  specified, defaults to 0.
    :param cap: Specifies a capability or a set of capabilities
                associated with the property.  The value may be a
                single string, naming the capability, or it may be a
                sequence of capability strings.  If the property is
                implemented, all methods or properties with
                corresponding capabilities will be required, and the
                capabilities implemented will be listed in the class's
                ``__capabilities__`` set.

    :returns: The decorated function or a decorator function,
              depending on whether a positional argument was passed.
    """

    # Handle the arguments
    return _helper(args, kwargs, RequiredProperty, set(['since', 'cap']),
                   Required)


def provides(*args, **kwargs):
    """
    Mark a method as provided.  This takes one optional keyword-only
    argument.

    :param since: Specifies the first version in which the provided
                  method appeared.  Must be an integer.  If not
                  specified, defaults to 0.

    :returns: The decorated function or a decorator function,
              depending on whether a positional argument was passed.
    """

    # The actual decorator function
    def decorator(prov, func):
        func.__isprovidedmethod__ = prov
        return func

    # Handle the arguments
    return _helper(args, kwargs, decorator, set(['since']), Provides)


def provides_property(*args, **kwargs):
    """
    Mark a property as provided.  This takes one optional keyword-only
    argument.

    :param since: Specifies the first version in which the provided
                  property appeared.  Must be an integer.  If not
                  specified, defaults to 0.

    :returns: The decorated function or a decorator function,
              depending on whether a positional argument was passed.
    """

    # Handle the arguments
    return _helper(args, kwargs, ProvidesProperty, set(['since']), Provides)
