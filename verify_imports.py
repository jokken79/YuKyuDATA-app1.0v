
import sys
import traceback

try:
    print("Attempting imports...")
    import main
    print("Import main success")
except Exception:
    print("Exception occurred!")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    # Extract last frame finding
    tb_list = traceback.extract_tb(exc_traceback)
    
    # Find the frame in main.py if possible
    main_frame = None
    for frame in tb_list:
        if "main.py" in frame.filename:
            main_frame = frame
            
    if main_frame:
        print(f"Error in {main_frame.filename} at line {main_frame.lineno}")
        print(f"Code: {main_frame.line}")
    else:
        # Just print the last one
        last_frame = tb_list[-1]
        print(f"Error in {last_frame.filename} at line {last_frame.lineno}")
        print(f"Code: {last_frame.line}")
        
    print(f"Exception: {exc_type.__name__}: {str(exc_value)}")
    
    with open("debug_error.txt", "w") as f:
        f.write(traceback.format_exc())
