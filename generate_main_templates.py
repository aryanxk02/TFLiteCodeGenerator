import os
import templates

main_cc = templates.main
main_functions_h = templates.main_functions

result_a = main_cc.substitute()
result_b = main_functions_h.substitute()

file_path_a = os.path.join("common", "main.cc")
with open(file_path_a, "w") as file_a:
    file_a.write(result_a)

file_path_b = os.path.join("common", "main_functions.h")
with open(file_path_b, "w") as file_b:
    file_b.write(result_b)
