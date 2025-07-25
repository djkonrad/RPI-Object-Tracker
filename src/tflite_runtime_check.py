# src/tflite_runtime_check.py
import os
import sys

try:
    from tflite_runtime.interpreter import Interpreter
    print("Successfully imported tflite_runtime.interpreter.")
except ImportError:
    print("Error: Could not import tflite_runtime.interpreter.")
    print("Please ensure tflite-runtime is installed correctly for your Raspberry Pi architecture and Python version.")
    print("Refer to the 'tflite-runtime' installation steps in setup_guide.md.")
    sys.exit(1)

def main():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'ssd_mobilenet_v2.tflite')

    # This is a placeholder path.
    # In Week 4, you would replace 'dummy_model.tflite' with your actual ML model.
    # For now, ensure you have *any* file named 'dummy_model.tflite' in the 'models/' directory.
    # An empty file is sufficient for this script to attempt loading and confirm the interpreter works.

    if not os.path.exists(model_path):
        print(f"Error: Model file not found at '{model_path}'.")
        print("Please ensure you have placed a '.tflite' file (e.g., 'dummy_model.tflite')")
        print("in the 'models/' directory of your project.")
        sys.exit(1)

    print(f"Attempting to load model from: {model_path}")

    try:
        # Load the TFLite model and allocate tensors.
        interpreter = Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        print("Successfully loaded model and allocated tensors using tflite_runtime.")
        print("\nTensorFlow Lite runtime environment is ready for inference!")

        # Get input and output details (optional, but good for verification)
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print("\nModel Input Details:")
        for detail in input_details:
            print(f"  Name: {detail['name']}, Shape: {detail['shape']}, Dtype: {detail['dtype']}")

        print("\nModel Output Details:")
        for detail in output_details:
            print(f"  Name: {detail['name']}, Shape: {detail['shape']}, Dtype: {detail['dtype']}")


    except Exception as e:
        print(f"Error loading or initializing TFLite interpreter: {e}")
        print("This could be due to a corrupted model file, or an issue with your tflite-runtime installation.")
        sys.exit(1)

if __name__ == "__main__":
    main()