=============
Versioned API
=============

The versioned API package provides the ability to define versioned
APIs as classes.  The primary use of this functionality is for
expressing the interfaces required by plugins, while allowing the
flexibility to evolve the interface over time using a version number.
Any package that defines an API should be compatible with any plugin
that implements that API, while plugins may optionally specify a
minimum interface version with which they work.

Required vs. Provided Interfaces
================================

Because ``vapi`` is intended to be used to define the interface for a
plugin, there are actually two distinct interfaces defined by a given
plugin class.  The first interface is those methods which must be
implemented by a plugin.  These methods are marked with the
``@required()`` decorator, and all plugins must provide those methods
for which a ``since=`` argument is not provided.

The second interface is those methods provided by the plugin base
class.  These methods are used by plugins to interact with the system
that they're plugged in to, and the methods are marked with the
``@provides()`` decorator.

The ``@required()`` and ``@provides()`` decorators have
``@required_property()`` and ``@provides_property()`` decorators
similar in concept to the ``@abc.abstractproperty`` decorator:
``vapi`` can be thought of as an extension of the abstract base
classes functionality, although it does not provide the ability to
register virtual subclasses which is available using ``abc.ABCMeta``.

What is an Interface?
=====================

A ``vapi`` interface is any class using ``vapi.VAPIMeta`` as its
metaclass.  Methods and properties may be decorated with the
decorators mentioned above; the decorators function in both a
documentation and an enforcement role, and are described below.  In
addition to the decorated methods and properties, a ``vapi`` interface
definition must provide a value for the ``__interface_version__``
class attribute, and an implementation must provide a value for the
``__api_version__`` class attribute.  The values of these attributes
must be simple integers, starting from 1; ``__interface_version__``
specifies the version of the interface definition, and
``__api_version__`` specifies the version of the interface definition
that has been implemented.  An implementation may also provide
``__minimum_version__`` to specify a minimum version of the interface
with which it is compatible; this may be used if, for instance, a
``@provides()`` decorated method introduced with a given interface
version is necessary for the plugin to function.  The plugin may also
provide ``__version__``, containing a *string* specifying the plugin
version, and ``__name__``, containing a user-presentable string naming
the plugin.

Creating an Interface
---------------------

For the first version of an interface, set ``__interface_version__``
to 0 and create a set of methods and properties decorated with the
appropriate decorators.  Do *not* use the ``since=`` parameter for
these decorators; this parameter is used in evolving an interface.
Subclassing one interface to define another interface is acceptable,
but is not recommended; to avoid programmer confusion, it is probably
best to only subclass an interface when implementing that interface.

Evolving an Interface
---------------------

Changes to an interface must allow for backwards compatibility.  This
means that the return values of methods and properties should remain
the same; newly added ``@required()`` methods and
``@required_property()`` properties must be optional; and any
parameters added to a ``@required()`` method must be optional, with
reasonable default values.  For every such logical change, the
``__interface_version__`` must be incremented by one, and newly-added
methods and properties must have ``since=`` specified to the
appropriate decorator.  The value of ``since=`` should be the value to
which ``__interface_version__`` was incremented.  The same rules apply
to ``@provides()`` methods and ``@provides_property()`` properties.

When changes must be made that break backwards compatibility, this
should be done by creating an entirely new interface class.  Use
``isinstance()`` tests to determine which major interface a given
plugin implements, and of course reset ``__interface_version__`` to 0
on the new interface class.  It is recommended to continue supporting
a previous interface for several versions, while emitting deprecation
warnings to alert users and plugin developers to the new interface.

Implementing an Interface
-------------------------

To implement a given interface, extend the interface class and provide
implementations of the ``@required()`` methods and
``@required_property()`` properties.  It is also necessary to provide
a value for ``__api_version__`` specifying which version of the
interface has been implemented.  The plugin must support being called
by any version from ``__minimum_version__`` (defaults to 0) up through
the specified ``__api_version__``; the rules regarding evolving an
interface ensure that it may be called by any version above
``__api_version__``.  Note that all required interface methods and
properties for the declared ``__api_version__`` must be implemented.

Plugin implementations may use any ``@provides()`` methods and
``@provides_property()`` properties available up to the declared
``__api_version__``.  If a given provided method or property was not
available until a given version, the plugin may choose to either set
``__minimum_version__`` to the version where that method or property
first appeared, or it may use a conditional on
``__interface_version__`` to determine if it should use an alternative
method to accomplish a given task.

In addition to ``__api_version__`` and ``__minimum_version__``,
plugins may provide ``__version__`` to specify the plugin version
(usually the same as the package version) and ``__name__`` to specify
a human-readable plugin name.

Capabilities
============

Capabilities are optional features that may be implemented by a
plugin.  The primary way to define a capability is to pass the
optional ``cap=`` argument to the ``@required()`` or
``@required_property()`` decorators; the value of this argument should
be a short string or a sequence of strings naming the associated
capability or capabilities that the method or property implements.
For each capability, if a given plugin implements one method or
property for that capability, it must implement *all* of them (under
the normal control of the ``since=`` parameter).  The list of
implemented capabilities are automatically computed and stored as a
set in the plugin's ``__capabilities__`` class attribute.

As an example of how this may be useful, consider an interface for
password managers.  The basic interface includes functions to save a
password, retrieve a password, and delete a password.  Some managers
may also choose to implement a list operation, but for security or
other reasons, many do not.  The interface could be defined with a
``list()`` method decorated with ``@required(cap='list')``.  An
application using the plugin--say, a GUI application--can then check
to see if the capability ``'list'`` exists in the plugin's
``__capabilities__`` set, and provide a "List" button if it does.

Capabilities may also be used to indicate support for optional
features that can't be tied to a set of methods or properties.  For
instance, a method may be defined as unconditionally required, but may
be defined to perform an operation when called in a certain way for
supporting plugins.  To advertise this support, a sequence of
capabilities implemented by a plugin may be assigned to
``__capabilities__`` in the class definition; this sequence will be
merged with the automatically computed capabilities, and thus will be
present in the ``__capabilities__`` class attribute.

Detecting Plugin Incompatibilities
==================================

The ``vapi.VAPIMeta`` metaclass uses the same methodology as
``abc.ABCMeta`` to advertise that a class is not suitable for
instantiation: required methods that are not implemented are listed in
a set called ``__abstractmethods__`` in the class.  When the
application then attempts to instantiate the class, a ``TypeError`` is
raised.  Therefore, to detect whether a plugin can be used, check to
see if a ``TypeError`` is raised when the plugin class is
instantiated.
