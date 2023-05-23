# TFlite-Micro Tools for Espressif Chipsets

This repo contains handy tools to make it easier for developers looking to run ML models to run on Espressif micro-controllers.

## TFLite to Example Template Generation

This script can convert any tflite model to example template which then can be integrated with any project.

Example command for the same:

```
python main.py hello_world.tflite common/main_functions.cc
```
