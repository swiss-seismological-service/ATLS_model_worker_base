# RT-RAMSIS SFM-Worker Components

## Installation

Make sure that the following dependencies are installed:

* libpq-dev
* libgdal-dev

Next, invoke:

```
pip install -r requirements.txt
```

Note, that encapsulating the installation by means of a [virtual
environment](https://docs.python.org/3/tutorial/venv.html) is strongly
recommended.

## Concept

`RT-RAMSIS` SFM-Workers wrap forecast models providing a RESTful API.
SFM-Workers handle requests, control the forecast computation and both return
and delete results when requested. Workers are implemented as stateless
webservices using the [Flask](http://flask.pocoo.org/) framework.

A worker basically consists of the following parts:

* A *resource* which provides the web service API
* A *model* implementing the scientific forecast model (or rather an adapter to
  the scientific forecast model, respectively)
* A *task* wrapping the forecast model
* A *schema* to deserialize model specific parameters included in the input
  message

## Implementation of a concrete SFM-Worker

In order to fully implement a `RT-RAMSIS` SFM-Worker API the `ramsis.worker`
package provides two general purpose implementations of
[Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/) resources:

1. `ramsis.sfm.worker.resource.RamsisWorkerResource`
2. `ramsis.sfm.worker.resource.RamsisWorkerListResource`

Hence, to implement a concrete SFM worker follow this recipe:

1. Provide a concrete implementation of `ramsis.sfm.worker.model.Model`. A
   model must return a valid `ramsis.sfm.worker.model.ModelResult`.
2. Provide a concrete implementation of
   `ramsis.sfm.worker.resource.RamsisWorkerListResource`. Optionally also for
   `ramsis.sfm.worker.resource.RamsisWorkerResource`.
3. Worker-side you should use a specified implementation of
   `ramsis.sfm.worker.parser.SFMWorkerIMessageSchema`. Define a custom model
   specific schema for the `model_parameters` field. Simply, inherit from class
   `ramsis.sfm.worker.parser.ModelParameterSchemaBase` in order to
   enable parameter validation for model specific parameters. Finally, create a
   a customized `SFMWorkerIMessageSchema` by means of the
   `ramsis.sfm.worker.parser.create_sfm_worker_imessage_schema` factory.

The worker communication protocol is standardized. That is why model
configuration parameters by default are passed to the worker as a dictionary.

The EM1 (formerly SaSS (Shapiro and Smoothed Seismicity)) SFM-Worker is an
exemplary concrete implemention of an asynchronous worker implementing the Flask
[Blueprint](https://flask.pocoo.org/docs/blueprints/) approach. The source code
is located at the
[ramsis.sfm.em1](https://gitlab.seismo.ethz.ch/indu/ramsis.sfm.em1) package.
