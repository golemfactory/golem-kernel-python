import json
import os
import sys
import tempfile

from ipykernel.kernelapp import IPKernelApp
from jupyter_client.kernelspec import KernelSpecManager

from .golem_kernel import GolemKernel

KERNEL_DICT = {
    "argv": ["python", "-m", "golem_kernel", "-f", "{connection_file}"],
    "display_name": "Golem",
    "language": "python",
}


def parse_install_argv():
    if len(sys.argv) == 2:
        return False
    elif len(sys.argv) == 3 and sys.argv[2] == "--user":
        return True
    else:
        raise ValueError(f"Incorrect args: {sys.argv[2:]}. Only accepted option is --user.")


def install():
    args = {"kernel_name": "golem"}

    user = parse_install_argv()
    if user:
        args["user"] = True
    else:
        args["prefix"] = sys.prefix

    with tempfile.TemporaryDirectory() as path:
        with open(os.path.join(path, "kernel.json"), "w") as f:
            json.dump(KERNEL_DICT, f, indent=1)

        args["source_dir"] = path

        kernel_spec_manager = KernelSpecManager()
        dest = kernel_spec_manager.install_kernel_spec(**args)

    print(f"Installed kernelspec Golem in {dest}")


if __name__ == '__main__':
    if sys.argv[1] == "install":
        install()
    else:
        IPKernelApp.launch_instance(kernel_class=GolemKernel)
