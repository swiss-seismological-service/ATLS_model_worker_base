# RT-RAMSIS SFM-Worker Components

## Installation

**TODO**

## Concept

`RT-RAMSIS` SFM-Workers wrap forecast models providing a RESTful API.
SFM-Workers handle requests, control the forecast computation and both return
and delete results when requested. Workers are implemented as stateless
webservices using the [Flask](http://flask.pocoo.org/) framework.

A worker basically consists of the following parts:

* A *resource* which provides the web service API
* A *model* implementing the scientific forecast model
* A *task* wrapping the forecast model
* A *schema* to deserialize model specific parameters included in the input
  message

## Implementation of a concrete SFM-Worker

In order to fully implement a `RT-RAMSIS` SFM-Worker API the `ramsis.worker`
package provides two general purpose implementations of
[Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/) resources:

1. `ramsis.sfm.worker.resource.RamsisWorkerResource`
2. `ramsis.sfm.worker.resource.RamsisWorkerListResource`

Hence, to implement a concrete worker follow this recipe:

1. Provide a concrete implementation of `ramsis.sfm.worker.model.Model`. A
   model must return a valid `ramsis.sfm.worker.model.ModelResult`.
2. Provide a concrete implementation of
   `ramsis.sfm.worker.resource.RamsisWorkerListResource`. Optionally also for
   `ramsis.sfm.worker.resource.RamsisWorkerResource`.
3. Worker-side you should use a specified implementation of
   `ramsis.utils.protocol.WorkerInputMessage`. Define a custom model specific
   schema for the `model_parameters` field in order to enable parameter
   validation.

The worker communication protocol is standardized. That is why model
configuration parameters by default are passed to the worker as a dictionary.

The EM1 (formerly SaSS (Shapiro and Smoothed Seismicity)) SFM-Worker is an
exemplary concrete implemention of an asynchronous worker implementing the Flask
[Blueprint](https://flask.pocoo.org/docs/blueprints/) approach. The source code
is located at the `ramsis.sfm.em1` package.
