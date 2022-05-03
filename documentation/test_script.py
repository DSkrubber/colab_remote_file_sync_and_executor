"""Dummy script to test colab remote execution with results generation."""
import os

os.mkdir("/content/uploaded/output")
with open("/content/uploaded/output/result", "w") as result_file:
    result_file.write("12345\n")
