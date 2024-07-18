# Jupyter on Golem - Python Kernel

## About

> [!WARNING]
> At this time, further development of Jupyter on Golem project has been put on hold.

Jupyter on Golem is a Python kernel, which integrates with JupyterLab (https://jupyterlab.readthedocs.io) and enables it to run your Python Notebooks using resources available on decentralized Golem Network (https://www.golem.network/). Providers of such resources are compensated for their work with GLM tokens.

JupyterLab is an open-source project that is widely used by data scientists, analysts, researchers and developers. It allows you to create and share Notebooks - documents that combine code, equations, visualisations and narrative text. JupyterLab is part of Project Jupyter, umbrella project born from IPython Project (https://ipython.org/) and centered around providing tools for interactive computing with computational notebooks. Find more about Jupyter Project: https://jupyter.org/

**Simplified view on JupyterLab:**

![Simplified Diagram of a JupyterLab flow](https://raw.githubusercontent.com/golemfactory/golem-kernel-python/master/images/jupyterlab.png)

**Simplified view on Jupyter on Golem:**

![Simplified Diagram of a Jupyter on Golem flow](https://raw.githubusercontent.com/golemfactory/golem-kernel-python/master/images/jupyter_golem.png)

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
    *   **Mainnet (Polygon) - For Blockchain pros**: This one assumes that You are familliar with Blockchain and are fully capable of obtaining GLM + Matic tokens on your own. Mainnet is more stable and offers more powerful providers. Check [Mainnet](#mainnet) section of this document to get help with obtaining GLM and Matic tokens for Jupyter on Golem.  

    Both scenarios are linked in [Examples](#examples) section of this document.

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

![Screenshot of a Golem kernel visible in JupyterLab web interface.](https://raw.githubusercontent.com/golemfactory/golem-kernel-python/master/images/Jupyter_on_Golem_kernel.png)

Click on the upper Golem icon (right under the Notebook section) to open new Notebook. You should be able to run Jupyter on Golem magic commands like _%help_ ,which will display the most important information about Jupyter on Golem:

```
%help
```

![Screenshot of a Golem help output in JupyterLab web interface.](https://raw.githubusercontent.com/golemfactory/golem-kernel-python/master/images/Jupyter_on_Golem_help.png)

**When You finish using Jupyter on Golem You can close JupyterLab (File -> Shut Down) and press Ctrl+C in Yagna terminal window to turn it off.** 

## Commands

Below You will find the list of all Jupter on Golem magic commands which are required to interact with this tool.

Magic commands is the concept of IPython (default kernel of JupyterLab). If you want to learn more then You should visit: https://ipython.readthedocs.io/en/stable/interactive/tutorial.html#magic-functions

### %help

Shows Jupyter on Golem basic information and list of available magic commands with a short description.

### %status

Shows the current status of Jupyter on Golem. With this command You can get following information:

*   **Your YAGNA node ID**
*   **Your YAGNA wallet address** - You should sent there GLM and MATIC tokens if You want to use Golem mainnet. By default wallet address is the same as node ID
*   **Amount of tokens (GLM,MATIC) hold by your wallet on Mainnet**
*   **Amount of tokens (tGLM,tETH) hold by your wallet on Testnet**
*   **Current connection status** - Disconnected or Established
    *   **Name and Node ID of a Provider** - for Established connections only
    *   **Resources of a Provider (RAM, DISK, CPU)** - for Established connections only
    *   **Elapsed connection time** - for Established connections only

### %fund

Requests for Goerli testnet tokens: tGLM and tETH. You can only get Goerli testnet tokens this way.

```
%fund goerli
```

### %budget

Allocates budget (GLM/tGLM) from funds in Your wallet for computation purposes on Jupter on Golem. It also sets the network to which you will connect when using `%connect` command! Using this command multiple times will each time overwrite the previous settings.

To setup for Goerli Testnet and Allocate 2 tGLM:
```
%budget goerli 1
```

To setup for Polygon Mainnet and Allocate 2 tGLM:
```
%budget polygon 2
```

### %connect

Initialize a connection with a provider fulfilling specified requirements.

following requirements can be specified:

*  **Minimal amount of RAM (GB)** - mem
*  **Minimal amount of disk space (GB)** - disk
*  **Minimal amount of CPU cores** - cores

Please take into account that sometimes it might take a litle bit longer to find a provider and setup him for work. To define how much You are willing to wait You can use timeout parameter. Default timeout is set to 10 minutes (`timeout=10m`)

Sample connect command requesting for provider with at least 4GM of RAM, 10GB of Disk space and 2 CPU cores:
```
%connect mem>4 disk>10 cores>2
```

Sample connect command with timeout set to 15 minutes, requesting for provider with at least 4GM of RAM, 10GB of Disk space and 2 CPU cores:
```
%connect mem>4 disk>10 cores>2 timeout=15m
```

### %disconnect

Disconnects from the current provider and initializes the payment transaction. It also shows following information:
*   Elapsed connection time
*   Total cost of the connection
*   Remaining allocation

### %pip install

Installs specified pip package. It is imporant to do it as a magic command (with % prefix) for installation to be completed correctly!

For instance, to add some colors to Your notebook You can install colorama package:
```
%pip install colorama
```

## Mainnet

To easily onboard yourself into Polygon Mainnet, You can use our "Onboarding Portal". However, please keep in mind that it is currently in the Technical Beta stage. Consequently, It should be functional but some issues migh still be present.

To use our "Onboarding Portal" You first need to identify Your Yagna Wallet Address. Fortunately it can be easily done with `%status` command run under Jupyter on Golem Notebook. Command will present You **My wallet address** value. Copy that value into clipboard and paste it into <PUT_HERE_YOUR_JUPYTER_ON_GOLEM_WALLET_ADDRESS> in the link below:

`https://golemfactory.github.io/onboarding_production/?yagnaAddress=<PUT_HERE_YOUR_JUPYTER_ON_GOLEM_WALLET_ADDRESS>`

As a result Your link should look simillarly to the one below:

DO NOT USE THIS LINK! THIS IS EXAMPLE ONLY! `https://golemfactory.github.io/onboarding_production/?yagnaAddress=0x0000000000000000000000000000000000000000` DO NOT USE THIS LINK! THIS IS EXAMPLE ONLY!

Put the link with Your Jupyter on Golem wallet in Your browser address bar and follow the instructions presented there. To have minimal yet comfortable amount of tokens for trying out Golem Network it is recommended to spent around 10 EUR for Matic tokens and swap around 70% of them into GLM tokens. Onboarding Portal will help You out with that steps.

After the last step is completed, You should have Your GLM and Matic tokens on Yagna Wallet. You can verify that by running again `%status` command under Jupyter on Golem Notebook. Now You should be able to create allocation (e.g.`%budget polygon 2`) and connect to Mainnet Providers.

## Examples

We have prepared some examples to help you play around with Jupyter on Golem and better feel what this solution is capable of. To run examples you need to import to Your JupyterLab following files:

*   [Testnet (Goerli) example notebook](https://github.com/golemfactory/golem-kernel-python/blob/master/examples/goerli_testnet_example.ipynb)
*   [Mainnet (Polygon) example notebook](https://github.com/golemfactory/golem-kernel-python/blob/master/examples/polygon_mainnet_example.ipynb)
*   [Data Set (for both Testnet and Mainnet)](https://github.com/golemfactory/golem-kernel-python/blob/master/examples/california_housing_train.csv) 

Above examples are modification of "Linear Regression with a Real Dataset" Notebook from Machine Learning Crash Course created by Google: [LINK](https://github.com/google/eng-edu/blob/main/ml/cc/exercises/linear_regression_with_a_real_dataset.ipynb). All exercises are made available under the [Apache License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)

Data Set contains data drawn from the 1990 U.S. Census. It is also available as part of Machine Learning Crash Course created by Google: [LINK](https://download.mlcc.google.com/mledu-datasets/california_housing_train.csv). Tou can find data description [HERE](https://developers.google.com/machine-learning/crash-course/california-housing-data-description)

## Limitations

Jupyter on Golem is in its infancy stage. Consequently, it has many limitations You should be aware of. The most imporant are listed below:

* Currently Golem Network does not support easy way to utilize provider's GPU. Consequently, Jupyter on Golem is limited to utilize RAM, Disk space and CPU from the provider's resources.
* Data sets, results and other files need to be downloaded and uploaded via Requestor (i.e. Jupyter on Golem). In other words if You want to use some data sets from the Internet you need to download it locally first and then push into the provider host with `%upload` command.
* Installing Python libraries is limited to PyPI with PIP.
* Using `%pip install` does not present live progress output. However, there is a spinner icon to let You know that installation process in ongoing.
* Outbound Internet access is limited to the most important services like above mentioned PyPI with PIP. Don't be surprised that other calls might not work.
* It might take a while to `%connect` to provider. Specifics depends on many factors, yet usually it takes something between 3 up to 10 minutes. You can also use `timeout=10m` paremeter to define how much are you willing to wait. In general we recommend to use this time to get a tea or coffee ;)
* Currently only post-paid payments are supported. Single payment transaction is initialized after Requestor (Jupter on Golem) disconnects from the Provider.
* Golem Network is a free market where You receive multiple offers for a single demand. Multiple strategies can be applied to chose the offer. However, currently Jupyter on Golem supports only random strategy (i.e. choosing the random option among all offers received).

## Feedback

Did You try Jupyter on Golem? We would love to get to know your thoughts! Please give us your feedback [HERE](https://qkjx8blh5hm.typeform.com/JoGfeedback)

## Support

If you experience problems with Jupyter on Golem, You can try to get some help in the following places:
* **jupyter-on-golem-discussion** channel on our Golem Network [Discord Server](https://chat.golem.network/)
* [Github Repository](https://github.com/golemfactory/golem-kernel-python) of the project

## Known Issues

Below You will find list of known issues and potential solutions:

### 1. Unsuccessful funding on Goerli Testnet:

Sometimes after using `%fund goerli` command, You will get **"Funding failed"** output. It might happen due to delay between requesting tETH and tGLM by Jupyter on Golem. In most cases, it should be enough to just wait a few minutes. Afterwards, type `%status` command and You should be able to see that both tETH and tGLM have arrieved to Your wallet.

## Terms and Conditions

By using Jupyter on Golem you agree to be bound by the terms described in Golem Network [Disclaimer](https://www.golem.network/disclaimer), [User Interaction Guidelines](https://www.golem.network/uig) and [Privacy Policy](https://www.golem.network/privacy).

## Legal Statements

“Jupyter” and the Jupyter logos are trademarks or registered trademarks of NumFOCUS.
