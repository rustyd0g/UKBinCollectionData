# Midlothian HACS testing branch

This branch tests the Midlothian govService API implementation through the
existing Home Assistant integration. The upstream PR branch is
`MidlothianCouncil-GranicusAPI-PR`; these HACS-only changes should not be merged
into that PR.

- Testing branch: `MidlothianCouncil-GranicusAPI-HA`
- Fork: <https://github.com/rustyd0g/UKBinCollectionData>
- Integration version: `0.173.5-dev.20261113`
- Scraper package version: `0.173.5.dev20261113`
- Pinned package/configuration source: `2798b821ad107ef5c5a763f703f453345f63fa5e`

The integration manifest installs the scraper from a commit-pinned GitHub ZIP,
not the normal PyPI release. This needs no Git executable in Home Assistant.
The council configuration URL uses the same commit, so Midlothian setup asks
for a UPRN and does not require Selenium.

The integration domain remains `uk_bin_collection`. This replaces the code of
an existing UK Bin Collection installation; it is not a second integration
that can run alongside the official one. Other configured councils also use
this pinned library version while testing.

## Install using HACS

1. Take a Home Assistant backup before changing the installed integration.
2. If your current Midlothian entry uses only postcode and house number,
   disable that entry in **Settings > Devices & services** and keep it for
   rollback. The existing reconfiguration form cannot add a missing UPRN
   field; create a separately named test entry after installing this build.
3. If the official `robbrad/UKBinCollectionData` repository is installed in
   HACS, remove that installation from HACS before installing the fork. This
   removes integration files: install the fork before restarting Home
   Assistant. Keep your existing UK Bin Collection configuration entries in
   **Settings > Devices & services**; do not delete them just to switch code.
4. In HACS, open **Custom repositories** and add
   `https://github.com/rustyd0g/UKBinCollectionData` as an **Integration**.
   Use the repository URL, not a `/tree/` branch URL.
5. Download the fork. The initial download may use its normal master/release;
   select the testing branch in the next step before restarting.
6. Find the HACS update entity for the **rustyd0g fork**. In Home Assistant's
   **Developer tools > Actions**, call the following action, replacing the
   example entity ID with that actual update entity:

   ```yaml
   action: update.install
   target:
     entity_id: update.replace_with_fork_update_entity
   data:
     version: MidlothianCouncil-GranicusAPI-HA
   ```

   HACS supports public branches and full commit SHAs through this action.
   The entity must track the fork: using the official repository's entity
   cannot install a branch that exists only in the fork. A GitHub prerelease
   or a change to the default branch is not needed.
7. Restart Home Assistant and allow its dependency installation to finish.
8. If you already have a working UPRN-based Midlothian entry, it can keep
   using that UPRN. Otherwise add a new **UK Bin Collection Data (Midlothian
   Test)** entry, use a distinct name such as **Midlothian API Test**, select
   **Midlothian**, and supply your property's UPRN. No Selenium server is
   needed for Midlothian.

If the setup still asks for postcode/house number and a Selenium server, check
that the test branch was downloaded, restart completed, and the pinned
configuration URL is reachable. Check this in a new entry: reconfiguring an
old entry continues to show only its previously stored address fields.
Check Home Assistant logs for dependency
installation failures if the integration does not load.

Only let one HACS repository manage `custom_components/uk_bin_collection`.
Avoid installing an official update over the test build while testing.

## Return to the official integration

Disable the separately named UPRN test entry, remove the fork installation
from HACS, download the official `robbrad/UKBinCollectionData` integration,
then restart Home Assistant. Re-enable the original Midlothian entry you
kept. If you did not keep an original entry and the official
scraper still requires postcode/house number, add a new entry using those
fields; the reconfiguration form cannot add them to a UPRN-only entry.

The fork package deliberately uses a development version below `0.173.5`.
It does not satisfy the official integration's `uk-bin-collection>=0.173.5`
requirement, so Home Assistant will replace it with a stable PyPI package
when you restore the official integration.

## Refresh this test build

The dependency and configuration URLs are immutable pins. Updating only the
scraper file on this branch will not change the code Home Assistant installs.
For another test build:

1. Bring the desired scraper changes onto this branch.
2. Give the test library a new development version and commit those changes.
3. Point the manifest requirement and `INPUT_JSON_URL` at that source commit.
4. Bump the integration's test version, update this document, and commit.
5. Push the branch and repeat the HACS `update.install` action, then restart.

Do not create release tags merely to install this branch: the repository's
normal tag workflow publishes packages to PyPI and builds Docker images.

## References

- [HACS custom repositories](https://www.hacs.xyz/docs/faq/custom_repositories/)
- [HACS branch/commit installation](https://www.hacs.xyz/docs/use/entities/update/#install-action)
- [Home Assistant integration requirements](https://contributors.home-assistant.io/core/integrations/manifest/#requirements)
