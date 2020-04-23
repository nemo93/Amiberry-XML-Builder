# About The Amiberry XML Builder 
The Amiberry XML Builder is an automated tool which will routinely scan for available Amiga WHDLoad Packs (Games) and pre-set 
various options to be used in conjunction with the [Amiga emulator Amiberry](https://github.com/midwan/amiberry) to aid with games 
compatibility and usability. This tool will be storing the end results in an output XML file named after 
[whdload_db.xml](https://raw.githubusercontent.com/nemo93/Amiberry-XML-Builder/master/whdload_db.xml).

If the above sounds like another language, or makes no sense, please consider visiting https://github.com/midwan/amiberry/wiki to 
learn more about why this tool exists.

# Credits
This tool is the work of [@Horace And The Spider](https://github.com/HoraceAndTheSpider) and 
[@osvaldolove](https://github.com/osvaldolove). This Github is a simple fork with few modifications to ensure
this project goes on. This tool would have no meaning without the hard work done by [@midwan](https://github.com/midwan/amiberry) 
from the [Amiberry emulator](https://github.com/midwan/amiberry) as well as from all
[the contributors](https://github.com/midwan/amiberry/blob/master/.github/CONTRIBUTING.md#contributors).
All credits must go to the people above.

# What is this GitHub for? 
This GitHub exists to ensure that the host machine for this tool has a central repostiry for it's information, and to give Amiberry
somewhere to download the latest XML.

It is intended to be a route for users to supply updated 'community led' proposed changes. However, to achieve this across over 
3000+ supported games, information provided needs to be clear and concise.

# Acceptable ways to submit issues

**Please read before posting any issues on this GitHub**

There are certain rules which must be adhered to when posting proposed changes which will be applied to the repo and eventually 
filter to the XML. Faiulre to follow these will result in requests being ignored and eventually deleted.

1. Post one issue per game please.

2. Clearly identify the game, and version of the game you are working from
* Supply the exact filename in use from the 'RetroPlay' packs
* Supply from the existing XML the <subpath> tag for a shared name, which will allow the setting to be applied on future versions.
* e.g. "Change requested for Bloodwych_v2.51_0439.lha , subpath: Bloodwych

3. Clearly identify the changes to be made, and whether any existing settings should be removed.
* e.g. "Current SCREEN WIDTH is set to 256 and this should be set to 262.

4. State the reason for the change

* e.g. "This fixes a screen issue and allows the menu to be viewed correctly"

5. Do *NOT* provide an updated XML file or sections of the XML file.
