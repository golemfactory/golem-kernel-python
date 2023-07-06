# Jupyter on Golem - Python Kernel

## About

Lorem Ipsum - What is it
Lorem Ipsum - Clear reference to Jupytger Project

Jupyter on Golem comes with following PyPI preinstallled. Other packages can be installed  as described in Commands sexctions.

## Prerequisites

Jupyter on Golem needs some prerequsites. Please make sure you have the following requirements pre-installed:

*   **JupyterLab - version 4.0.2 or above**

    It most likely need no introduction. As stated on Jupyter Project webpage, JupyterLab is "highly extensible, feature-rich notebook authoring application and editing environment, and is a part of Project Jupyter, a large umbrella project centered around the goal of providing tools (and standards) for interactive computing with computational notebooks". To easy install JupoyterLab follow instructions provided on Jupyter Project webpage: https://jupyter.org/install

    TLDR Installation:
    ```
    pip install jupyterlab
    ```

*   **Yagna - version 0.12.2 or above**

    Yagna is a default implementation of Golem Network Node. It will act as an intermediary for JupyterLab to be able to communicate with Golem Network and find provider to execute our Jupyter Notebooks. Yagna can work in two "modes": Requestor or Provider. Jupyter on Golem needs Yagna to run in Requestor mode. To easy install Yagna as a Requestor follow instructions provided on Golem Network webpage: https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development#easy-installation

    TLDR Installation:
    ```
    curl -sSf https://join.golem.network/as-requestor | bash -
    ```

## Installation

```
#   Install Jupyter on Golem package from PyPI
pip install jupyter-on-golem

#   Add jupyter-on-golem to the list of known kernels
python -m jupyter_on_golem install

#   Start Jupyter in a browser to verify installation process
jupyter-lab
```

When above steps are completed Golem kernel should be visible and available in JupyterLab web interface:

Lorem Ipsum Picture here.

## Usage

Jupyter on Golem needs Yagna running on Your host to be able to talk with Golem Network. You can run it with single command (preferably in the separate Console Window):

```
#   Start Yagna on Your Host
yagna service run
```
With Yagna up and running You can start JupyterLab in standard fashion:

```
#   Start jupyter in a browser
jupyter-lab
```
In JupyterLab Web Interface click on Golem under the Notebook section to open new Notebook. You should be able to run Jupyter on Golem magic commands:

```
#   Display information about Jupyter on Golem
%help
```

Lorem Ipsum Picture here.

**After You close JupyterLab You can press Ctrl+C in Yagna terminal window to turn it off.** 

## Commands

#### %status

Shows the amount of tokens on the testnet and mainnet.

### %fund

Get some funds, if you need them. You can only get testnet tokens this way.

```
%fund goerli
```

### %budget

Define a budget for computations.

```
%budget goerli 1
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

### pip install

Lorem Ipsum

## Examples

We have prepared some examples to help you play around with Jupyter on Golem and better feel what it is capable of

Examples are based on
To run example you need to import to Your Jupyter this file:

*   **Testnet (Goerli) example notebook**: Lorem Ipsum  Github URL HERE
*   **Mainnet (Polygon) example notebook**: Lorem Ipsum  Github URL HERE

## Feedback

Lorem Ipsum - how to provide feedback