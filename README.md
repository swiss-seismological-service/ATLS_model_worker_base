# RT-RAMSIS Worker

`RT-RAMSIS` workers wrap forecast models providing a RESTful API. Workers
handle requests, control the forecast computation and both return and delete
results when requested. Workers are implemented as stateless webservices using
the [Flask](http://flask.pocoo.org/) framework.

A worker basically consists of the following parts:

* A *resource* which provides the web service API
* A *model* implementing the scientific forecast model
* A *task* executing the forecast model
* A *schema* to deserialize model specific parameters included in the input
  message

# Implementation

In order to fully implement a `RT-RAMSIS` worker API the `ramsis.worker`
package provides two general purpose implementations of
[Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/) resources:

1. `ramsis.worker.utils.resource.RamsisWorkerResource`
2. `ramsis.worker.utils.resource.RamsisWorkerListResource`

Hence, to implement a concrete worker follow this recipe:

1. Provide a concrete implementation of `ramsis.worker.utils.model.Model`. A
   model must return a valid `ramsis.worker.utils.model.ModelResult`.
2. Provide a concrete implementation of
   `ramsis.worker.utils.resource.RamsisWorkerListResource`. Optionally also for
   `ramsis.worker.utils.resource.RamsisWorkerResource`.
3. Worker-side you should use a specified implementation of
   `ramsis.utils.protocol.WorkerInputMessage`. Define a custom model specific
   schema for the `model_parameters` field in order to enable parameter
   validation.

The worker communication protocol is standardized. That is why model
configuration parameters by default are passed to the worker as a dictionary.

The SaSS (Shapiro and Smoothed Seismicity) model worker is an exemplary
concrete implemention of an asynchronous worker implementing the Flask
[Blueprint](https://flask.pocoo.org/docs/blueprints/) approach. The source code
is located at the `ramsis.worker.SaSS` package.
