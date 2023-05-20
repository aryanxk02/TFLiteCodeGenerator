import subprocess
from string import Template
import os
import re
import argparse

# subprocess to run generate_cc_array.py
"""
RUN from tools
> python generate_cc_arrays.py esp/output_dir esp/TFLITE/hello_world.tflite 
"""

parser = argparse.ArgumentParser(
    description="Description: Accept .tflite or .bmp file as input from the user"
)
parser.add_argument("input_file", help=".tflite or .bmp format")
args = parser.parse_args()
tflite_file = args.input_file

generate_cc_array = [
    "python",
    "generate_cc_arrays.py",
    "esp/output_dir",
    tflite_file,
]
subprocess.run(generate_cc_array, check=True)

# subprocess to run generate_micromutable_op_resolver.py
"""
RUN from tools
> python gen_micro_mutable_op_resolver/generate_micro_mutable_op_resolver_from_model.py --common_tflite_path=esp/TFLITE --input_tflite_files=hello_world.tflite --output_dir=esp/ops_resolver_output
"""
generate_micromutable_op_resolver = [
    "python",
    "gen_micro_mutable_op_resolver/generate_micro_mutable_op_resolver_from_model.py",
    "--common_tflite_path=.",
    f"--input_tflite_files={tflite_file}",
    "--output_dir=esp/ops_resolver_output",
]
subprocess.run(generate_micromutable_op_resolver, check=True)

cppTemplate = Template(
    """
/* Copyright 2020 The TensorFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/


#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/system_setup.h"
#include "tensorflow/lite/schema/schema_generated.h"

// #include "main_functions.h"
#include "gen_micro_mutable_op_resolver.h"
#include "output_dir/hello_world_model_data.h"
// #include "constants.h"
// #include "output_handler.h"

// Globals, used for compatibility with Arduino-style sketches.
namespace {
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;
int inference_count = 0;

constexpr int kTensorArenaSize = $kTensor_Arena_Size;
uint8_t tensor_arena[kTensorArenaSize];
}  // namespace

// The name of this function is important for Arduino compatibility.
void setup() {
  // Map the model into a usable data structure. This doesn't involve any
  // copying or parsing, it's a very lightweight operation.
  
  // X: variable =  g_hello_world_model_data
  model = tflite::GetModel($model_name);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    MicroPrintf("Model provided is schema version %d not equal to supported "
                "version %d.", model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }

  // This pulls in all the operation implementations we need.
  // NOLINTNEXTLINE(runtime-global-variables)
  // X: variable = Pull all the operations from op_resolver.h file
  static tflite::MicroMutableOpResolver<$num_of_operations> $resolver;
  $resolver.$layer_description

  #  = get_resolver();
  // Build an interpreter to run the model with.
  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, kTensorArenaSize);
  interpreter = &static_interpreter;

  // Allocate memory from the tensor_arena for the model's tensors.
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    MicroPrintf("AllocateTensors() failed");
    return;
  }

  // Obtain pointers to the model's input and output tensors.
  input = interpreter->input(0);
  output = interpreter->output(0);

  // Keep track of how many inferences we have performed.
  inference_count = 0;
}

// The name of this function is important for Arduino compatibility.
void loop() {
  // Calculate an x value to feed into the model. We compare the current
  // inference_count to the number of inferences per cycle to determine
  // our position within the range of possible x values the model was
  // trained on, and use this to calculate a value.
  float position = static_cast<float>(inference_count) /
                   static_cast<float>(kInferencesPerCycle);
  float x = position * kXrange;

  // Quantize the input from floating-point to integer
  int8_t x_quantized = x / input->params.scale + input->params.zero_point;
  // Place the quantized input in the model's input tensor
  input->data.int8[0] = x_quantized;

  // Run inference, and report any error
  TfLiteStatus invoke_status = interpreter->Invoke();
  if (invoke_status != kTfLiteOk) {
    MicroPrintf("Invoke failed on x: %f\n",
                         static_cast<double>(x));
    return;
  }

  // Obtain the quantized output from model's output tensor
  int8_t y_quantized = output->data.int8[0];
  // Dequantize the output from integer to floating-point
  float y = (y_quantized - output->params.zero_point) * output->params.scale;

  // Output the results. A custom HandleOutput function can be implemented
  // for each supported hardware target.
  HandleOutput(x, y);

  // Increment the inference_counter, and reset it if we have reached
  // the total number per cycle
  inference_count += 1;
  if (inference_count >= kInferencesPerCycle) inference_count = 0;
}

"""
)
# extract model name from .tflite file
x = tflite_file.split(".")[0]

# extract operations from gen_micro_mutable_op_resolver.h
with open(f"esp/ops_resolver_output/{x}_gen_micro_mutable_op_resolver.h") as cppfile:
    operations = []
    for line in cppfile:
        if "micro_op_resolver." in line:
            # print(line)
            line = "".join(line.split())
            operations.append(line)
# print(operations)


with open(f"esp/output_dir/{x}_model_data.cc", "r") as file:
    cpp_content = file.read()

pattern = r"const\s+unsigned\s+char\s+(\w+)\[\]"
match = re.search(pattern, cpp_content)

if match:
    array_name = match.group(1)
    print("Array name:", array_name)
else:
    print("Array name not found.")

# VARIABLES
# kTensor_Arena_Size = int(input("Enter kTensor_Arena_Size: "))
model_name = array_name
num_of_operations = len(operations)
resolver = "micro_op_resolver"

print("*"*100)
print("model_name:", model_name)
print("num of ops:", num_of_operations)
print("Operations Description: ")
for i in operations:
    print(i)
print("*"*100)
# results = cppTemplate.safe_substitute(
#     kTensor_Arena_Size=kTensor_Arena_Size,
#     model_name=array_name,
#     num_of_operations=num_of_operations,
#     resolver=resolver,
# )
# print("*" * 100)
# print(results)
