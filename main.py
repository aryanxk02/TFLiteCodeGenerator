# import necessary modules
import subprocess
from string import Template
import os
import re
import argparse
import templates

# subprocess to run generate_cc_array.py
"""
RUN from tools
> python generate_cc_arrays.py main hello_world.tflite 
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
    "main",
    tflite_file,
]
subprocess.run(generate_cc_array, check=True)

# subprocess to run generate_micromutable_op_resolver.py
"""
RUN from tools
> python gen_micro_mutable_op_resolver/generate_micro_mutable_op_resolver_from_model.py --common_tflite_path=. --input_tflite_files=hello_world.tflite --output_dir=main
"""
generate_micromutable_op_resolver = [
    "python",
    "gen_micro_mutable_op_resolver/generate_micro_mutable_op_resolver_from_model.py",
    "--common_tflite_path=.",
    f"--input_tflite_files={tflite_file}",
    "--output_dir=main",
]
subprocess.run(generate_micromutable_op_resolver, check=True)

# subprocess to generate .cc and .h templates
generate_main_templates = ["python", "generate_main_templates.py"]
subprocess.run(generate_main_templates, check=True)

# extract model name from .tflite file
x = tflite_file.split(".")[0]

# extract operations from gen_micro_mutable_op_resolver.h
with open(f"main/{x}_gen_micro_mutable_op_resolver.h") as cppfile:
    operations = []
    for line in cppfile:
        if "micro_op_resolver." in line:
            # print(line)
            line = "".join(line.split())
            operations.append(line)
# print(operations)

# extract the name of the unsigned integer array
with open(f"main/{x}_model_data.cc", "r") as file:
    cpp_content = file.read()

pattern = r"const\s+unsigned\s+char\s+(\w+)\[\]"
match = re.search(pattern, cpp_content)

if match:
    array_name = match.group(1)
    print("/*")
    print("Array name:", array_name)
else:
    print("Array name not found.")

# VARIABLES
model_name = array_name
num_of_operations = len(operations)
resolver = "micro_op_resolver"
model_name_header = x
print("Name of the Model:", model_name)
print("Number of Operations:", num_of_operations)
print("Model Name Header:", model_name_header)
print("Description of Operations: ")
for i in operations:
    print(i)
print("*/")

results = templates.cppTemplate.safe_substitute(
    model_name=array_name,
    num_of_operations=num_of_operations,
    resolver=resolver,
    model_name_header=x,
)
cmake_template = templates.CMakeLists_txt.safe_substitute(model_name_header=x)

# store the results in main_functions.cc inside main folder
folder_path = "main"
file_path = os.path.join(folder_path, "main_functions.cc")

with open(file_path, "w") as file:
    file.write(results)

# x is passed to ${model_header_name} and written inside CMakeLists.txt
file_path_cmake = os.path.join(folder_path, "CMakeLists.txt")
with open(file_path_cmake, "w") as file:
    file.write(cmake_template)
