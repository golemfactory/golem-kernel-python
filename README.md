# Golem Kernel

## Installation & usage

This assumes you have a running `yagna` and `YAGNA_APPKEY` variable is set.

```
#   Install packages
pip3 install jupyterlab golem-kernel

#   Add golem-kernel to the list of known kernels
python3 -m golem_kernel install

#   Start jupyter in a browser. Golem kernel should be available.
jupyter-lab
```

## Example usage

Check the [`demo.ipynb`](demo.ipynb) notebook.

## Magic commands

### %status

Shows the amount of tokens on the testnet and mainnet.

### %fund

Get some funds, if you need them. You can only get testnet tokens this way.

```
%fund rinkeby
```

### %budget

Define a budget for computations.

```
%budget rinkeby 1
```

### %connect

Connect to a provider.

You can specify:

*   Minimal amount of RAM, disk and cores
*   Provider selection strategy (available strategies: "bestprice" - default, cheapest provider, "random" - random provider)
*   Image hash - [creating Golem images](https://handbook.golem.network/requestor-tutorials/vm-runtime/convert-a-docker-image-into-a-golem-image). This
    defaults to an image built from the [`provider`](provider) directory. Your image must include everything specified in [`provider/Dockerfile`](provider/Dockerfile) (except `numpy`).

Sample usage:

```
%connect mem>4 disk>100 cores>2 strategy=random image_hash=5389c01c128f94f14653bc0b56822c22b4b3987737ef8f3c0ac61946
```

### %disconnect

End work (on the current provider, you can connect to another one later) and pay.
