# RAMSIS Worker 

A RAMSIS Worker controls a forecast model on behalf of RAMSIS Core. It
receives requests over a RESTful API, starts or stops its model
and returns results and state information whenever requested from the core.

A Worker consists of three parts:

1. A *resource* which provides the web service API.
2. A *task* which contains the model specific control mechanism
3. A *schema* to deserialize model specific parameters included in the input
message


# Implementation

Since the worker API makes use of [Flask-RESTful]
(https://flask-restful.readthedocs.io/en/latest/) workers are resource
implementations. `ramsis.worker.utils.AbstractWorkerResource` extends the
resource API e.g. by means of handling an instance of a concrete
`ramsis.worker.utils.Task` object.

Hence, to implement a concrete worker follow this recipe:

1. Provide a concrete implementation of `ramsis.worker.utils.Task`.
2. Provide a concrete implementation of
`ramsis.worker.utils.AbstractWorkerResource`.
3. Worker-side you should use a specified implementation of
`ramsis.utils.protocol.WorkerInputMessage`. Define a custom model specific
schema for `model_parameters` to allow parameter validation.

The worker communication protocol is standardized. That is why model
configuration parameters are passed to the worker as a dictionary.

The SaSS (Shapiro and Smoothed Seismicity) model worker is an exemplary
concrete implemention of an asynchronous worker. It is located at the
`ramsis.worker.SaSS` package.
