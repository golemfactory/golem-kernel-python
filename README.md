# Jupyter on Golem - Python Kernel

## About

Jupyter on Golem is a JupyterLab Python kernel (https://jupyterlab.readthedocs.io), which enables you to run your Python Notebooks using resources available on decentralized Golem Network (https://www.golem.network/). Providers of such resources are compensated for their work with GLM tokens.

JupyterLab is an open-source project that is widely used by data scientists, analysts, researchers and developers. It allows you to create and share Notebooks - documents that combine code, equations, visualisations and narrative text. JupyterLab is part of Project Jupyter, umbrella project born from IPython Project (https://ipython.org/) and centered around providing tools for interactive computing with computational notebooks. Find more about Jupyter Project: https://jupyter.org/

**Simplified view on JupyterLab:**

![Simplified Diagram of a JupyterLab flow](https://github.com/golemfactory/golem-kernel-python/blob/2fac592d6dbcd88f73b830cabee774702c32326e/jupyterlab.png)

**Simplified view on Jupyter on Golem:**

![Simplified Diagram of a Jupyter on Golem flow](https://github.com/golemfactory/golem-kernel-python/blob/2fac592d6dbcd88f73b830cabee774702c32326e/jupyter_golem.png)

Jupyter on Golem comes with following PyPI packages preinstallled:
*   jupyter         - version 1.0.0
*   pandas          - version 2.0.2
*   tensorflow-cpu  - version 2.12.0
*   matplotlib      - version 3.7.1

Other packages can be installed on the Provider's host with `%pip install` command as described in **Commands** section of this document.

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

*   **GLM tokens**

    Golem is a Decentralized Network where Requestors (those who need computational resources) meet with Providers (those who rent such resources). Jupyter on Golem acts as a Requestor and consequently need a way to compensate Providers for their work. Golem utilize Blockchain technology to provide censorship resistant payments with GLM tokens (https://www.golem.network/glm). 
    
    **To sum it up You will need GLM tokens and some Network native tokens (ETH/Matic) for transaction fees to use Jupyter on Golem!** 
    
    However, We are aware that for some people Blockchain might be a little bit tricky at the start. That is why we have prepared two example scenarios of using Jupyter on Golem. One of them does not require from You any prior ownership of GLM tokens and is perfect for a first try!
    
    *   **Testnet (Goerli) - For Blockchain newbies**: This example will be performed on Testnet and as a result will not require from You any prior Blockchain knowledge. Testnet still needs tokens to pay providers but those will be given via `%fund` command. Nevertheless, You need to take into account that Testnet is for testing purposes. In other words it might be unstable from time to time and offers smaller amount of providers with less powerful equipment.
    *   **Mainnet (Polygon) - For Blockchain pros**: This one assumes that You are familliar with Blockchain and are fully capable of obtaining GLM + Matic tokens on your own. Mainnet is more stable and offers more powerful providers.

    Both scenarios are linked in **Examples** section of this document.

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

We have prepared some examples to help you play around with Jupyter on Golem and better feel what this solution is capable of. Examples and Data Sets are based on
To run examples you need to import to Your Jupyter following files:

*   **Testnet (Goerli) example notebook**: < Github URL HERE >
*   **Mainnet (Polygon) example notebook**: < Github URL HERE >
*   **Data Set (for both Testnet and Mainnet)**: < Github URL HERE >

## Limitations

Jupyter on Golem is in its infancy stage. Consequently, it has many limitations You should be aware of. The most imporant are listed below:

* ABC
* ABC
* ABC

## Feedback

Did You try Jupyter on Golem? We would love to get a feedback from You! Please do it under this link: < LINK HERE >

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

### 2. pip install returns error**:



