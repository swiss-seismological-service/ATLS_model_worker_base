"""
============================
RAMSIS worker implementation
============================

Since the worker API makes use of `Flask-RESTful
<https://flask-restful.readthedocs.io/en/latest/>`_ workers are resource
implementations. :cls:`ramsis.worker.utils.AbstractWorkerResource``extends the
resource API e.g. by means of handling an instance of a concrete
;cls:`ramsis.worker.utils.Task` object.

Hence, to implement a concrete worker follow this recipe:

    1. Provide a concrete implementation of :cls:`ramsis.worker.utils.Task`.
    2. Provide a concrete implmentation of
    :cls:`ramsis.worker.utils.AbstractWorkerResource`.
    3. Worker-side you should use a specified implementation of
    `ramsis.utils.protocol.WorkerInputMessage`. Define a custom model specific
    schema for `model_parameters` to allow parameter validation.

The worker communication protocol is standardized. That is why model
configuration parameters are passed to the worker as a dictionary.

The SaSS (Shapiro and Smoothed Seismicity) model worker is an exemplary
concrete implemention of an asynchronous worker. It is located at the
`ramsis.worker.SaSS` package.
"""

__version__ = '0.1'
