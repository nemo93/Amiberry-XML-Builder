import sys
import lhafile
import os
from pathlib import Path
import math
import argparse
import hashlib
import openretroid
import datetime
import platform
import tempfile
from utils import text_utils
from whdload import whdload_slave
from slave_lha.parse_lha.read_lha import LhaSlaveArchive

import ftputil
import urllib.request
import shutil
from lxml import etree
import xml.parsers.expat

# =======================================
# Methods
# =======================================
def sha1(fname):
    hash_sha1 = hashlib.sha1()
    with open(str(fname), "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()


def value_list(in_file, game_name):
    file_name = "settings/" + in_file

    if os.path.isfile(file_name) is False:
        return ""

    with open(file_name) as f:
        content = f.readlines()
        content = [x.strip() for x in content]
    f.close()

    answer = ""

    for this_line in content:
        if not this_line == "":
            this_word = this_line.split()
            if this_word[0] == game_name:
                answer = this_word[1]
                break

    return answer

def check_list(in_file, game_name):

    temp_game = game_name

    if text_utils.right(temp_game.lower(),4) == ".iso" or text_utils.right(temp_game.lower(),4) == ".cue":
        temp_game = text_utils.left(temp_game,len(temp_game)-4)
        
    if text_utils.right(temp_game.lower(),4) == ".adf" or text_utils.right(temp_game.lower(),4) == ".hdf":
        temp_game = text_utils.left(temp_game,len(temp_game)-4)
    
    file_name = "settings/" + in_file

    if os.path.isfile(file_name) is False:
        return False

    with open(file_name) as f:
        content = f.readlines()
        content = [x.strip() for x in content]
    f.close()

    answer = False

    for this_line in content:
        if this_line == temp_game:
            answer = True
            break

    return answer

# For XML sorting
def sortchildrenby(parent, attr):
    parent[:] = sorted(parent, key=lambda child: child.get(attr))

# For XML validation
def parsefile(file):
    parser = xml.parsers.expat.ParserCreate()
    parser.Parse(file)


# =======================================
# main section starting here...
# =======================================

script_version = '0.8'
print()
print(
    text_utils.FontColours.BOLD + text_utils.FontColours.OKBLUE + "HoraceAndTheSpider and osvaldolove's" + text_utils.FontColours.ENDC + text_utils.FontColours.BOLD +
    " Amiberry XML Builder" + text_utils.FontColours.ENDC + text_utils.FontColours.OKGREEN + " ("+script_version+")" + text_utils.FontColours.ENDC + " | " + "" +
    text_utils.FontColours.FAIL + "www.ultimateamiga.co.uk" + text_utils.FontColours.ENDC)
print()

# =======================================
# command-line stuff | not needed now
# =======================================
"""
parser = argparse.ArgumentParser(description='Create Amiberry XML for WHDLoad Packs.')

parser.add_argument('--scandir', '-s',                         # command line argument
                    help='Directories to Scan',
                    default='/home/pi/RetroPie/roms/amiga/'    # Default directory if none supplied
#                    default = "/media/MARVIN/Geek/WHDLoad/"
                    )

parser.add_argument('--refresh', '-n',                      # command line argument
                    action="store_true",                    # if argument present, store value as True otherwise False
                    help="Full XML refresh"
                    )

parser.add_argument('--forceinput', '-f',                  # command line argument
                    action="store_true",                    # if argument present, store value as True otherwise False
                    help="Force -S to be used on OSX, and ignore timecheck"
                    )

# Parse all command line arguments
args = parser.parse_args()

# Get the directories to scan (or default)
# yeah, i shouldnt do this, but i'm lazy, so i will.
if platform.system() == "Darwin" and args.forceinput != True:
        input_directory = "/Volumes/Macintosh HD/Users/horaceandthespider/Google Drive/Geek/Shared Pi Games/amiga/_Standard/"
else:
        input_directory = args.scandir
"""
# =======================================
# Get recently updated packages from FTP
# =======================================
input_directory = '/tmp' # Directory where packages will be downloaded to
ftphost = ''
ftplogin = 'ftp'
ftppass = ''
ftpcon = ftputil.FTPHost(ftphost,ftplogin,ftppass)
ftproot = ''
ftpdemo = ''
ftpgames = ''
gamelist = []
whdbfile = 'whdload_db.xml'
whdbtmp = 'whdload_db.tmp'
whdbbak = 'whdload_db.xml.bak'

# filename pattern for what the script is looking for
fpattern = '.lha'

# Timecheck the original XML
whdbtime = datetime.datetime.fromtimestamp(os.path.getmtime(whdbfile)).date()
curdate = datetime.date.today()

# get the nb of days since last update of whdbfile
getdelta = (curdate - whdbtime).days

# UTC time minus 'getdelta' in seconds 
# any files created/modified since then will have to be processed
utc_datetime_delta = datetime.datetime.utcnow()-datetime.timedelta(days=getdelta)

# also get whdbfile size before modification
whdsize = Path(whdbfile).stat().st_size

# logging into FTP and get a list of recently modified files
with ftpcon as host: 
    ftpcon.use_list_a_option = 'False'
    recursive = host.walk(ftproot,topdown=True,onerror=None)
    for root,dirs,files in recursive:
        if root.find(ftpdemo) > 0 or root.find(ftpgames) > 0: # ugly as f*ck
          for name in files:
            fpath = host.path.join(root, name)
            fext = Path(fpath).suffix # get file extension
            get_mtime = host.stat(fpath).st_mtime 
            file_mtime = datetime.datetime.utcfromtimestamp(get_mtime)
            if file_mtime >= utc_datetime_delta and fext == fpattern: 
              if fpath not in gamelist:
                gamelist.append(fpath)

host.close()

for item in gamelist:
    try:         
      print("retrieving file:", os.path.basename(item) + " to " + input_directory)  
      urllib.request.urlretrieve('ftp://'+ftplogin+':'+ftppass+'@'+ftphost+item, input_directory + "/" + os.path.basename(item))
    except:
      print("WARNING: File could not be downloaded")

# =======================================
# Backup before doing naughty stuff!!
# =======================================
if not os.path.isfile(whdbbak) or whdsize >= os.stat(whdbbak).st_size:
    shutil.copy2(whdbfile, whdbbak)
    whdbaksize = Path(whdbbak).stat().st_size

# Setup Bool Constant for XML refresh / default to False
#FULL_REFRESH  = args.refresh
FULL_REFRESH  = False

hash_algorithm = 'SHA1'
count = 1

#XML_HEADER= '<?xml version="1.0" encoding="UTF-8"?>' + chr(10)
#XML_HEADER = XML_HEADER + '<whdbooter timestamp="' + datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S") + '">' + chr(10)
XML_HEADER = '<whdbooter timestamp="' + datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S") + '">' + chr(10)
XML_OLD = ""

if FULL_REFRESH == False:    
    text_file = open(whdbfile, "r")
    XML_OLD = text_file.read()
    text_file.close()

    a = XML_OLD.find("<whdbooter")
    for b in range(a , a+100):
        if XML_OLD[b]==">":
            break

    c = XML_OLD.find("</whdbooter")            

    XML_OLD = XML_OLD[b+2:c]
    # print(XML_OLD)
    
#XML = ''
#XML_FOOTER = "</whdbooter>" + chr(10)
XML = ''
XML_FOOTER = '</whdbooter>'

ERROR_MSG    = 'Problem file log: ' + datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S") + '' + chr(10)
COMPLETE_MSG = 'Scanned file log: ' + datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S") + '' + chr(10)



for file2 in Path(input_directory + "/").glob('**/*.lha'):
    archive_path = str(file2)
    this_file = os.path.basename(archive_path)

    # check for a skip, and that its value for skipping
    if (FULL_REFRESH==False and XML_OLD.find('<game filename="' + this_file[0:len(this_file)-4].replace("&", "&amp;") + '"')>-1):        
        print("Skipping: " + text_utils.FontColours.OKBLUE + text_utils.FontColours.BOLD  + this_file + text_utils.FontColours.ENDC)
        COMPLETE_MSG = COMPLETE_MSG + "Skipped: " + this_file + chr(10)
    elif text_utils.left(this_file,2)=="._":
        ...
        count = count - 1
    else:
        print()
        print("Processing: " + text_utils.FontColours.FAIL + text_utils.FontColours.BOLD  + this_file + text_utils.FontColours.ENDC)
        
        try:
                slave_archive = LhaSlaveArchive(archive_path, hash_algorithm)
                file_details = openretroid.parse_file(archive_path)
                
                slave_archive.read_lha()
                ArchiveSHA = sha1(file2)
              
                # Defaults
                HW_CHIPSET = "ECS"
                HW_PROCESSOR = "68020"
                HW_SPEED = "7"
                HW_CHIP = .5
                HW_FAST = 0
                HW_Z3 = 0
                
                hardware = ""
                SLAVE_XML=""
                first_slave=""
                UUID = ""
                n=1
                default_slave = ""
                default_slave_found = False
                
                UUID = file_details['uuid']                    
                print("Openretro URL: " + text_utils.FontColours.UNDERLINE + text_utils.FontColours.OKBLUE +  "http://www.openretro.org/game/{}".format(UUID) + text_utils.FontColours.ENDC)
                #print("Variant UUID: {}".format(file_details['uuid']))
                print()
                # we should get the default slave here, so that we only select it if it

                def_msg = ""
                
                # default slave
                default_slave = value_list("WHD_DefaultSlave.txt", text_utils.left(this_file,len(this_file) - 4))
                if default_slave != "":
                     def_msg = " (Lookup from list using File Name)"                               

                # From here, we need to process WHDLoad header information out of the slave files!
                for slave in slave_archive.slaves:
                    slave.get_hash()
                    print(text_utils.FontColours.BOLD + '  Slave Found: ', end='')
                    print(text_utils.FontColours.OKBLUE + slave.name + text_utils.FontColours.ENDC)
                    #print( "{} Hash: ".format(slave.hasher.name.upper()), end='')
                    #print(slave.hash_digest + text_utils.FontColours.ENDC)

                    if default_slave != "":
                        if  slave.name.find(default_slave) >0:
                            default_slave_found = True
                        
                # extract the slave as a temp file
                    fp = tempfile.NamedTemporaryFile()
                    fp.write(slave.data)
                    fp.seek(0)
                    this_slave = whdload_slave.whdload_factory(fp.name)
                    fp.close()

                    
              #     we could work something out here later... but maybe it doesnt even matter here
              #     we can use the 'sub path' of slave.name to get the old UAE Config Maker folder name
                    slave_path = os.path.dirname(slave.name)
                    sub_path = text_utils.left(slave.name,len(slave_path) - len(slave.name))
                    full_game_name = text_utils.make_full_name(sub_path)

                    #print("check settings: "+sub_path)
                    if first_slave == "":
                        first_slave = slave.name.replace(slave_path +"/","")
                        
                # Extract H/W settings from the slaves
                    for slave_flag in this_slave.flags:
                        #print(slave_flag)
                        if slave_flag == "Req68020":
                            HW_PROCESSOR = "68020"
                            
                        if slave_flag == "ReqAGA":
                            HW_CHIPSET = "AGA"
                            HW_SPEED = "14"

              # where we have multiple slaves, we will set the requirements as the highest ones found
              # e.g. the one needing most memory etc

                    # round up any wierd chipram values       
                    temp_chip_ram = this_slave.base_mem_size/1048576
                    for i in range(0, 2):
                        low_ram = int(math.pow(2, i-1))
                        high_ram = int(math.pow(2, i ))           
                        if temp_chip_ram > low_ram and temp_chip_ram < high_ram:
                            temp_chip_ram = high_ram

                    # update the value if the highest slave requirement
                    if temp_chip_ram > HW_CHIP:
                            whd_chip_ram = temp_chip_ram
                            
                    # round up any wierd fastram values       
                    temp_fast_ram = this_slave.exp_mem/1048576
                    for i in range(0, 5):
                        low_ram = int(math.pow(2, i-1))
                        high_ram = int(math.pow(2, i )) 
                        if temp_fast_ram > low_ram and temp_fast_ram < high_ram:
                            temp_fast_ram = high_ram

                    # update the value if the highest slave requirement
                    whd_fast_ram = 0
                    if temp_fast_ram > HW_FAST:
                            whd_fast_ram = temp_fast_ram

                    # we use the name of the 'last' slave, if there is only one
                    last_slave = slave.name.replace(slave_path +"/","")

                    SLAVE_XML = SLAVE_XML + chr(9)+ chr(9)+ '<slave number="' + str(n) + '">' + chr(10)
                    SLAVE_XML = SLAVE_XML + chr(9)+ chr(9)+ chr(9) + '<filename>' + (slave.name.replace(slave_path +"/","")).replace("&", "&amp;") + '</filename>' + chr(10)
                    SLAVE_XML = SLAVE_XML + chr(9)+ chr(9)+ chr(9) + '<datapath>' + (this_slave.current_dir).replace("&", "&amp;") + '</datapath>' + chr(10)
                    if (this_slave.config) is not None:
                        SLAVE_XML = SLAVE_XML + chr(9)+ chr(9)+ chr(9) + '<custom>'  + chr(10)

                        for configs in this_slave.config:
                            if configs is not None:
                                SLAVE_XML = SLAVE_XML + chr(9)+ chr(9)+ chr(9) + ((configs.replace("<","")).replace(">","")).replace("&", "&amp;") + chr(10)


                        SLAVE_XML = SLAVE_XML + chr(9)+ chr(9)+ chr(9) + '</custom>'  + chr(10)
                        
                    SLAVE_XML = SLAVE_XML + chr(9)+ chr(9)+ '</slave>'  + chr(10)
                    n=n+1
                    
                    
                # end of slave checking

                print()
                print("Game name: " + text_utils.FontColours.HEADER + full_game_name + text_utils.FontColours.ENDC)
                print("Lookup Name: " + text_utils.FontColours.HEADER + sub_path + text_utils.FontColours.ENDC)
                
                # resurn of the default slave!
                if default_slave_found == False:
                        default_slave = ""
                        
                if len(slave_archive.slaves) == 1 and default_slave=="":
                        default_slave = last_slave
                        def_msg = " (Only slave in archive search)"

                elif default_slave=="":
                        default_slave = first_slave
                        def_msg = " (First slave in archive search)"
                        
                print("Default Slave: " + text_utils.FontColours.HEADER + default_slave + text_utils.FontColours.WARNING + def_msg + text_utils.FontColours.ENDC)
                # get what settings we can, based on the name lookup in old Config Maker Files


                # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #


                # '======== DISPLAY SETTINGS =======
                # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # ' screen Y/X Offsets

                screen_offset_y = value_list("Screen_OffsetY.txt", sub_path)
             #   screen_offset_x = value_list("Screen_OffsetX.txt", sub_path)

                # ' screen heights { 200, 216, 240, 256, 262, 270 };
                HW_HEIGHT = ""
                if check_list("Screen_Height_270.txt", sub_path) is True:
                                HW_HEIGHT = "270"
                if check_list("Screen_Height_262.txt", sub_path) is True:
                                HW_HEIGHT = "262"
                if check_list("Screen_Height_256.txt", sub_path) is True:
                                HW_HEIGHT = "256"
                if check_list("Screen_Height_240.txt", sub_path) is True:
                                HW_HEIGHT = "240"
                if check_list("Screen_Height_224.txt", sub_path) is True:
                                HW_HEIGHT = "224"
                if check_list("Screen_Height_216.txt", sub_path) is True:
                                HW_HEIGHT = "216"
                if check_list("Screen_Height_200.txt", sub_path) is True:
                                HW_HEIGHT = "200"

                # ' screen widths  { 320, 352, 384, 640, 704, 768 };
                HW_WIDTH = ""
                if check_list("Screen_Width_320.txt", sub_path) is True:
                                HW_WIDTH = "320"
                if check_list("Screen_Width_352.txt", sub_path) is True:
                                HW_WIDTH = "352"
                if check_list("Screen_Width_384.txt", sub_path) is True:
                                HW_WIDTH = "384"
                if check_list("Screen_Width_640.txt", sub_path) is True:
                                HW_WIDTH = "640"
                if check_list("Screen_Width_704.txt", sub_path) is True:
                                HW_WIDTH = "704"
                if check_list("Screen_Width_768.txt", sub_path) is True:
                                HW_WIDTH = "768"
                                
                # ' extras
                HW_NTSC = ""
                if check_list("Screen_ForceNTSC.txt", sub_path) is True:
                     HW_NTSC = "TRUE"       
                elif this_file.find("NTSC") > -1:
                     HW_NTSC = "TRUE" 
                            
                # '======== CONTROL SETTINGS =======
                # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # ' mouse / mouse 2 / CD32

                use_mouse1 = check_list("Control_Port0_Mouse.txt", sub_path)
                use_mouse2 = check_list("Control_Port1_Mouse.txt", sub_path)
                use_cd32_pad = check_list("Control_CD32.txt", sub_path)


                # quick clean-up on WHDLoad memory requirements
                whd_z3_ram = 0

                if whd_fast_ram>8:
                    whd_z3_ram = whd_fast_ram
                    whd_fast_ram = 0

                chip_ram = 2
                fast_ram = 4
               
                
                old_chip_ram = chip_ram
                for i in range(0, 4):
                    chip_ram = int(math.pow(2, i)) / 2
                    if chip_ram >= 1:
                                    chip_ram = int(chip_ram)

                    if check_list("Memory_ChipRam_" + str(chip_ram) + ".txt", sub_path) is True:
                                    chip_ram = int(chip_ram * 2)
                                    break
                    chip_ram = old_chip_ram
                    # whd chip-memory overwrite
                if whd_chip_ram >= chip_ram: chip_ram = whd_chip_ram


                # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # ' when we want different fast ram!!

                old_fast_ram = fast_ram
                for i in range(0, 4):
                    fast_ram = int(math.pow(2, i))
                    if check_list("Memory_FastRam_" + str(fast_ram) + ".txt", sub_path) is True:
                        break
                    fast_ram = old_fast_ram

                # whd fast-memory overwrite
                if whd_fast_ram >= fast_ram and whd_fast_ram <= 8 : fast_ram = whd_fast_ram

                # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # ' when we want different Z3 ram!!

                for i in range(0, 8):
                    z3_ram = int(math.pow(2, i))
                    if check_list("Memory_Z3Ram_" + str(z3_ram) + ".txt", sub_path) is True:
                        break
                    z3_ram = 0

                    # whd z3-memory overwrite
                if whd_fast_ram >= z3_ram and whd_fast_ram > 8 : z3_ram = whd_chip_ram


                # '======== CHIPSET SETTINGS =======
                # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # ' sprite collisions

                HW_SPRITES = ""
                if check_list("Chipset_CollisionLevel_playfields.txt", sub_path) is True:
                                HW_SPRITES = "PLAYFIELDS"
                if check_list("Chipset_CollisionLevel_none.txt", sub_path) is True:
                                HW_SPRITES = "NONE"
                if check_list("Chipset_CollisionLevel_sprites.txt", sub_path) is True:
                                HW_SPRITES = "SPRITES"
                if check_list("HW_SPRITES.txt", sub_path) is True:
                                HW_SPRITES = "FULL"

                # ' blitter    
                HW_BLITS = ""        
                if check_list("Chipset_ImmediateBlitter.txt", sub_path) is True:
                    HW_BLITS = "IMMEDIATE"
                if  check_list("Chipset_NormalBlitter.txt", sub_path) is True:
                    HW_BLITS = "NORMAL"
                if  check_list("Chipset_WaitBlitter.txt", sub_path) is True:
                    HW_BLITS = "WAIT"

                HW_FASTCOPPER = ""
                if not check_list("Chipset_NoFastCopper.txt", sub_path) is False:
                        HW_FASTCOPPER = "FALSE"

                if check_list("Chipset_FastCopper.txt", sub_path) is True:
                    HW_FASTCOPPER = "TRUE"

                

                # '======== CPU SETTINGS =======
                # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                # ' max emu speed
                HW_SPEED = ""
                if check_list("CPU_MaxSpeed.txt", sub_path) is True:
                                HW_SPEED = "MAX"
                if check_list("CPU_RealSpeed.txt", sub_path) is True:
                                HW_SPEED = "REAL"
                # ' clock speed
                if check_list("CPU_ClockSpeed_7.txt", sub_path) is True:
                                HW_SPEED = "7"
                if check_list("CPU_ClockSpeed_14.txt", sub_path) is True:
                                HW_SPEED = "14"
                if check_list("CPU_ClockSpeed_28.txt", sub_path) is True:
                                HW_SPEED = "28"


                HW_CPU = ""
                # ' cpu model 68000
                if check_list("CPU_68000.txt", sub_path) is True:
                                HW_CPU = "68000"
                                
                # ' cpu model 68010
                if check_list("CPU_68010.txt", sub_path) is True:
                                HW_CPU = "68010"
                                HW_24BIT = "FALSE"
                                
                # ' cpu model 68040
                if check_list("CPU_68040.txt", sub_path) is True:
                                HW_CPU = "68040"
                                HW_24BIT = "FALSE"

                # ' 24 bit addressing 
                HW_24BIT = ""
                if not check_list("CPU_No24BitAddress.txt", sub_path) is False:
                    HW_24BIT = "FALSE"
             
                #   compatible CPU 
                HW_CPUCOMP = ""
                if check_list("CPU_Compatible.txt", sub_path) is True:
                    HW_CPUCOMP = "TRUE"
                    
             #   cycle_exact = check_list("CPU_CycleExact.txt", sub_path)

                #JIT Cache
                HW_JIT = ""
                if check_list("CPU_ForceJIT.txt",sub_path) == True:
                        HW_JIT = "TRUE"
                        HW_SPEED = "MAX"
                elif check_list("CPU_NoJIT.txt", sub_path) == True:
                        HW_JIT = "FALSE"

                # CHIPSET
                HW_CHIPSET = ""
                if check_list("CPU_ForceAGA.txt",sub_path) == True:
                        HW_CHIPSET = "AGA"
                elif check_list("CPU_ForceECS.txt", sub_path) == True:
                        HW_CHIPSET = "ECS"  
                elif check_list("CPU_ForceOCS.txt", sub_path) == True:
                        HW_CHIPSET = "OCS"  

                if this_file.find("_AGA") > -1:
                        HW_CHIPSET = "AGA"                                       
                if this_file.find("_CD32") > -1:
                        HW_CHIPSET = "AGA"
                        use_cd32_pad = True



                # ================================
                # building the hardware section
                if use_mouse1 == True:
                    hardware += ("PRIMARY_CONTROL=MOUSE") + chr(10)
                else:
                    hardware += ("PRIMARY_CONTROL=JOYSTICK")  + chr(10)       

                # building the hardware section
                if use_mouse1 == True:
                    hardware += ("PORT0=MOUSE") + chr(10)
                elif use_cd32_pad == True:
                    hardware += ("PORT0=CD32") + chr(10)
                else:
                    hardware += ("PORT0=JOY")  + chr(10)       

                if use_mouse2 == True:
                    hardware += ("PORT1=MOUSE") + chr(10)
                elif use_cd32_pad == True:
                    hardware += ("PORT1=CD32")  + chr(10)       
                else:
                    hardware += ("PORT1=JOY")  + chr(10)      

             #   hardware += ("PRIMARY_CONTROL=MOUSE") + chr(10)

                if HW_FASTCOPPER != "":
                    hardware += ("FAST_COPPER=") + HW_FASTCOPPER + chr(10)

                if HW_BLITS != "":
                    hardware += ("BLITTER=") + HW_BLITS + chr(10)

                if HW_SPRITES != "":
                    hardware += ("SPRITES=") + HW_CPU + chr(10)
                    
                if HW_24BIT != "":
                    hardware += ("CPU_24BITADDRESSING=") + HW_24BIT + chr(10)

                if HW_CPUCOMP != "":
                    hardware += ("CPU_COMPATIBLE=") + HW_CPUCOMP + chr(10)

                if HW_CPU != "":
                    hardware += ("CPU=") + HW_CPU + chr(10)
                
                if HW_JIT != "":
                    hardware += ("JIT=") + HW_JIT + chr(10)

                if HW_SPEED != "":
                    hardware += ("CLOCK=") + HW_SPEED + chr(10)

                if HW_CHIPSET != "":
                    hardware += ("CHIPSET=") + HW_CHIPSET + chr(10)
                    
                if HW_NTSC != "":
                    hardware += ("NTSC=") + HW_NTSC + chr(10)

                # SCREEN OPTIONS
                if HW_HEIGHT != "":
                    hardware += ("SCREEN_HEIGHT=") + HW_HEIGHT + chr(10)

                if HW_WIDTH != "":
                    hardware += ("SCREEN_WIDTH") + HW_WIDTH + chr(10)

                if screen_offset_y != 0:
                    hardware += ("SCREEN_Y_OFFSET=") + str(screen_offset_y) + chr(10)




                # MEMORY OPTIONS

                if chip_ram != 2:
                    hardware += ("CHIP_RAM=") + str(chip_ram) + chr(10)

                if fast_ram != 4:
                    hardware += ("FAST_RAM=") + str(fast_ram) + chr(10)

                if z3_ram != 0:
                    hardware += ("Z3_RAM=") + str(z3_ram) + chr(10)

                    
                # custom controls
                custom_file = "customcontrols/" + full_game_name + ".controls"
                custom_text = ""
                                
                if os.path.isfile(custom_file) == True:

                # remove any items which are not amiberry custom settings
                    with open(custom_file) as f:
                        content = f.readlines()
                    f.close()
                                    
                    for this_line in content:
                        if this_line.find("amiberry_custom") > -1:
                            custom_text += this_line


                # 
                extra_libs = "False"
                if check_list("WHD_Libraries.txt", sub_path) is True:
                    extra_libs = "True"

                COMPLETE_MSG = COMPLETE_MSG + "Scanned: " + full_game_name + chr(10)
                ##generate XML
                
                
                XML = XML + chr(9)+ '<game filename="' + text_utils.left(this_file,len(this_file) - 4).replace("&", "&amp;") + '"  sha1="' + ArchiveSHA + '">' + chr(10)
                XML = XML + chr(9)+ chr(9) + '<name>' + full_game_name.replace("&", "&amp;") + '</name>' + chr(10)
                XML = XML + chr(9)+ chr(9) + '<subpath>' + sub_path.replace("&", "&amp;") + '</subpath>' + chr(10)
                XML = XML + chr(9)+ chr(9) + '<variant_uuid>' + UUID + '</variant_uuid>' + chr(10)
                XML = XML + chr(9)+ chr(9) + '<slave_count>' + str(len(slave_archive.slaves)) + '</slave_count>' + chr(10)
                XML = XML + chr(9)+ chr(9) + '<slave_default>' + default_slave.replace("&", "&amp;")  + '</slave_default>' + chr(10)
                XML = XML + chr(9)+ chr(9) + '<slave_libraries>' + extra_libs  + '</slave_libraries>' + chr(10)
                XML = XML + SLAVE_XML
                XML = XML + chr(9)  + chr(9) + '<hardware>'
                XML = XML + chr(10) + chr(9) + chr(9) + hardware.replace(chr(10), chr(10) + chr(9) + chr(9) )
#                XML = XML + chr(10) + chr(9) + chr(9) + '</hardware>' + chr(10)
                XML = XML + '</hardware>' + chr(10)


                if len(custom_text)>0:
#                    XML = XML + chr(9)+ chr(9) + '<custom_controls>' + chr(10) + custom_text  + chr(10) + chr(9) + chr(9) + '</custom_controls>' + chr(10)
                    XML = XML + chr(9)+ chr(9) + '<custom_controls>' + chr(10) + chr(9) + chr(9) + custom_text  + chr(10) + chr(9) + chr(9) + '</custom_controls>' + chr(10)
                
                XML = XML + chr(9)+ '</game>' + chr(10)

        except FileNotFoundError:
                print("Could not find LHA archive: {}".format(archive_path))
                ERROR_MSG = ERROR_MSG + "Could not find LHA archive: {}".format(this_file)  + chr(10)
                #sys.exit(1)
                
        except lhafile.BadLhafile:
                print("Could not read LHA archive: {}".format(archive_path))
                ERROR_MSG = ERROR_MSG + "Could not read LHA archive: {}".format(this_file)  + chr(10) 
                #sys.exit(1)
        except KeyboardInterrupt:
                print()
                print("User Abort")
                break
        except:
                print("Something went wrong with LHA archive: {}".format(archive_path))
                ERROR_MSG = ERROR_MSG + "Could not read LHA archive: {}".format(this_file)  + chr(10) 
       
    # limit  it to a certian number of archives (for testing)
    if count >= 99999:
        break
    count = count + 1

XML = XML_HEADER + XML_OLD + XML + XML_FOOTER

# =======================================
# print XML and other files
# =======================================
print("Generating XML File")
text_file = open(whdbtmp, "w+")
text_file.write(XML)
text_file.close()

# Sorting elements / not required but easier to debug
print("Sorting XML File")

tree = etree.parse(whdbtmp)
parent = tree.getroot()
sortchildrenby(parent, 'filename')
tree.write(whdbfile)

# Validating XML well-formedness
try:
    parsefile(whdbfile)
    print('XML valid')
except:
    print('XML NOT valid.')

text_file = open("files_scanned.txt", "w+")
text_file.write(COMPLETE_MSG)
text_file.close()

##if ERROR_MSG != "":
text_file = open("files_failed.txt", "w+")
text_file.write(ERROR_MSG)
text_file.close()

# =======================================
# Cleaning
# =======================================
# Remove any .lha that have been processed
for lhaclean in os.listdir(input_directory):
    if lhaclean.endswith(".lha"):
        os.remove(os.path.join(input_directory, lhaclean))

# Remove the tmp whdload_db.xml
os.remove(whdbtmp)

# Note: could use md5 hash instead
# get whdbfile size after modification
whdsize_after = Path(whdbfile).stat().st_size

if whdsize_after > 0:
    os.remove(whdbbak)

# =======================================
print('Bye!')
print()
