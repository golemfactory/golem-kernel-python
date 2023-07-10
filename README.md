# Jupyter on Golem - Python Kernel

## About

Lorem Ipsum - What is it
Lorem Ipsum - Clear reference to Jupytger Project

Jupyter on Golem comes with following PyPI preinstallled. Other packages can be installed  as described in Commands sexctions.

## Prerequisites

Jupyter on Golem needs some prerequsites. Please make sure you have the following requirements pre-installed:

*   **JupyterLab - version 4.0.2 or above**

    It most likely need no introduction. As stated on Jupyter Project webpage, JupyterLab is "highly extensible, feature-rich notebook authoring application and editing environment, and is a part of Project Jupyter, a large umbrella project centered around the goal of providing tools (and standards) for interactive computing with computational notebooks". To easy install JupoyterLab follow instructions provided on Jupyter Project webpage: https://jupyter.org/install

    TLDR install JupyterLab:
    ```
    pip install jupyterlab
    ```

*   **Yagna - version 0.12.2 or above**

    Yagna is a default implementation of Golem Network Node. It will act as an intermediary for JupyterLab to be able to communicate with Golem Network and find provider to execute our Jupyter Notebooks. Yagna can work in two "modes": Requestor or Provider. Jupyter on Golem needs Yagna to run in Requestor mode. To easy install Yagna as a Requestor follow instructions provided on Golem Network webpage: https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development#easy-installation

    TLDR install Yagna:
    ```
    curl -sSf https://join.golem.network/as-requestor | bash -
    ```

*   **Increased number of open file descriptors - macOS only!**

    This change is required for **macOS users only!** To apply it open terminal and perform following steps:

    Check Your current limit value of open file descriptors (most likely it will be 256) and write it down so You can go back to it if needed later:
    ```
    ulimit -n
    ```

    Increase the limit to 65565:
    ```
    ulimit -n 65565 
    ```
    Verify that the change took place:
    ```
    ulimit -n
    ```

## Installation

Install Jupyter on Golem package from PyPI:
```
pip install jupyter-on-golem
```

Add jupyter-on-golem to the list of known kernels:
```
python -m jupyter_on_golem install
```

## Usage

Jupyter on Golem needs Yagna running on Your host to be able to talk with Golem Network. You can run it with single command (preferably in the separate Console Window):

```
yagna service run
```
With Yagna up and running You can start JupyterLab in standard fashion:

```
jupyter-lab
```

If installation process was completed correctly then Golem kernel should be visible and available in JupyterLab web interface:

![Screenshot of a Golem kernel visible in JupyterLab web interface.](https://github.com/golemfactory/golem-kernel-python/blob/7f8669fbef78bfb4dc6ff9fbddc41e63d81bb2ba/Jupyter_on_Golem_kernel.png)

Click on the upper Golem icon (right under the Notebook section) to open new Notebook. You should be able to run Jupyter on Golem magic commands like _%help_ ,which will display the most important information about Jupyter on Golem:

```
%help
```

![Screenshot of a Golem help output in JupyterLab web interface.](https://github.com/golemfactory/golem-kernel-python/blob/7f8669fbef78bfb4dc6ff9fbddc41e63d81bb2ba/Jupyter_on_Golem_help.png)

**When You finish using Jupyter on Golem You can close JupyterLab (File -> Shut Down) and press Ctrl+C in Yagna terminal window to turn it off.** 

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

Might be good idea to take Go of coffee teams or tea.

### %disconnect

End work (on the current provider, you can connect to another one later) and pay.

### %pip install

Lorem Ipsum

## Examples

We have prepared some examples to help you play around with Jupyter on Golem and better feel what it is capable of

Examples are based on
To run example you need to import to Your Jupyter this file:

*   **Testnet (Goerli) example notebook**: Lorem Ipsum  Github URL HERE
*   **Mainnet (Polygon) example notebook**: Lorem Ipsum  Github URL HERE

## Feedback

Lorem Ipsum - how to provide feedback

## Troubleshooting

Lorem Ipsum - typical problems

### 1. Testnet (Goerli) fund lack of tGLM**:

Lorem Ipsum solution

**Solution A - Id on Yagna**

```
yagna id update 0x4f597d426bc06ed463cd2639cd5451667f9c3e3d --set-default

yagna id create --from-keystore
```

**Solution B - Metamask**



