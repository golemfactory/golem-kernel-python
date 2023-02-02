from ipykernel.kernelapp import IPKernelApp

from .golem_kernel import GolemKernel

IPKernelApp.launch_instance(kernel_class=GolemKernel)
