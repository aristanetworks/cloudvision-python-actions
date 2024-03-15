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

### CloudVision 2023.1+ / CVaaS

From CloudVision version 2023.1 (or on CVaaS), the Packaging UI under the general settings can be used to add or remove actionpacks downloaded from the [releases page](https://github.com/aristanetworks/cloudvision-python-actions/releases).

### CloudVision 2022.3 or before

For on-premises installation versions 2022.3 or before, the following approach needs to be taken to install actionpacks.
(This approach can alternatively be used for on-premises installations of version 2023.1 onwards instead of the Packaging UI as well)

**Note**: The following method of uploading scripts is not available for CVaaS customers.

### Pre-requisites

* `git`
* `tar`
* `make` (optional, used for tarring up multiple packs at once)

### Steps

#### Prepare the action pack

* Clone the github repo into a folder using `git clone`
* Check out the branch/tag associated with the wanted release e.g. `git checkout 2022.2`
* `tar` up the action pack while you are in the `actionpacks` directory (or equivalent directory). The name of the tar is not important, but it is good practice to use the same name as the as the directory you are tarring, and include the version string.
  * If using an OS X (Apple) machine, be sure to include the `--disable-copyfile` flag when running tar, or the actionpack may not be accepted. This flag is not available on Linux machines
  * Alternatively (in a 2022 or beyond release), running `make actionpacks` (or `make actionpacks-mac` on an OS X system) will tar up all action packs in the repository and add them into the `gen` folder

**Note**: For CloudVision version 2023.1 onwards, check the [releases page](https://github.com/aristanetworks/cloudvision-python-actions/releases) to download the prebuilt tar files directly.

#### Upload the actionpack

* Use `scp` to copy the tar file over to any of the cvp nodes in the system.
* On the cvp node, upload the action pack via the the `actionpack_cli`

**Note**: This will upload the action pack as the `aerisadmin` user, which means that only the `aerisadmin` user will be able to modify or delete them (copies can still be made and modified/deleted by any user authorised to create actions).

To _avoid_ making an aeris admin gated script, it is advised to create a new action, and to copy the script and arguments wanted from the example in question.

### Example

**Note**: This example is using the `event-monitor` action pack, which is bundled by default, for a CloudVision `2022.2.*` installation, with tar being run on an OS X machine.

For CloudVision version 2023.1 onwards, check the [releases page](https://github.com/aristanetworks/cloudvision-python-actions/releases) to download the prebuilt tar files such as `event-monitor-action-pack` directly.

#### Creating the action pack tar

* Clone the repo, enter it, and `checkout` the version of CloudVision that is being run

``` Shell
> git clone git@github.com:aristanetworks/cloudvision-python-actions.git
...
> cd cloudvision-python-actions
> git checkout 2022.2
```

* `tar` up the desired action pack as shown below (or run `make actionpacks` to tar all packs and put them into the `gen` folder):

``` Shell
> tar cvf --disable-copyfile event-monitor-action-pack_1.0.0.tar event-monitor-action-pack
a event-monitor-action-pack
a event-monitor-action-pack/config.yaml
a event-monitor-action-pack/event-monitor
a event-monitor-action-pack/event-monitor/config.yaml
a event-monitor-action-pack/event-monitor/script.py
```

#### Uploading the action pack

* `scp` the .tar action pack over to the cvp node

* `ssh` onto the node and run `/cvpi/tools/actionpack_cli event-monitor-action-pack_1.0.0.tar`


### Removing an action pack uploaded via `actionpack_cli`
Running the following curl command from the cli of the CloudVision instance will remove an actionpack from the system.
`curl -X DELETE https://localhost:8443/cvpservice/package/v1/packages/<action-pack-id> -k --cacert <cvp-ca-cert> --cert <aerisadmin-cert> --key <aerisadmin-key>`
Where the `action-pack-id` will be the name of the tar file uploaded through `actionpack_cli`
**Note**: From 2023.1, the Packaging UI in general settings can alternatively be used to remove actionpacks.
