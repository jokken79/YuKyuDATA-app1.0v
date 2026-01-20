
import sys
import os
import traceback

try:
    print("Attempting imports...")
    from exceptions.custom_exceptions import YuKyuException
    print("Import 1 success")
    from middleware.auth_middleware import create_access_token
    print("Import 2 success")
    import main
    print("Import main success")
except Exception:
    print("Exception occurred!")
    with open("debug_error.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Error written to debug_error.txt")
