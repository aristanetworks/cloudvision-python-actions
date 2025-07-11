# CloudVision Custom Python3 Actions

**Note**: Go to the [releases page](https://github.com/aristanetworks/cloudvision-python-actions/releases) or check out release branches (e.g. 2022.2) for scripts compatible with your CloudVision version.
Actions are forwards compatible within a CloudVision release, with new releases in a maintenance train only being made if bugs are addressed. If a release does not exist for the your latest running maintenance version of CloudVision, then the latest release from that given train has the most up-to-date actions and will work on your installation, e.g. 2023.1.0 artifacts work for CloudVision version 2023.1.1, 2023.1.2, etc.
CVaaS users are directed to install the latest release artifacts on their systems.

## Overview

Here are a number of example Python3 scripts in action pack form to serve as reference to those designing their own user scripts.

**Please note that scripts in the trunk branch may not be compatible with your installation of CloudVision. Please refer to the branch/[release](https://github.com/aristanetworks/cloudvision-python-actions/releases) corresponding to your CloudVision version for compatible scripts.**

These action packs are also able to be uploaded to a CloudVision cluster, where they can be used as needed, or duplicated and customised.
Those action packs listed in `bundled.yaml` are **_bundled by default_** with CloudVision on-premises installations.

## How to Upload Action Packs to a CloudVision cluster

The Packaging UI under the general settings can be used to add or remove actionpacks downloaded from the [releases page](https://github.com/aristanetworks/cloudvision-python-actions/releases).

## Creating artifacts from source

It is also possible to create the artifacts by hand from the source code and upload them via the packaging UI. The following steps outline this approach.

### Pre-requisites

* `git`
* `tar`
* `make` (optional, used for tarring up multiple packs at once)

### Steps

#### Prepare the action pack

* Clone the github repo into a folder using `git clone`
* (Optional) Check out the branch/tag associated with the wanted release e.g. `git checkout 2024.2`
* `tar` up the action pack while you are in the `actionpacks` directory (or equivalent directory). The name of the tar is not important, but it is good practice to use the same name as the as the directory you are tarring, and include the version string.
  * Run `make actionpacks` will tar up all action packs in the repository and add them into the `gen` folder (See Makefile for further details)

### Example

**Note**: This example is using the `event-monitor` action pack, which is bundled by default, for a CloudVision `2024.3.*` installation.

#### Creating the action pack tar

* Clone the repo, enter it, and `checkout` the version of CloudVision that is being run

``` Shell
> git clone git@github.com:aristanetworks/cloudvision-python-actions.git
...
> cd cloudvision-python-actions
> git checkout 2024.3
```

* `tar` up the desired action pack as shown below (or run `make actionpacks` to tar all packs and put them into the `gen` folder):

``` Shell
> tar -C cloudvision-actions cvf --disable-copyfile event-monitor-action-pack_1.0.0.tar event-monitor-action-pack
a event-monitor-action-pack
a event-monitor-action-pack/config.yaml
a event-monitor-action-pack/event-monitor
a event-monitor-action-pack/event-monitor/config.yaml
a event-monitor-action-pack/event-monitor/script.py
```