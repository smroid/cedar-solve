"""
Generate the Python code for the gRPC proto files.
"""

import subprocess
from pathlib import Path

# repository root directory
_repo_root = Path(__file__).parent.parent


def main():
    # directory containing the main project module, in this case "tetra3"
    py_src_dir = _repo_root

    # directory containing all .proto files (may be multiple or nested)
    client_proto_root = _repo_root / "tetra3" / "proto"

    # directory where generated code will be placed
    client_target = _repo_root / "tetra3"

    # include root directory for generated code
    proto_include = client_target.relative_to(py_src_dir)

    # fetch all *.proto files as string paths
    proto_files = [str(p) for p in client_proto_root.glob("**/*.proto")]

    subprocess.check_call([
        "python", "-m", "grpc_tools.protoc",
        f"-I{proto_include}={client_proto_root}",
        f"--pyi_out={py_src_dir}",
        f"--python_out={py_src_dir}",
        f"--grpc_python_out={py_src_dir}",
        *proto_files,  # expand list of all proto files
    ])


if __name__ == '__main__':
    main()
