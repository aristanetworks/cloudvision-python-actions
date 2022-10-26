# CloudVision Custom Python3 Actions

## **Note**: This is only available from CloudVision 2021.3.0 onwards

## **Note**: Check out release branches (e.g. 2022.2) for scripts compatible with that CloudVision version

## Overview

Here are a number of example Python3 scripts in action pack form to serve as reference to those designing their own user scripts.

**Please note that scripts in the trunk branch may not be compatible with your installation of CloudVision. Please refer to the branch corresponding to your Cloudvision version for compatible scripts.**

These action packs are also able to be uploaded to a CloudVision cluster, where they can be used as needed, or duplicated and customised.
Those action packs listed in `bundled.yaml` are _bundled by default_ to CloudVision.

## How to Upload Action Packs to a CloudVision cluster

**Note**: This is method of uploading scripts is not yet available for CVaaS customers.

### Pre-requisites

* `git`
* `tar`
* `make` (optional, used for tarring up multiple packs at once)

### Steps

* Clone the github repo into a folder using `git clone`
* Check out the branch/tag associated with the wanted release e.g. `git checkout 2022.2`
* `tar` up the action pack while you are in the `actionpacks` directory (or equivalent directory). The name of the tar is not important, but it is good practice to use the same name as the as the directory you are tarring, and include the version string.
  * If using an OS X (Apple) machine, be sure to include the `--disable-copyfile` flag when running tar, or the actionpack may not be accepted. This flag is not available on Linux machines
  * Alternatively (in a 2022 or beyond release), running `make actionpacks` (or `make actionpacks-mac` on an OS X system) will tar up all action packs in the repository and add them into the `gen` folder
* Use `scp` to copy the tar file over to any of the cvp nodes in the system.
* On the cvp node, upload the action pack via the the `actionpack_cli` tool

**Note**: This will upload the action pack as the `aerisadmin` user, which means that only the `aerisadmin` user will be able to modify or delete them (copies can still be made and modified/deleted by any user authorised to create actions).

To _avoid_ making an aeris admin gated script, it is advised to create a new action, and to copy the script and arguments wanted from the example in question.

### Example

**Note**: This example is using the `event-monitor` action pack, which is bundled by default, for a CloudVision `2022.2.*` installation, with tar being run on an OS X machine

* Clone the repo, enter it, and `checkout` the version of CloudVision that is being run

``` Shell
> git clone git@github.com:aristanetworks/cloudvision-python-actions.git
...
> cd cloudvision-python-actions
> git checkout 2022.2
```

* `tar` up the desired action pack as shown below (or run `make actionpacks` to tar all packs and put them into the `gen` folder):

``` Shell
> tar --disable-copyfile cvf event-monitor-action-pack_1.0.0.tar event-monitor-action-pack
a event-monitor-action-pack
a event-monitor-action-pack/config.yaml
a event-monitor-action-pack/event-monitor
a event-monitor-action-pack/event-monitor/config.yaml
a event-monitor-action-pack/event-monitor/script.py
```

* `scp` the .tar action pack over to the cvp node

* `ssh` onto the node and run `/cvpi/tools/actionpack_cli event-monitor-action-pack_1.0.0.tar`
